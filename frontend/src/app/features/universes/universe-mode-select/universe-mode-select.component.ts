import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { WorldgenService } from '@core/services/worldgen.service';
import {
  LucideAngularModule,
  Bot,
  PenTool,
  ArrowLeft,
  Sparkles,
  Globe,
  Clock,
  Trash2,
  AlertCircle,
  Settings
} from 'lucide-angular';
import { WorldgenSessionSummary } from '@core/models';

@Component({
  selector: 'app-universe-mode-select',
  standalone: true,
  imports: [CommonModule, RouterLink, LucideAngularModule],
  template: `
    <div class="mode-select">
      <div class="mode-select__bg">
        <div class="mode-select__orb mode-select__orb--1"></div>
        <div class="mode-select__orb mode-select__orb--2"></div>
      </div>

      <header class="mode-select__header animate-fade-in-down">
        <a routerLink="/universes" class="back-link">
          <lucide-icon [img]="ArrowLeftIcon" />
          Back to universes
        </a>
        <div class="mode-select__title">
          <div class="mode-select__title-icon">
            <lucide-icon [img]="GlobeIcon" />
          </div>
          <h1>Create Universe</h1>
          <p>Choose how you'd like to build your world</p>
        </div>
      </header>

      <main class="mode-select__content animate-fade-in-up">
        @if (errorMessage()) {
          <div class="error-banner">
            <lucide-icon [img]="AlertCircleIcon" />
            <span>{{ errorMessage() }}</span>
          </div>
        }

        <div class="mode-cards">
          <!-- AI Collaboration Mode -->
          <button class="mode-card mode-card--ai" (click)="selectAiMode()" [disabled]="isLoading()">
            <div class="mode-card__icon">
              <lucide-icon [img]="BotIcon" />
            </div>
            <div class="mode-card__content">
              <h2>Collaborate with Whispyr</h2>
              <p>Chat with Whispyr to brainstorm and build your universe together. Get creative suggestions for lore, factions, and more.</p>
              <div class="mode-card__features">
                <span class="feature"><lucide-icon [img]="SparklesIcon" /> Guided worldbuilding</span>
                <span class="feature"><lucide-icon [img]="SparklesIcon" /> Generate homebrew content</span>
                <span class="feature"><lucide-icon [img]="SparklesIcon" /> Persistent conversations</span>
              </div>
            </div>
            @if (isLoading() && selectedMode() === 'ai_collab') {
              <div class="mode-card__loading">
                <div class="spinner"></div>
              </div>
            }
          </button>

          <!-- Manual Mode -->
          <button class="mode-card mode-card--manual" (click)="selectManualMode()" [disabled]="isLoading()">
            <div class="mode-card__icon">
              <lucide-icon [img]="PenToolIcon" />
            </div>
            <div class="mode-card__content">
              <h2>Manual Creation</h2>
              <p>Build your universe step by step with full control. You can always ask Whispyr for help at any point.</p>
              <div class="mode-card__features">
                <span class="feature"><lucide-icon [img]="SparklesIcon" /> Full control</span>
                <span class="feature"><lucide-icon [img]="SparklesIcon" /> Whispyr available</span>
                <span class="feature"><lucide-icon [img]="SparklesIcon" /> Upload existing lore</span>
              </div>
            </div>
            @if (isLoading() && selectedMode() === 'manual') {
              <div class="mode-card__loading">
                <div class="spinner"></div>
              </div>
            }
          </button>
        </div>

        <!-- Draft Sessions -->
        @if (draftSessions().length > 0) {
          <section class="drafts-section">
            <h3>Resume a Draft</h3>
            <div class="drafts-list">
              @for (session of draftSessions(); track session.id) {
                <button class="draft-card" (click)="resumeSession(session.id)">
                  <div class="draft-card__icon">
                    <lucide-icon [img]="session.mode === 'ai_collab' ? BotIcon : PenToolIcon" />
                  </div>
                  <div class="draft-card__content">
                    <span class="draft-card__name">{{ session.name }}</span>
                    <span class="draft-card__meta">
                      <lucide-icon [img]="ClockIcon" />
                      {{ formatDate(session.updated_at) }}
                    </span>
                  </div>
                  <button class="draft-card__delete" (click)="deleteSession(session.id, $event)" title="Delete draft">
                    <lucide-icon [img]="Trash2Icon" />
                  </button>
                </button>
              }
            </div>
          </section>
        }

        @if (!llmConfigured() && llmChecked()) {
          <div class="llm-notice">
            <lucide-icon [img]="SettingsIcon" />
            <div>
              <strong>LLM Not Configured</strong>
              <p>AI collaboration requires an LLM endpoint. <a routerLink="/settings">Configure one in Settings</a> to enable AI features.</p>
            </div>
          </div>
        }
      </main>
    </div>
  `,
  styles: [`
    .mode-select {
      min-height: 100vh;
      position: relative;
      overflow: hidden;
    }

    .mode-select__bg {
      position: absolute;
      inset: 0;
      pointer-events: none;
      overflow: hidden;
    }

    .mode-select__orb {
      position: absolute;
      border-radius: 50%;
      filter: blur(100px);
      opacity: 0.15;
      animation: float 30s ease-in-out infinite;
    }

    .mode-select__orb--1 {
      width: 500px;
      height: 500px;
      background: var(--wk-secondary);
      top: -200px;
      right: -100px;
    }

    .mode-select__orb--2 {
      width: 400px;
      height: 400px;
      background: var(--wk-accent);
      bottom: -150px;
      left: 10%;
      animation-delay: -10s;
    }

    @keyframes float {
      0%, 100% { transform: translate(0, 0) scale(1); }
      25% { transform: translate(20px, -30px) scale(1.03); }
      50% { transform: translate(-15px, 20px) scale(0.97); }
      75% { transform: translate(-25px, -15px) scale(1.01); }
    }

    .mode-select__header {
      padding: var(--wk-space-6) var(--wk-space-8);
      position: relative;
      z-index: 10;
    }

    .back-link {
      display: inline-flex;
      align-items: center;
      gap: var(--wk-space-2);
      color: var(--wk-text-secondary);
      text-decoration: none;
      font-size: var(--wk-text-sm);
      transition: color var(--wk-transition-fast);
      lucide-icon { width: 16px; height: 16px; }
      &:hover { color: var(--wk-primary); }
    }

    .mode-select__title {
      margin-top: var(--wk-space-6);
      text-align: center;
    }

    .mode-select__title-icon {
      width: 64px;
      height: 64px;
      margin: 0 auto var(--wk-space-4);
      background: linear-gradient(135deg, var(--wk-secondary) 0%, var(--wk-accent) 100%);
      border-radius: var(--wk-radius-2xl);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 0 30px var(--wk-secondary-glow);
      lucide-icon { width: 32px; height: 32px; color: white; }
    }

    .mode-select__title h1 {
      margin: 0 0 var(--wk-space-2);
      font-size: var(--wk-text-3xl);
      font-weight: var(--wk-font-bold);
      color: var(--wk-text-primary);
    }

    .mode-select__title p {
      margin: 0;
      color: var(--wk-text-secondary);
      font-size: var(--wk-text-lg);
    }

    .mode-select__content {
      max-width: 900px;
      margin: 0 auto;
      padding: var(--wk-space-8);
      position: relative;
      z-index: 5;
    }

    .error-banner {
      display: flex;
      align-items: center;
      gap: var(--wk-space-3);
      padding: var(--wk-space-4);
      margin-bottom: var(--wk-space-6);
      background: var(--wk-error-glow);
      border: 1px solid var(--wk-error);
      border-radius: var(--wk-radius-lg);
      color: var(--wk-error);
      lucide-icon { width: 20px; height: 20px; flex-shrink: 0; }
    }

    .mode-cards {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: var(--wk-space-6);
    }

    @media (max-width: 768px) {
      .mode-cards { grid-template-columns: 1fr; }
    }

    .mode-card {
      position: relative;
      display: flex;
      flex-direction: column;
      padding: var(--wk-space-6);
      background: var(--wk-glass-bg);
      backdrop-filter: blur(var(--wk-blur-md));
      border: 2px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-2xl);
      text-align: left;
      cursor: pointer;
      transition: all var(--wk-transition-base);

      &:disabled {
        opacity: 0.7;
        cursor: not-allowed;
      }

      &:hover:not(:disabled) {
        transform: translateY(-4px);
        border-color: var(--wk-primary);
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
      }

      &--ai:hover:not(:disabled) {
        border-color: var(--wk-secondary);
        box-shadow: 0 0 30px var(--wk-secondary-glow);
      }

      &--manual:hover:not(:disabled) {
        border-color: var(--wk-accent);
        box-shadow: 0 0 30px var(--wk-accent-glow);
      }
    }

    .mode-card__icon {
      width: 56px;
      height: 56px;
      margin-bottom: var(--wk-space-4);
      border-radius: var(--wk-radius-xl);
      display: flex;
      align-items: center;
      justify-content: center;

      lucide-icon { width: 28px; height: 28px; color: white; }
    }

    .mode-card--ai .mode-card__icon {
      background: linear-gradient(135deg, var(--wk-secondary) 0%, var(--wk-accent) 100%);
    }

    .mode-card--manual .mode-card__icon {
      background: linear-gradient(135deg, var(--wk-primary) 0%, var(--wk-primary-dark) 100%);
    }

    .mode-card__content h2 {
      margin: 0 0 var(--wk-space-2);
      font-size: var(--wk-text-xl);
      font-weight: var(--wk-font-semibold);
      color: var(--wk-text-primary);
    }

    .mode-card__content p {
      margin: 0 0 var(--wk-space-4);
      color: var(--wk-text-secondary);
      font-size: var(--wk-text-sm);
      line-height: var(--wk-leading-relaxed);
    }

    .mode-card__features {
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-2);
    }

    .feature {
      display: flex;
      align-items: center;
      gap: var(--wk-space-2);
      font-size: var(--wk-text-xs);
      color: var(--wk-text-muted);
      lucide-icon { width: 12px; height: 12px; color: var(--wk-primary); }
    }

    .mode-card__loading {
      position: absolute;
      inset: 0;
      background: rgba(0, 0, 0, 0.5);
      border-radius: var(--wk-radius-2xl);
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .spinner {
      width: 32px;
      height: 32px;
      border: 3px solid var(--wk-glass-border);
      border-top-color: var(--wk-primary);
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .drafts-section {
      margin-top: var(--wk-space-10);
    }

    .drafts-section h3 {
      margin: 0 0 var(--wk-space-4);
      font-size: var(--wk-text-lg);
      font-weight: var(--wk-font-semibold);
      color: var(--wk-text-primary);
    }

    .drafts-list {
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-3);
    }

    .draft-card {
      display: flex;
      align-items: center;
      gap: var(--wk-space-4);
      padding: var(--wk-space-4);
      background: var(--wk-glass-bg);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-xl);
      cursor: pointer;
      transition: all var(--wk-transition-fast);
      text-align: left;

      &:hover {
        border-color: var(--wk-primary);
        background: var(--wk-primary-glow);
      }
    }

    .draft-card__icon {
      width: 40px;
      height: 40px;
      background: var(--wk-surface-elevated);
      border-radius: var(--wk-radius-lg);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      lucide-icon { width: 20px; height: 20px; color: var(--wk-text-secondary); }
    }

    .draft-card__content {
      flex: 1;
      min-width: 0;
    }

    .draft-card__name {
      display: block;
      font-weight: var(--wk-font-medium);
      color: var(--wk-text-primary);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .draft-card__meta {
      display: flex;
      align-items: center;
      gap: var(--wk-space-1);
      font-size: var(--wk-text-xs);
      color: var(--wk-text-muted);
      margin-top: var(--wk-space-1);
      lucide-icon { width: 12px; height: 12px; }
    }

    .draft-card__delete {
      width: 32px;
      height: 32px;
      background: transparent;
      border: 1px solid transparent;
      border-radius: var(--wk-radius-md);
      color: var(--wk-text-muted);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all var(--wk-transition-fast);
      lucide-icon { width: 16px; height: 16px; }

      &:hover {
        background: var(--wk-error-glow);
        border-color: var(--wk-error);
        color: var(--wk-error);
      }
    }

    .llm-notice {
      display: flex;
      gap: var(--wk-space-4);
      margin-top: var(--wk-space-8);
      padding: var(--wk-space-4);
      background: var(--wk-warning-glow);
      border: 1px solid var(--wk-warning);
      border-radius: var(--wk-radius-lg);
      color: var(--wk-text-primary);

      lucide-icon { width: 24px; height: 24px; color: var(--wk-warning); flex-shrink: 0; }

      strong { display: block; margin-bottom: var(--wk-space-1); }
      p { margin: 0; font-size: var(--wk-text-sm); color: var(--wk-text-secondary); }
      a { color: var(--wk-primary); text-decoration: underline; }
    }

    .animate-fade-in-down { animation: fadeInDown 0.3s ease-out forwards; }
    .animate-fade-in-up { animation: fadeInUp 0.4s ease-out forwards; }

    @keyframes fadeInDown {
      from { opacity: 0; transform: translateY(-10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    @keyframes fadeInUp {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
  `]
})
export class UniverseModeSelectComponent implements OnInit {
  private readonly worldgenService = inject(WorldgenService);
  private readonly router = inject(Router);

