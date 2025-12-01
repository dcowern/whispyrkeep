import { Component, input, inject, signal, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { UniverseService } from '@core/services/universe.service';
import { LoreService } from '@core/services/lore.service';
import { Universe, HardCanonDoc, LoreSessionSummary } from '@core/models';
import {
  LucideAngularModule,
  ArrowLeft,
  Book,
  FileText,
  Loader2,
  Plus,
  MessageSquare,
  Upload,
  Clock,
  Trash2,
  Sparkles
} from 'lucide-angular';

@Component({
  selector: 'app-universe-lore',
  standalone: true,
  imports: [CommonModule, RouterLink, LucideAngularModule],
  template: `
    <main id="main-content" class="page">
      <header class="page__header">
        <a [routerLink]="['/universes', id()]" class="back-link">
          <lucide-icon [img]="ArrowLeftIcon" />
          Back to universe
        </a>
        <div class="page__title">
          <lucide-icon [img]="BookIcon" />
          <div>
            <h1>Lore & Canon</h1>
            @if (universe()) {
              <span class="page__subtitle">{{ universe()!.name }}</span>
            }
          </div>
        </div>
      </header>

      <div class="page__content">
        @if (isLoading()) {
          <div class="loading">
            <lucide-icon [img]="Loader2Icon" class="animate-spin" />
            <span>Loading...</span>
          </div>
        } @else {
          <!-- Action Cards -->
          <div class="action-cards">
            <div class="action-card action-card--primary">
              <lucide-icon [img]="SparklesIcon" />
              <h3>Develop Lore with AI</h3>
              <p>Create rich lore documents through conversation with an AI assistant.</p>
              <button class="btn btn--primary" (click)="startLoreBuilder()">
                <lucide-icon [img]="MessageSquareIcon" />
                Start Lore Builder
              </button>
            </div>

            <div class="action-card action-card--disabled">
              <lucide-icon [img]="UploadIcon" />
              <h3>Upload Documents</h3>
              <p>Import existing lore from PDFs, text files, or markdown.</p>
              <button class="btn btn--secondary" disabled>
                <lucide-icon [img]="PlusIcon" />
                Coming Soon
              </button>
            </div>
          </div>

          <!-- Active Sessions -->
          @if (activeSessions().length > 0) {
            <section class="section">
              <h2>Active Lore Sessions</h2>
              <div class="session-list">
                @for (session of activeSessions(); track session.id) {
                  <div class="session-card" (click)="resumeSession(session.id)">
                    <div class="session-info">
                      <lucide-icon [img]="MessageSquareIcon" />
                      <div>
                        <span class="session-title">{{ session.document_count }} document(s) in progress</span>
                        <span class="session-date">Started {{ formatDate(session.created_at) }}</span>
                      </div>
                    </div>
                    <div class="session-actions">
                      <button class="btn btn--ghost" (click)="deleteSession($event, session.id)" title="Delete session">
                        <lucide-icon [img]="Trash2Icon" />
                      </button>
                    </div>
                  </div>
                }
              </div>
            </section>
          }

          <!-- Canon Documents -->
          <section class="section">
            <h2>Canon Documents</h2>
            @if (canonDocs().length === 0) {
              <div class="empty-state">
                <lucide-icon [img]="FileTextIcon" />
                <h3>No Canon Documents Yet</h3>
                <p>Hard canon documents define the immutable facts of your universe. Use the AI Lore Builder to create documents about geography, history, factions, and more.</p>
              </div>
            } @else {
              <div class="doc-list">
                @for (doc of canonDocs(); track doc.id) {
                  <div class="doc-card">
                    <div class="doc-header">
                      <lucide-icon [img]="FileTextIcon" />
                      <h4>{{ doc.title }}</h4>
                      <span class="doc-source">{{ formatSourceType(doc.source_type) }}</span>
                    </div>
                    <p class="doc-preview">{{ (doc.raw_text || '') | slice:0:200 }}{{ (doc.raw_text?.length || 0) > 200 ? '...' : '' }}</p>
                    <div class="doc-footer">
                      <span class="doc-date">
                        <lucide-icon [img]="ClockIcon" />
                        {{ formatDate(doc.created_at) }}
                      </span>
                    </div>
                  </div>
                }
              </div>
            }
          </section>
        }
      </div>
    </main>
  `,
  styles: [`
    .page {
      padding: var(--wk-space-6);
      max-width: 1000px;
      margin: 0 auto;
    }

    .page__header {
      margin-bottom: var(--wk-space-6);
    }

    .back-link {
      display: inline-flex;
      align-items: center;
      gap: var(--wk-space-2);
      color: var(--wk-text-secondary);
      text-decoration: none;
      font-size: var(--wk-text-sm);
      margin-bottom: var(--wk-space-4);
      transition: color var(--wk-transition-fast);

      lucide-icon { width: 16px; height: 16px; }

      &:hover { color: var(--wk-text-primary); }
    }

    .page__title {
      display: flex;
      align-items: center;
      gap: var(--wk-space-4);

      > lucide-icon {
        width: 48px;
        height: 48px;
        color: var(--wk-secondary);
      }

      h1 {
        margin: 0;
        font-size: var(--wk-text-2xl);
        font-weight: var(--wk-font-bold);
        color: var(--wk-text-primary);
      }
    }

    .page__subtitle {
      font-size: var(--wk-text-sm);
      color: var(--wk-text-muted);
    }

    .loading {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: var(--wk-space-4);
      padding: var(--wk-space-12);
      text-align: center;
      color: var(--wk-text-secondary);

      lucide-icon {
        width: 48px;
        height: 48px;
        color: var(--wk-text-muted);
      }
    }

    .action-cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: var(--wk-space-4);
      margin-bottom: var(--wk-space-8);
    }

    .action-card {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      padding: var(--wk-space-6);
      background: var(--wk-surface);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-xl);
      transition: all var(--wk-transition-fast);

      > lucide-icon {
        width: 48px;
        height: 48px;
        color: var(--wk-primary);
        margin-bottom: var(--wk-space-4);
      }

      h3 {
        margin: 0 0 var(--wk-space-2);
        font-size: var(--wk-text-lg);
        font-weight: var(--wk-font-semibold);
        color: var(--wk-text-primary);
      }

      p {
        margin: 0 0 var(--wk-space-4);
        color: var(--wk-text-secondary);
        font-size: var(--wk-text-sm);
        line-height: var(--wk-leading-relaxed);
      }

      &--primary {
        border-color: var(--wk-primary);
        background: linear-gradient(135deg, rgba(var(--wk-primary-rgb), 0.05) 0%, transparent 100%);

        &:hover {
          border-color: var(--wk-primary);
          box-shadow: 0 0 20px rgba(var(--wk-primary-rgb), 0.2);
        }
      }

      &--disabled {
        opacity: 0.7;

        > lucide-icon {
          color: var(--wk-text-muted);
        }
      }
    }

    .section {
      margin-bottom: var(--wk-space-8);

      h2 {
        font-size: var(--wk-text-lg);
        font-weight: var(--wk-font-semibold);
        color: var(--wk-text-primary);
        margin: 0 0 var(--wk-space-4);
      }
    }

    .session-list {
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-3);
    }

    .session-card {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: var(--wk-space-4);
      background: var(--wk-surface);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-lg);
      cursor: pointer;
      transition: all var(--wk-transition-fast);

      &:hover {
        border-color: var(--wk-primary);
        background: rgba(var(--wk-primary-rgb), 0.05);
      }
    }

    .session-info {
      display: flex;
      align-items: center;
      gap: var(--wk-space-3);

      > lucide-icon {
        width: 24px;
        height: 24px;
        color: var(--wk-primary);
      }

      > div {
        display: flex;
        flex-direction: column;
      }
    }

    .session-title {
      font-weight: var(--wk-font-medium);
      color: var(--wk-text-primary);
    }

    .session-date {
      font-size: var(--wk-text-sm);
      color: var(--wk-text-muted);
    }

    .session-actions {
      display: flex;
      gap: var(--wk-space-2);
    }

    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      padding: var(--wk-space-8);
      background: var(--wk-surface);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-xl);

      lucide-icon {
        width: 48px;
        height: 48px;
        color: var(--wk-text-muted);
        margin-bottom: var(--wk-space-4);
      }

      h3 {
        margin: 0 0 var(--wk-space-2);
        font-size: var(--wk-text-lg);
        font-weight: var(--wk-font-semibold);
        color: var(--wk-text-primary);
      }

      p {
        margin: 0;
        max-width: 400px;
        color: var(--wk-text-secondary);
        line-height: var(--wk-leading-relaxed);
      }
    }

    .doc-list {
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-4);
    }

    .doc-card {
      padding: var(--wk-space-5);
      background: var(--wk-surface);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-lg);

      &:hover {
        border-color: var(--wk-text-muted);
      }
    }

    .doc-header {
      display: flex;
      align-items: center;
      gap: var(--wk-space-3);
      margin-bottom: var(--wk-space-3);

      > lucide-icon {
        width: 20px;
        height: 20px;
        color: var(--wk-secondary);
      }

      h4 {
        margin: 0;
        flex: 1;
        font-size: var(--wk-text-base);
        font-weight: var(--wk-font-semibold);
        color: var(--wk-text-primary);
      }
    }

    .doc-source {
      font-size: var(--wk-text-xs);
      color: var(--wk-text-muted);
      padding: var(--wk-space-1) var(--wk-space-2);
      background: var(--wk-glass-bg);
      border-radius: var(--wk-radius-sm);
    }

    .doc-preview {
      margin: 0 0 var(--wk-space-3);
      font-size: var(--wk-text-sm);
      color: var(--wk-text-secondary);
      line-height: var(--wk-leading-relaxed);
    }

    .doc-footer {
      display: flex;
      align-items: center;
      gap: var(--wk-space-4);
    }

    .doc-date {
      display: flex;
      align-items: center;
      gap: var(--wk-space-1);
      font-size: var(--wk-text-xs);
      color: var(--wk-text-muted);

      lucide-icon {
        width: 12px;
        height: 12px;
      }
    }

    .btn {
      display: inline-flex;
      align-items: center;
      gap: var(--wk-space-2);
      padding: var(--wk-space-3) var(--wk-space-5);
      border-radius: var(--wk-radius-lg);
      font-size: var(--wk-text-sm);
      font-weight: var(--wk-font-medium);
      text-decoration: none;
      cursor: pointer;
      transition: all var(--wk-transition-fast);
      border: none;

      lucide-icon { width: 18px; height: 18px; }

      &--primary {
        background: linear-gradient(135deg, var(--wk-primary) 0%, var(--wk-primary-dark) 100%);
        color: white;

        &:hover:not(:disabled) {
          box-shadow: 0 0 20px var(--wk-primary-glow);
        }
      }

      &--secondary {
        background: var(--wk-glass-bg);
        color: var(--wk-text-secondary);
        border: 1px solid var(--wk-glass-border);

        &:hover:not(:disabled) {
          background: var(--wk-surface);
          border-color: var(--wk-text-muted);
        }

        &:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      }

      &--ghost {
        background: transparent;
        color: var(--wk-text-muted);
        padding: var(--wk-space-2);

        lucide-icon { width: 16px; height: 16px; }

        &:hover {
          color: var(--wk-error);
          background: rgba(var(--wk-error-rgb), 0.1);
        }
      }
    }

    .animate-spin {
      animation: spin 1s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  `]
})
export class UniverseLoreComponent {
  private readonly universeService = inject(UniverseService);
  private readonly loreService = inject(LoreService);
  private readonly router = inject(Router);

  readonly ArrowLeftIcon = ArrowLeft;
  readonly BookIcon = Book;
  readonly FileTextIcon = FileText;
  readonly Loader2Icon = Loader2;
  readonly PlusIcon = Plus;
  readonly MessageSquareIcon = MessageSquare;
  readonly UploadIcon = Upload;
  readonly ClockIcon = Clock;
  readonly Trash2Icon = Trash2;
  readonly SparklesIcon = Sparkles;

  readonly id = input.required<string>();

  readonly universe = signal<Universe | null>(null);
  readonly canonDocs = signal<HardCanonDoc[]>([]);
  readonly activeSessions = signal<LoreSessionSummary[]>([]);
  readonly isLoading = signal(true);

  constructor() {
    effect(() => {
      const universeId = this.id();
      if (universeId) {
        this.loadData(universeId);
      }
    }, { allowSignalWrites: true });
  }

  private loadData(universeId: string): void {
    this.isLoading.set(true);

    // Load universe, canon docs, and active sessions in parallel
    this.universeService.get(universeId).subscribe({
      next: (universe) => {
        this.universe.set(universe);
      },
      error: () => {}
    });

    this.loreService.listCanonDocs(universeId).subscribe({
      next: (docs) => {
        this.canonDocs.set(docs);
        this.isLoading.set(false);
      },
      error: () => {
        this.isLoading.set(false);
      }
    });

    this.loreService.listSessions(universeId).subscribe({
      next: (sessions) => {
        this.activeSessions.set(sessions);
      },
      error: () => {}
    });
  }

  startLoreBuilder(): void {
    const universeId = this.id();
    this.loreService.createSession(universeId).subscribe({
      next: (session) => {
        this.router.navigate(['/universes', universeId, 'lore', 'build', session.id]);
      },
      error: (err) => {
        console.error('Failed to create lore session:', err);
        // Could show a toast/alert here
      }
    });
  }

  resumeSession(sessionId: string): void {
    const universeId = this.id();
    this.router.navigate(['/universes', universeId, 'lore', 'build', sessionId]);
  }

  deleteSession(event: Event, sessionId: string): void {
    event.stopPropagation();
    if (confirm('Are you sure you want to delete this session? Any unsaved work will be lost.')) {
      const universeId = this.id();
      this.loreService.abandonSession(universeId, sessionId).subscribe({
        next: () => {
          this.activeSessions.update(sessions => sessions.filter(s => s.id !== sessionId));
        },
        error: (err) => {
          console.error('Failed to delete session:', err);
        }
      });
    }
  }

  formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  }

  formatSourceType(sourceType: string): string {
    switch (sourceType) {
      case 'upload': return 'Uploaded';
      case 'worldgen': return 'World Gen';
      case 'user_edit': return 'Created';
      default: return sourceType;
    }
  }
}
