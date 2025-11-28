import { Injectable, inject, signal, computed } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, Subject } from 'rxjs';
import { marked } from 'marked';
import { ApiService } from './api.service';
import { StorageService } from './storage.service';
import { environment } from '@env/environment';
import {
  WorldgenSession,
  WorldgenSessionSummary,
  WorldgenSessionMode,
  WorldgenStepName,
  WorldgenStreamEvent,
  Universe
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
  private readonly _streamContent = signal('');

  // Public signals
  readonly currentSession = this._currentSession.asReadonly();
  readonly isStreaming = this._isStreaming.asReadonly();
  readonly streamContent = this._streamContent.asReadonly();

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

  // Send a chat message with streaming
  sendMessage(sessionId: string, message: string): Subject<WorldgenStreamEvent> {
    const subject = new Subject<WorldgenStreamEvent>();

    const token = this.storage.getAccessToken();
    if (!token) {
      // Treat missing token the same way the interceptor would
      queueMicrotask(() => {
        this.storage.clearTokens();
        this.router.navigate(['/auth/login']);
        subject.error(new Error('Not authenticated'));
      });
      return subject;
    }

    this._isStreaming.set(true);
    this._streamContent.set('');

    const url = `${environment.apiUrl}${this.endpoint}sessions/${sessionId}/chat/`;

    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ message })
    })
      .then(async response => {
        if (response.status === 401) {
          this.storage.clearTokens();
          this.router.navigate(['/auth/login']);
          throw new Error('Unauthorized');
        }

        if (!response.ok) {
          const errorText = await response.text().catch(() => '');
          const messageText = errorText || `HTTP ${response.status}`;
          throw new Error(messageText);
        }
        return response.body;
      })
      .then(body => {
        if (!body) {
          throw new Error('No response body');
        }

        const reader = body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        const processStream = async () => {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
              if (!line.startsWith('data: ')) continue;

              try {
                const event: WorldgenStreamEvent = JSON.parse(line.slice(6));

                if (event.type === 'chunk' && event.content) {
                  const combined = this._streamContent() + event.content;
                  // Check if we're receiving unfiltered DATA_JSON (should not happen)
                  if (event.content.includes('DATA_JSON')) {
                    console.warn('[WORLDGEN] ⚠️  Chunk contains DATA_JSON - backend filter may not be active:', event.content.substring(0, 100));
                  }
                  this._streamContent.set(this.cleanAssistantContent(combined));
                }

                if (event.type === 'error') {
                  const messageText = event.content || 'Streaming error';
                  this._isStreaming.set(false);
                  subject.error(new Error(messageText));
                  return;
                }

                if (event.type === 'complete') {
                  // Update session with new data
                  this._currentSession.update(session => {
                    if (!session) return session;
                    return {
                      ...session,
                      step_status_json: event.step_status ?? session.step_status_json,
                      draft_data_json: event.draft_data ?? session.draft_data_json,
                      conversation_json: [
                        ...session.conversation_json,
                        { role: 'user' as const, content: message, timestamp: new Date().toISOString() },
                        { role: 'assistant' as const, content: this._streamContent(), timestamp: new Date().toISOString() }
                      ]
                    };
                  });
                }

                subject.next(event);
              } catch (e) {
                console.error('Failed to parse SSE event:', e);
              }
            }
          }

          this._isStreaming.set(false);
          subject.complete();
        };

        processStream().catch(err => {
          this._isStreaming.set(false);
          subject.error(err);
        });
      })
      .catch(err => {
        this._isStreaming.set(false);
        subject.error(err);
      });

    return subject;
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
  getAiAssist(sessionId: string, step: WorldgenStepName, field?: string, message?: string): Subject<WorldgenStreamEvent> {
    const subject = new Subject<WorldgenStreamEvent>();

    const token = this.storage.getAccessToken();
    if (!token) {
      queueMicrotask(() => {
        this.storage.clearTokens();
        this.router.navigate(['/auth/login']);
        subject.error(new Error('Not authenticated'));
      });
      return subject;
    }

    this._isStreaming.set(true);
    this._streamContent.set('');

    const url = `${environment.apiUrl}${this.endpoint}sessions/${sessionId}/assist/`;

    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ step, field, message })
    })
      .then(async response => {
        if (response.status === 401) {
          this.storage.clearTokens();
          this.router.navigate(['/auth/login']);
          throw new Error('Unauthorized');
        }

        if (!response.ok) {
          const errorText = await response.text().catch(() => '');
          const messageText = errorText || `HTTP ${response.status}`;
          throw new Error(messageText);
        }
        return response.body;
      })
      .then(body => {
        if (!body) {
          throw new Error('No response body');
        }

        const reader = body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        const processStream = async () => {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
              if (!line.startsWith('data: ')) continue;

              try {
                const event: WorldgenStreamEvent = JSON.parse(line.slice(6));

                if (event.type === 'chunk' && event.content) {
                  const combined = this._streamContent() + event.content;
                  // Check if we're receiving unfiltered DATA_JSON (should not happen)
                  if (event.content.includes('DATA_JSON')) {
                    console.warn('[WORLDGEN] ⚠️  Chunk contains DATA_JSON - backend filter may not be active:', event.content.substring(0, 100));
                  }
                  this._streamContent.set(this.cleanAssistantContent(combined));
                }

                if (event.type === 'error') {
                  const messageText = event.content || 'Streaming error';
                  this._isStreaming.set(false);
                  subject.error(new Error(messageText));
                  return;
                }

                if (event.type === 'complete') {
                  this._currentSession.update(session => {
                    if (!session) return session;
                    return {
                      ...session,
                      step_status_json: event.step_status ?? session.step_status_json,
                      draft_data_json: event.draft_data ?? session.draft_data_json
                    };
                  });
                }

                subject.next(event);
              } catch (e) {
                console.error('Failed to parse SSE event:', e);
              }
            }
          }

          this._isStreaming.set(false);
          subject.complete();
        };

        processStream().catch(err => {
          this._isStreaming.set(false);
          subject.error(err);
        });
      })
      .catch(err => {
        this._isStreaming.set(false);
        subject.error(err);
      });

    return subject;
  }

  // Clear current session (for navigation)
  clearSession(): void {
    this._currentSession.set(null);
    this._streamContent.set('');
    this._isStreaming.set(false);
  }

  private cleanAssistantContent(raw: string): string {
    // Drop CHAT: prefix and remove any DATA_JSON section that follows
    let content = raw;
    const dataJsonIdx = content.indexOf('DATA_JSON:');
    if (dataJsonIdx !== -1) {
      content = content.slice(0, dataJsonIdx);
    }
    content = content.replace(/^\s*CHAT:\s*/i, '');
    return content.trim();
  }

  renderMarkdown(text: string): string {
    const clean = this.cleanAssistantContent(text);
    // Debug logging
    if (clean.length > 0) {
      console.log('[WORLDGEN] Rendering markdown. Input length:', text.length, 'Cleaned length:', clean.length);
      if (clean.includes('DATA_JSON')) {
        console.warn('[WORLDGEN] ⚠️  CLEANED CONTENT STILL HAS DATA_JSON!');
      }
    }
    // Escape HTML to avoid injection, then render markdown
    const escaped = clean
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
    const html = marked.parse(escaped, { renderer: this.markdownRenderer }) as string;
    return html;
  }
}
