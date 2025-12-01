import { Injectable, inject, signal, computed } from '@angular/core';
import { Router } from '@angular/router';
import { Observable } from 'rxjs';
import { tap, finalize } from 'rxjs/operators';
import { marked } from 'marked';
import { ApiService } from './api.service';
import { StorageService } from './storage.service';
import {
  WorldgenSession,
  WorldgenSessionSummary,
  WorldgenSessionMode,
  WorldgenStepName,
  WorldgenChatResponse,
  Universe,
  ConsistencyCheckProgress,
  ConsistencyCheckStartResponse
} from '../models/api.models';

export interface StepInfo {
  name: WorldgenStepName;
  displayName: string;
  description: string;
  required: boolean;
}

export const WORLDGEN_STEPS: StepInfo[] = [
  { name: 'basics', displayName: 'Basics', description: 'Name and description', required: true },
  { name: 'tone', displayName: 'Tone', description: 'Mood and atmosphere', required: true },
  { name: 'rules', displayName: 'Rules', description: 'Game mechanics', required: true },
  { name: 'calendar', displayName: 'Calendar', description: 'In-world time', required: false },
  { name: 'lore', displayName: 'Lore', description: 'World history', required: false },
  { name: 'homebrew', displayName: 'Homebrew', description: 'Custom content', required: false },
];

@Injectable({
  providedIn: 'root'
})
export class WorldgenService {
  private readonly api = inject(ApiService);
  private readonly storage = inject(StorageService);
  private readonly router = inject(Router);
  private readonly endpoint = '/universes/worldgen/';
  private readonly markdownRenderer = new marked.Renderer();

  // Current session state
  private readonly _currentSession = signal<WorldgenSession | null>(null);
  private readonly _isStreaming = signal(false);
  private readonly _pendingUserMessage = signal<string | null>(null);

  // Public signals
  readonly currentSession = this._currentSession.asReadonly();
  readonly isStreaming = this._isStreaming.asReadonly();
  readonly pendingUserMessage = this._pendingUserMessage.asReadonly();

  // Computed values
  readonly stepStatus = computed(() => {
    const session = this._currentSession();
    return session?.step_status_json ?? null;
  });

  readonly draftData = computed(() => {
    const session = this._currentSession();
    return session?.draft_data_json ?? null;
  });

  readonly conversationMessages = computed(() => {
    const session = this._currentSession();
    return session?.conversation_json ?? [];
  });

  readonly currentStep = computed((): WorldgenStepName => {
    const status = this.stepStatus();
    if (!status) return 'basics';

    for (const step of WORLDGEN_STEPS) {
      const stepStatus = status[step.name];
      if (!stepStatus?.complete) {
        return step.name;
      }
    }
    return 'homebrew'; // All complete, default to homebrew
  });

  readonly canFinalize = computed(() => {
    const status = this.stepStatus();
    if (!status) return false;

    const requiredSteps: WorldgenStepName[] = ['basics', 'tone', 'rules'];
    return requiredSteps.every(step => status[step]?.complete);
  });

  // Check if LLM is configured
  checkLlmStatus(): Observable<{ configured: boolean }> {
    return this.api.get<{ configured: boolean }>(`${this.endpoint}llm-status/`);
  }

  // List user's draft sessions
  listSessions(): Observable<WorldgenSessionSummary[]> {
    return this.api.get<WorldgenSessionSummary[]>(`${this.endpoint}sessions/`);
  }

