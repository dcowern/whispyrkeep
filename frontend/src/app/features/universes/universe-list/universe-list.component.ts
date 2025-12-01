import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { UniverseService } from '@core/services/universe.service';
import { Universe } from '@core/models';
import {
  LucideAngularModule,
  Plus,
  Globe,
  Calendar,
  Loader2
} from 'lucide-angular';

@Component({
  selector: 'app-universe-list',
  standalone: true,
  imports: [CommonModule, RouterLink, LucideAngularModule],
  template: `
    <main id="main-content" class="page">
      <header class="page__header">
        <div class="page__title">
          <lucide-icon [img]="GlobeIcon" />
          <h1>Universes</h1>
        </div>
        <a routerLink="new" class="btn btn--primary">
          <lucide-icon [img]="PlusIcon" />
          Create Universe
        </a>
      </header>

      <div class="page__content">
        @if (isLoading()) {
          <div class="loading">
            <lucide-icon [img]="Loader2Icon" class="animate-spin" />
            <span>Loading universes...</span>
          </div>
        } @else if (error()) {
          <div class="error">
            <p>{{ error() }}</p>
            <button class="btn btn--secondary" (click)="loadUniverses()">Try Again</button>
          </div>
        } @else if (universes().length === 0) {
          <div class="empty">
            <lucide-icon [img]="GlobeIcon" />
            <h3>No Universes Yet</h3>
            <p>Create your first universe to start building worlds for your campaigns.</p>
            <a routerLink="new" class="btn btn--primary">
              <lucide-icon [img]="PlusIcon" />
              Create Universe
            </a>
          </div>
        } @else {
          <div class="universe-grid">
            @for (universe of universes(); track universe.id) {
              <a [routerLink]="[universe.id]" class="universe-card">
                <div class="universe-card__header">
                  <lucide-icon [img]="GlobeIcon" />
                  <h3>{{ universe.name }}</h3>
                </div>
                @if (universe.description) {
                  <p class="universe-card__desc">{{ universe.description | slice:0:150 }}{{ universe.description.length > 150 ? '...' : '' }}</p>
                }
                <div class="universe-card__meta">
                  <lucide-icon [img]="CalendarIcon" />
                  <span>{{ universe.created_at | date:'mediumDate' }}</span>
                </div>
              </a>
            }
          </div>
        }
      </div>
    </main>
  `,
  styles: [`
    .page {
      padding: var(--wk-space-6);
      max-width: 1200px;
      margin: 0 auto;
    }

    .page__header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: var(--wk-space-6);
    }

    .page__title {
      display: flex;
      align-items: center;
      gap: var(--wk-space-3);

      lucide-icon {
        width: 32px;
        height: 32px;
        color: var(--wk-secondary);
      }

      h1 {
        margin: 0;
        font-size: var(--wk-text-2xl);
        font-weight: var(--wk-font-bold);
        color: var(--wk-text-primary);
      }
    }

    .loading, .error, .empty {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: var(--wk-space-4);
      padding: var(--wk-space-12);
      text-align: center;
      color: var(--wk-text-secondary);
    }

    .loading lucide-icon, .empty lucide-icon {
      width: 48px;
      height: 48px;
      color: var(--wk-text-muted);
    }

    .empty h3 {
      margin: 0;
      font-size: var(--wk-text-xl);
      color: var(--wk-text-primary);
    }

    .empty p {
      margin: 0;
      max-width: 400px;
    }

    .error {
      color: var(--wk-error);
    }

    .universe-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: var(--wk-space-4);
    }

    .universe-card {
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-3);
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
    }

    .universe-card__header {
      display: flex;
      align-items: center;
      gap: var(--wk-space-3);

      lucide-icon {
        width: 24px;
        height: 24px;
        color: var(--wk-secondary);
      }

      h3 {
        margin: 0;
        font-size: var(--wk-text-lg);
        font-weight: var(--wk-font-semibold);
        color: var(--wk-text-primary);
      }
    }

    .universe-card__desc {
      margin: 0;
      font-size: var(--wk-text-sm);
      color: var(--wk-text-secondary);
      line-height: var(--wk-leading-relaxed);
    }

    .universe-card__meta {
      display: flex;
      align-items: center;
      gap: var(--wk-space-2);
      margin-top: auto;
      padding-top: var(--wk-space-3);
      border-top: 1px solid var(--wk-glass-border);
      font-size: var(--wk-text-xs);
      color: var(--wk-text-muted);

      lucide-icon {
        width: 14px;
        height: 14px;
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

        &:hover {
          box-shadow: 0 0 20px var(--wk-primary-glow);
        }
      }

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
export class UniverseListComponent implements OnInit {
  private readonly universeService = inject(UniverseService);

  readonly GlobeIcon = Globe;
  readonly PlusIcon = Plus;
  readonly CalendarIcon = Calendar;
  readonly Loader2Icon = Loader2;

  readonly universes = signal<Universe[]>([]);
  readonly isLoading = signal(true);
  readonly error = signal<string | null>(null);

  ngOnInit(): void {
    this.loadUniverses();
  }

  loadUniverses(): void {
    this.isLoading.set(true);
    this.error.set(null);

    this.universeService.list().subscribe({
      next: (response) => {
        this.universes.set(response.results);
        this.isLoading.set(false);
      },
      error: (err) => {
        console.error('Failed to load universes:', err);
        this.error.set('Failed to load universes. Please try again.');
        this.isLoading.set(false);
      }
    });
  }
}