  readonly BotIcon = Bot;
  readonly PenToolIcon = PenTool;
  readonly ArrowLeftIcon = ArrowLeft;
  readonly SparklesIcon = Sparkles;
  readonly GlobeIcon = Globe;
  readonly ClockIcon = Clock;
  readonly Trash2Icon = Trash2;
  readonly AlertCircleIcon = AlertCircle;
  readonly SettingsIcon = Settings;

  readonly draftSessions = signal<WorldgenSessionSummary[]>([]);
  readonly isLoading = signal(false);
  readonly selectedMode = signal<'ai_collab' | 'manual' | null>(null);
  readonly errorMessage = signal('');
  readonly llmConfigured = signal(false);
  readonly llmChecked = signal(false);

  ngOnInit(): void {
    this.loadDraftSessions();
    this.checkLlmStatus();
  }

  loadDraftSessions(): void {
    this.worldgenService.listSessions().subscribe({
      next: sessions => this.draftSessions.set(sessions),
      error: () => {}
    });
  }

  checkLlmStatus(): void {
    this.worldgenService.checkLlmStatus().subscribe({
      next: status => {
        this.llmConfigured.set(status.configured);
        this.llmChecked.set(true);
      },
      error: () => this.llmChecked.set(true)
    });
  }

  selectAiMode(): void {
    if (!this.llmConfigured()) {
      this.router.navigate(['/settings']);
      return;
    }

    this.selectedMode.set('ai_collab');
    this.isLoading.set(true);
    this.errorMessage.set('');

    this.worldgenService.createSession('ai_collab').subscribe({
      next: session => {
        this.router.navigate(['/universes/build', session.id]);
      },
      error: err => {
        this.isLoading.set(false);
        this.errorMessage.set(err?.error?.error || 'Failed to create session');
      }
    });
  }

  selectManualMode(): void {
    this.selectedMode.set('manual');
    this.isLoading.set(true);
    this.errorMessage.set('');

    this.worldgenService.createSession('manual').subscribe({
      next: session => {
        this.router.navigate(['/universes/build', session.id]);
      },
      error: err => {
        this.isLoading.set(false);
        this.errorMessage.set(err?.error?.error || 'Failed to create session');
      }
    });
  }

  resumeSession(sessionId: string): void {
    this.router.navigate(['/universes/build', sessionId]);
  }

  deleteSession(sessionId: string, event: Event): void {
    event.stopPropagation();
    this.worldgenService.abandonSession(sessionId).subscribe({
      next: () => this.draftSessions.update(s => s.filter(x => x.id !== sessionId)),
      error: () => {}
    });
  }

  formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    return date.toLocaleDateString();
  }
}