  // Create a new session
  createSession(mode: WorldgenSessionMode = 'ai_collab'): Observable<WorldgenSession> {
    return new Observable(subscriber => {
      this.api.post<WorldgenSession>(`${this.endpoint}sessions/`, { mode })
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
  getSession(sessionId: string): Observable<WorldgenSession> {
    return new Observable(subscriber => {
      this.api.get<WorldgenSession>(`${this.endpoint}sessions/${sessionId}/`)
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
  abandonSession(sessionId: string): Observable<void> {
    return new Observable(subscriber => {
      this.api.delete<void>(`${this.endpoint}sessions/${sessionId}/`)
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
  sendMessage(sessionId: string, message: string): Observable<WorldgenChatResponse> {
    this._isStreaming.set(true);
    this._pendingUserMessage.set(message);

    return this.api.post<WorldgenChatResponse>(
      `${this.endpoint}sessions/${sessionId}/chat/`,
      { message }
    ).pipe(
      tap(result => {
        this._currentSession.update(session => {
          if (!session) return session;
          return {
            ...session,
            step_status_json: result.step_status,
            draft_data_json: result.draft_data,
            conversation_json: [
              ...session.conversation_json,
              { role: 'user' as const, content: message, timestamp: new Date().toISOString() },
              { role: 'assistant' as const, content: result.response, timestamp: new Date().toISOString() }
            ]
          };
        });
        this._pendingUserMessage.set(null);
      }),
      finalize(() => this._isStreaming.set(false))
    );
  }

  // Update step data directly (for manual mode)
  updateStepData(sessionId: string, step: WorldgenStepName, data: Record<string, unknown>): Observable<WorldgenSession> {
    return new Observable(subscriber => {
      this.api.patch<WorldgenSession>(`${this.endpoint}sessions/${sessionId}/update/`, { step, data })
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

  // Switch mode between AI collab and manual
  switchMode(sessionId: string, mode: WorldgenSessionMode): Observable<WorldgenSession> {
    return new Observable(subscriber => {
      this.api.post<WorldgenSession>(`${this.endpoint}sessions/${sessionId}/mode/`, { mode })
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

  // Finalize session and create universe
  finalizeSession(sessionId: string): Observable<Universe> {
    return new Observable(subscriber => {
      this.api.post<Universe>(`${this.endpoint}sessions/${sessionId}/finalize/`, {})
        .subscribe({
          next: universe => {
            this._currentSession.set(null);
            subscriber.next(universe);
            subscriber.complete();
          },
          error: err => subscriber.error(err)
        });
    });
  }

  // Get AI assistance for a specific step
  getAiAssist(sessionId: string, step: WorldgenStepName, field?: string, message?: string): Observable<WorldgenChatResponse> {
    this._isStreaming.set(true);

    return this.api.post<WorldgenChatResponse>(
      `${this.endpoint}sessions/${sessionId}/assist/`,
      { step, field, message }
    ).pipe(
      tap(result => {
        this._currentSession.update(session => {
          if (!session) return session;
          return {
            ...session,
            step_status_json: result.step_status,
            draft_data_json: result.draft_data
          };
        });
      }),
      finalize(() => this._isStreaming.set(false))
    );
  }

  // Extract data for a specific field from conversation history
  extractField(sessionId: string, step: WorldgenStepName, field: string): Observable<WorldgenChatResponse> {
    return this.api.post<WorldgenChatResponse>(
      `${this.endpoint}sessions/${sessionId}/extract-field/`,
      { step, field }
    ).pipe(
      tap(result => {
        this._currentSession.update(session => {
          if (!session) return session;
          return {
            ...session,
            step_status_json: result.step_status,
            draft_data_json: result.draft_data
          };
        });
      })
    );
  }

  // Extend existing field content with more detail
  extendField(sessionId: string, step: WorldgenStepName, field: string): Observable<WorldgenChatResponse> {
    return this.api.post<WorldgenChatResponse>(
      `${this.endpoint}sessions/${sessionId}/extend-field/`,
      { step, field }
    ).pipe(
      tap(result => {
        this._currentSession.update(session => {
          if (!session) return session;
          return {
            ...session,
            step_status_json: result.step_status,
            draft_data_json: result.draft_data
          };
        });
      })
    );
  }

  // Clear current session (for navigation)
  clearSession(): void {
    this._currentSession.set(null);
    this._isStreaming.set(false);
    this._pendingUserMessage.set(null);
  }

  // ==================== Consistency Check Methods ====================

  // Start a consistency check for the session
  startConsistencyCheck(sessionId: string): Observable<ConsistencyCheckStartResponse> {
    return this.api.post<ConsistencyCheckStartResponse>(
      `${this.endpoint}sessions/${sessionId}/consistency-check/`,
      {}
    );
  }

  // Get current status of a consistency check
  getConsistencyCheckStatus(sessionId: string, checkId: string): Observable<ConsistencyCheckProgress> {
    return this.api.get<ConsistencyCheckProgress>(
      `${this.endpoint}sessions/${sessionId}/consistency-check/${checkId}/`
    );
  }

  // Continue a paused consistency check (advance to next pair)
  continueConsistencyCheck(sessionId: string, checkId: string): Observable<ConsistencyCheckProgress> {
    return this.api.post<ConsistencyCheckProgress>(
      `${this.endpoint}sessions/${sessionId}/consistency-check/${checkId}/`,
      {}
    );
  }

  // Resolve a conflict and continue checking
  resolveConflict(
    sessionId: string,
    checkId: string,
    action: 'accept' | 'edit',
    fieldUpdates?: Record<string, unknown>
  ): Observable<ConsistencyCheckProgress> {
    return this.api.post<ConsistencyCheckProgress>(
      `${this.endpoint}sessions/${sessionId}/consistency-check/${checkId}/resolve/`,
      { action, field_updates: fieldUpdates }
    );
  }

  // Cancel an active consistency check
  cancelConsistencyCheck(sessionId: string, checkId: string): Observable<void> {
    return this.api.delete<void>(
      `${this.endpoint}sessions/${sessionId}/consistency-check/${checkId}/cancel/`
    );
  }

  renderMarkdown(text: string): string {
    // Pre-process: convert Unicode bullet characters to standard markdown list markers
    // This handles LLM output that uses • instead of - or *
    let processedText = text.replace(/^(\s*)•\s*/gm, '$1- ');

    // Convert en-dashes (–) used as sub-bullets to indented markdown list items
    // The LLM often uses – for sub-items which should be nested
    processedText = processedText.replace(/^(\s*)–\s*/gm, '$1  - ');

    const html = marked.parse(processedText, { renderer: this.markdownRenderer }) as string;
    return html;
  }
}
