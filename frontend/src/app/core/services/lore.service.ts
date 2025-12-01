import { Injectable, inject, signal, computed } from '@angular/core';
import { Observable } from 'rxjs';
import { tap, finalize } from 'rxjs/operators';
import { marked } from 'marked';
import { ApiService } from './api.service';
import {
  LoreSession,
  LoreSessionSummary,
  LoreChatResponse,
  LoreFinalizeResponse,
  HardCanonDoc,
  LoreDocumentDraft,
} from '../models/api.models';

@Injectable({
  providedIn: 'root'
})
export class LoreService {
  private readonly api = inject(ApiService);
  private readonly markdownRenderer = new marked.Renderer();

  // Current session state
  private readonly _currentSession = signal<LoreSession | null>(null);
  private readonly _isLoading = signal(false);
  private readonly _pendingUserMessage = signal<string | null>(null);

  // Public signals
  readonly currentSession = this._currentSession.asReadonly();
  readonly isLoading = this._isLoading.asReadonly();
  readonly pendingUserMessage = this._pendingUserMessage.asReadonly();

  // Computed values
  readonly currentDocument = computed(() => {
    const session = this._currentSession();
    return session?.current_document_json ?? null;
  });

  readonly draftDocuments = computed(() => {
    const session = this._currentSession();
    return session?.draft_documents_json ?? [];
  });

  readonly conversationMessages = computed(() => {
    const session = this._currentSession();
    return session?.conversation_json ?? [];
  });

  readonly documentCount = computed(() => {
    return this.draftDocuments().length;
  });

  // Build endpoint for lore sessions
  private buildEndpoint(universeId: string, path: string = ''): string {
    return `/universes/${universeId}/lore/sessions/${path}`;
  }

  // List user's lore sessions for a universe
  listSessions(universeId: string): Observable<LoreSessionSummary[]> {
    return this.api.get<LoreSessionSummary[]>(this.buildEndpoint(universeId));
  }

  // Create a new lore session
  createSession(universeId: string): Observable<LoreSession> {
    this._isLoading.set(true);
    return new Observable(subscriber => {
      this.api.post<LoreSession>(this.buildEndpoint(universeId), {})
        .pipe(finalize(() => this._isLoading.set(false)))
        .subscribe({
          next: session => {
            this._currentSession.set(session);
            subscriber.next(session);
            subscriber.complete();
          },
          error: err => subscriber.error(err)
        });
    });
  }

  // Get a session by ID
  getSession(universeId: string, sessionId: string): Observable<LoreSession> {
    this._isLoading.set(true);
    return new Observable(subscriber => {
      this.api.get<LoreSession>(this.buildEndpoint(universeId, `${sessionId}/`))
        .pipe(finalize(() => this._isLoading.set(false)))
        .subscribe({
          next: session => {
            this._currentSession.set(session);
            subscriber.next(session);
            subscriber.complete();
          },
          error: err => subscriber.error(err)
        });
    });
  }

  // Abandon a session
  abandonSession(universeId: string, sessionId: string): Observable<void> {
    return new Observable(subscriber => {
      this.api.delete<void>(this.buildEndpoint(universeId, `${sessionId}/`))
        .subscribe({
          next: () => {
            if (this._currentSession()?.id === sessionId) {
              this._currentSession.set(null);
            }
            subscriber.next();
            subscriber.complete();
          },
          error: err => subscriber.error(err)
        });
    });
  }

  // Send a chat message
  sendMessage(universeId: string, sessionId: string, message: string): Observable<LoreChatResponse> {
    this._isLoading.set(true);
    this._pendingUserMessage.set(message);

    return this.api.post<LoreChatResponse>(
      this.buildEndpoint(universeId, `${sessionId}/chat/`),
      { message }
    ).pipe(
      tap(result => {
        this._currentSession.update(session => {
          if (!session) return session;
          return {
            ...session,
            current_document_json: result.current_document,
            draft_documents_json: result.draft_documents,
            conversation_json: [
              ...session.conversation_json,
              { role: 'user' as const, content: message, timestamp: new Date().toISOString() },
              { role: 'assistant' as const, content: result.response, timestamp: new Date().toISOString() }
            ]
          };
        });
        this._pendingUserMessage.set(null);
      }),
      finalize(() => this._isLoading.set(false))
    );
  }

  // Start a new document
  startNewDocument(universeId: string, sessionId: string, title: string = ''): Observable<{ current_document: LoreDocumentDraft; draft_documents: LoreDocumentDraft[] }> {
    return this.api.post<{ current_document: LoreDocumentDraft; draft_documents: LoreDocumentDraft[] }>(
      this.buildEndpoint(universeId, `${sessionId}/document/`),
      { title }
    ).pipe(
      tap(result => {
        this._currentSession.update(session => {
          if (!session) return session;
          return {
            ...session,
            current_document_json: result.current_document,
            draft_documents_json: result.draft_documents
          };
        });
      })
    );
  }

  // Update current document manually
  updateCurrentDocument(
    universeId: string,
    sessionId: string,
    updates: Partial<LoreDocumentDraft>
  ): Observable<{ current_document: LoreDocumentDraft; draft_documents: LoreDocumentDraft[] }> {
    return this.api.patch<{ current_document: LoreDocumentDraft; draft_documents: LoreDocumentDraft[] }>(
      this.buildEndpoint(universeId, `${sessionId}/document/`),
      updates
    ).pipe(
      tap(result => {
        this._currentSession.update(session => {
          if (!session) return session;
          return {
            ...session,
            current_document_json: result.current_document,
            draft_documents_json: result.draft_documents
          };
        });
      })
    );
  }

  // Save current document to drafts
  saveCurrentDocument(universeId: string, sessionId: string): Observable<{ current_document: LoreDocumentDraft; draft_documents: LoreDocumentDraft[] }> {
    return this.api.put<{ current_document: LoreDocumentDraft; draft_documents: LoreDocumentDraft[] }>(
      this.buildEndpoint(universeId, `${sessionId}/document/`),
      {}
    ).pipe(
      tap(result => {
        this._currentSession.update(session => {
          if (!session) return session;
          return {
            ...session,
            current_document_json: result.current_document,
            draft_documents_json: result.draft_documents
          };
        });
      })
    );
  }

  // Finalize session and create UniverseHardCanonDocs
  finalizeSession(universeId: string, sessionId: string): Observable<LoreFinalizeResponse> {
    this._isLoading.set(true);
    return this.api.post<LoreFinalizeResponse>(
      this.buildEndpoint(universeId, `${sessionId}/finalize/`),
      {}
    ).pipe(
      tap(() => {
        this._currentSession.set(null);
      }),
      finalize(() => this._isLoading.set(false))
    );
  }

  // List canon docs for a universe
  listCanonDocs(universeId: string): Observable<HardCanonDoc[]> {
    return this.api.get<HardCanonDoc[]>(`/universes/${universeId}/lore/`);
  }

  // Clear current session (for navigation)
  clearSession(): void {
    this._currentSession.set(null);
    this._isLoading.set(false);
    this._pendingUserMessage.set(null);
  }

  // Render markdown to HTML
  renderMarkdown(text: string): string {
    // Pre-process: convert Unicode bullet characters to standard markdown list markers
    let processedText = text.replace(/^(\s*)•\s*/gm, '$1- ');

    // Convert en-dashes (–) used as sub-bullets to indented markdown list items
    processedText = processedText.replace(/^(\s*)–\s*/gm, '$1  - ');

    const html = marked.parse(processedText, { renderer: this.markdownRenderer }) as string;
    return html;
  }
}
