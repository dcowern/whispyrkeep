import { Component, inject, signal, input, OnInit, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { UniverseService } from '@core/services/universe.service';
import { Universe } from '@core/models';
import {
  LucideAngularModule,
  ArrowLeft,
  Globe,
  Calendar,
  Settings,
  Loader2,
  Sparkles,
  Skull,
  Sword,
  Book,
  Users
} from 'lucide-angular';

@Component({
  selector: 'app-universe-detail',
  standalone: true,
  imports: [CommonModule, RouterLink, LucideAngularModule],
  template: `
    <main id="main-content" class="page">
      @if (isLoading()) {
        <div class="loading">
          <lucide-icon [img]="Loader2Icon" class="animate-spin" />
          <span>Loading universe...</span>
        </div>
      } @else if (error()) {
        <div class="error">
          <p>{{ error() }}</p>
          <a routerLink="/universes" class="btn btn--secondary">
            <lucide-icon [img]="ArrowLeftIcon" />
            Back to Universes
          </a>
        </div>
      } @else if (universe()) {
        <header class="page__header">
          <a routerLink="/universes" class="back-link">
            <lucide-icon [img]="ArrowLeftIcon" />
            Back to universes
          </a>
          <div class="page__title">
            <lucide-icon [img]="GlobeIcon" />
            <div>
              <h1>{{ universe()!.name }}</h1>
              <span class="page__date">Created {{ universe()!.created_at | date:'mediumDate' }}</span>
            </div>
          </div>
        </header>

        <div class="page__content">
          @if (universe()!.description) {
            <section class="section">
              <h2>Description</h2>
              <p class="description">{{ universe()!.description }}</p>
            </section>
          }

          <section class="section">
            <h2>Tone Settings</h2>
            <div class="tone-grid">
              <div class="tone-item">
                <span class="tone-item__label">Darkness</span>
                <div class="tone-bar">
                  <div class="tone-bar__fill" [style.width.%]="universe()!.tone?.darkness ?? 50"></div>
                </div>
                <div class="tone-bar__labels">
                  <span>Grimdark</span>
                  <span>Cozy</span>
                </div>
              </div>
              <div class="tone-item">
                <span class="tone-item__label">Humor</span>
                <div class="tone-bar">
                  <div class="tone-bar__fill" [style.width.%]="universe()!.tone?.humor ?? 50"></div>
                </div>
                <div class="tone-bar__labels">
                  <span>Comedic</span>
                  <span>Serious</span>
                </div>
              </div>
              <div class="tone-item">
                <span class="tone-item__label">Realism</span>
                <div class="tone-bar">
                  <div class="tone-bar__fill" [style.width.%]="universe()!.tone?.realism ?? 50"></div>
                </div>
                <div class="tone-bar__labels">
                  <span>Realistic</span>
                  <span>Fantastical</span>
                </div>
              </div>
              <div class="tone-item">
                <span class="tone-item__label">Magic Level</span>
                <div class="tone-bar">
                  <div class="tone-bar__fill" [style.width.%]="universe()!.tone?.magic_level ?? 50"></div>
                </div>
                <div class="tone-bar__labels">
                  <span>Low Magic</span>
                  <span>High Magic</span>
                </div>
              </div>
            </div>
          </section>

          <section class="section">
            <h2>House Rules</h2>
            <div class="rules-grid">
              <div class="rule-item" [class.rule-item--enabled]="universe()!.rules?.permadeath">
                <lucide-icon [img]="SkullIcon" />
                <span>Permadeath</span>
                <span class="rule-item__status">{{ universe()!.rules?.permadeath ? 'Enabled' : 'Disabled' }}</span>
              </div>
              <div class="rule-item" [class.rule-item--enabled]="universe()!.rules?.critical_fumbles">
                <lucide-icon [img]="SwordIcon" />
                <span>Critical Fumbles</span>
                <span class="rule-item__status">{{ universe()!.rules?.critical_fumbles ? 'Enabled' : 'Disabled' }}</span>
              </div>
              <div class="rule-item" [class.rule-item--enabled]="universe()!.rules?.encumbrance">
                <lucide-icon [img]="BookIcon" />
                <span>Encumbrance</span>
                <span class="rule-item__status">{{ universe()!.rules?.encumbrance ? 'Enabled' : 'Disabled' }}</span>
              </div>
            </div>
          </section>

          <section class="section section--actions">
            <h2>Actions</h2>
            <div class="actions-grid">
              <a [routerLink]="['/campaigns/new']" [queryParams]="{universe: id()}" class="action-card">
                <lucide-icon [img]="UsersIcon" />
                <h3>Start Campaign</h3>
                <p>Begin a new adventure in this universe</p>
              </a>
              <a [routerLink]="['/universes', id(), 'lore']" class="action-card">
                <lucide-icon [img]="BookIcon" />
                <h3>Manage Lore</h3>
                <p>View and edit canon documents</p>
              </a>
            </div>
          </section>
        </div>
      }
    </main>
  `,
  styles: [`
    .page {
      padding: var(--wk-space-6);
      max-width: 900px;
      margin: 0 auto;
    }

    .loading, .error {
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

    .error {
      color: var(--wk-error);
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

    .page__date {
      font-size: var(--wk-text-sm);
      color: var(--wk-text-muted);
    }

    .section {
      margin-bottom: var(--wk-space-8);

      h2 {
        margin: 0 0 var(--wk-space-4);
        font-size: var(--wk-text-lg);
        font-weight: var(--wk-font-semibold);
        color: var(--wk-text-primary);
      }
    }

    .description {
      margin: 0;
      color: var(--wk-text-secondary);
      line-height: var(--wk-leading-relaxed);
      white-space: pre-wrap;
    }

    .tone-grid {
      display: grid;
      gap: var(--wk-space-4);
    }

    .tone-item {
      padding: var(--wk-space-4);
      background: var(--wk-surface);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-lg);
    }

    .tone-item__label {
      display: block;
      font-size: var(--wk-text-sm);
      font-weight: var(--wk-font-medium);
      color: var(--wk-text-primary);
      margin-bottom: var(--wk-space-2);
    }

    .tone-bar {
      height: 8px;
      background: var(--wk-surface-elevated);
      border-radius: var(--wk-radius-full);
      overflow: hidden;
    }

    .tone-bar__fill {
      height: 100%;
      background: linear-gradient(90deg, var(--wk-primary), var(--wk-secondary));
      border-radius: var(--wk-radius-full);
    }

    .tone-bar__labels {
      display: flex;
      justify-content: space-between;
      margin-top: var(--wk-space-1);
      font-size: var(--wk-text-xs);
      color: var(--wk-text-muted);
    }

    .rules-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: var(--wk-space-3);
    }

    .rule-item {
      display: flex;
      align-items: center;
      gap: var(--wk-space-3);
      padding: var(--wk-space-4);
      background: var(--wk-surface);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-lg);
      color: var(--wk-text-muted);

      lucide-icon {
        width: 20px;
        height: 20px;
        flex-shrink: 0;
      }

      span:first-of-type {
        flex: 1;
        font-weight: var(--wk-font-medium);
      }

      &--enabled {
        border-color: var(--wk-success);
        color: var(--wk-text-primary);

        lucide-icon { color: var(--wk-success); }
      }
    }

    .rule-item__status {
      font-size: var(--wk-text-xs);
      padding: var(--wk-space-1) var(--wk-space-2);
      background: var(--wk-surface-elevated);
      border-radius: var(--wk-radius-sm);
    }

    .actions-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: var(--wk-space-4);
    }

    .action-card {
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-2);
      padding: var(--wk-space-5);
      background: var(--wk-surface);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-xl);
      text-decoration: none;
      transition: all var(--wk-transition-fast);

      &:hover {
        border-color: var(--wk-primary);
        box-shadow: 0 0 20px var(--wk-primary-glow);
        transform: translateY(-2px);
      }

      lucide-icon {
        width: 28px;
        height: 28px;
        color: var(--wk-secondary);
      }

      h3 {
        margin: 0;
        font-size: var(--wk-text-base);
        font-weight: var(--wk-font-semibold);
        color: var(--wk-text-primary);
      }

      p {
        margin: 0;
        font-size: var(--wk-text-sm);
        color: var(--wk-text-secondary);
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

      &--secondary {
        background: var(--wk-surface-elevated);
        border: 1px solid var(--wk-glass-border);
        color: var(--wk-text-secondary);

        &:hover {
          background: var(--wk-surface);
          color: var(--wk-text-primary);
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
export class UniverseDetailComponent implements OnInit {
  private readonly universeService = inject(UniverseService);

  readonly ArrowLeftIcon = ArrowLeft;
  readonly GlobeIcon = Globe;
  readonly CalendarIcon = Calendar;
  readonly SettingsIcon = Settings;
  readonly Loader2Icon = Loader2;
  readonly SparklesIcon = Sparkles;
  readonly SkullIcon = Skull;
  readonly SwordIcon = Sword;
  readonly BookIcon = Book;
  readonly UsersIcon = Users;

  readonly id = input.required<string>();

  readonly universe = signal<Universe | null>(null);
  readonly isLoading = signal(true);
  readonly error = signal<string | null>(null);

  constructor() {
    // React to id changes
    effect(() => {
      const universeId = this.id();
      if (universeId) {
        this.loadUniverse(universeId);
      }
    }, { allowSignalWrites: true });
  }

  ngOnInit(): void {
    // Initial load handled by effect
  }

  private loadUniverse(id: string): void {
    this.isLoading.set(true);
    this.error.set(null);

    this.universeService.get(id).subscribe({
      next: (universe) => {
        this.universe.set(universe);
        this.isLoading.set(false);
      },
      error: (err) => {
        console.error('Failed to load universe:', err);
        this.error.set('Universe not found or you do not have access.');
        this.isLoading.set(false);
      }
    });
  }
}
