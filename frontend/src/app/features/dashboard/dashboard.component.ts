import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { CampaignService, CharacterService, UniverseService, AuthService } from '@core/services';
import { Campaign, CharacterSheet, Universe } from '@core/models';
import {
  LucideAngularModule,
  Swords,
  Users,
  Globe,
  Plus,
  Play,
  Sparkles,
  BookOpen,
  Compass
} from 'lucide-angular';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, LucideAngularModule],
  template: `
    <div class="dashboard">
      <header class="dashboard__header">
        <div class="dashboard__greeting">
          <h1 class="dashboard__title">
            Welcome back{{ userName() ? ', ' + userName() : '' }}
            <lucide-icon [img]="SparklesIcon" class="dashboard__title-icon" />
          </h1>
          <p class="dashboard__subtitle">Continue your adventures in the realms</p>
        </div>
      </header>

      <!-- Campaigns Section -->
      <section class="dashboard__section animate-fade-in-up" style="animation-delay: 100ms">
        <div class="section__header">
          <div class="section__title-group">
            <div class="section__icon">
              <lucide-icon [img]="SwordsIcon" />
            </div>
            <h2 class="section__title">Active Campaigns</h2>
          </div>
          <a routerLink="/campaigns/new" class="btn btn--primary">
            <lucide-icon [img]="PlusIcon" />
            New Campaign
          </a>
        </div>

        @if (campaigns().length === 0) {
          <div class="empty-state">
            <div class="empty-state__icon">
              <lucide-icon [img]="CompassIcon" />
            </div>
            <p class="empty-state__title">No campaigns yet</p>
            <p class="empty-state__description">Start your first adventure and explore new worlds!</p>
            <a routerLink="/campaigns/new" class="btn btn--primary">
              <lucide-icon [img]="PlusIcon" />
              Create Campaign
            </a>
          </div>
        } @else {
          <div class="card-grid">
            @for (campaign of campaigns(); track campaign.id; let i = $index) {
              <a [routerLink]="['/play', campaign.id]" class="card card--interactive" [style.animation-delay]="(i * 50) + 'ms'">
                <div class="card__header">
                  <h3 class="card__title">{{ campaign.name }}</h3>
                  <span class="badge" [class.badge--success]="campaign.status === 'active'" [class.badge--warning]="campaign.status === 'paused'">
                    {{ campaign.status }}
                  </span>
                </div>
                <p class="card__meta">
                  <lucide-icon [img]="BookOpenIcon" />
                  Turn {{ campaign.turn_count }}
                </p>
                <div class="card__action">
                  <lucide-icon [img]="PlayIcon" />
                  Continue Playing
                </div>
              </a>
            }
          </div>
        }
      </section>

      <!-- Characters Section -->
      <section class="dashboard__section animate-fade-in-up" style="animation-delay: 200ms">
        <div class="section__header">
          <div class="section__title-group">
            <div class="section__icon section__icon--secondary">
              <lucide-icon [img]="UsersIcon" />
            </div>
            <h2 class="section__title">Characters</h2>
          </div>
          <a routerLink="/characters/new" class="btn">
            <lucide-icon [img]="PlusIcon" />
            New Character
          </a>
        </div>

        @if (characters().length === 0) {
          <div class="empty-state">
            <div class="empty-state__icon empty-state__icon--secondary">
              <lucide-icon [img]="UsersIcon" />
            </div>
            <p class="empty-state__title">No characters yet</p>
            <p class="empty-state__description">Create your first hero to begin your journey.</p>
            <a routerLink="/characters/new" class="btn">
              <lucide-icon [img]="PlusIcon" />
              Create Character
            </a>
          </div>
        } @else {
          <div class="card-grid">
            @for (character of characters(); track character.id; let i = $index) {
              <a [routerLink]="['/characters', character.id]" class="card card--interactive" [style.animation-delay]="(i * 50) + 'ms'">
                <div class="card__avatar">
                  {{ character.name.charAt(0).toUpperCase() }}
                </div>
                <div class="card__content">
                  <h3 class="card__title">{{ character.name }}</h3>
                  <p class="card__meta">Level {{ character.level }} {{ character.race }} {{ character.class_name }}</p>
                </div>
              </a>
            }
          </div>
        }
      </section>

      <!-- Universes Section -->
      <section class="dashboard__section animate-fade-in-up" style="animation-delay: 300ms">
        <div class="section__header">
          <div class="section__title-group">
            <div class="section__icon section__icon--accent">
              <lucide-icon [img]="GlobeIcon" />
            </div>
            <h2 class="section__title">Universes</h2>
          </div>
          <a routerLink="/universes/new" class="btn">
            <lucide-icon [img]="PlusIcon" />
            New Universe
          </a>
        </div>

        @if (universes().length === 0) {
          <div class="empty-state">
            <div class="empty-state__icon empty-state__icon--accent">
              <lucide-icon [img]="GlobeIcon" />
            </div>
            <p class="empty-state__title">No universes yet</p>
            <p class="empty-state__description">Build your first world to set the stage for adventure.</p>
            <a routerLink="/universes/new" class="btn">
              <lucide-icon [img]="PlusIcon" />
              Create Universe
            </a>
          </div>
        } @else {
          <div class="card-grid">
            @for (universe of universes(); track universe.id; let i = $index) {
              <a [routerLink]="['/universes', universe.id]" class="card card--interactive" [style.animation-delay]="(i * 50) + 'ms'">
                <h3 class="card__title">{{ universe.name }}</h3>
                <p class="card__description">{{ universe.description | slice:0:80 }}{{ universe.description.length > 80 ? '...' : '' }}</p>
              </a>
            }
          </div>
        }
      </section>
    </div>
  `,
  styles: [`
    .dashboard {
      padding: var(--wk-space-8);
      max-width: 1200px;
      animation: fadeIn var(--wk-transition-smooth) forwards;
    }

    .dashboard__header {
      margin-bottom: var(--wk-space-10);
    }

    .dashboard__greeting {
      position: relative;
    }

    .dashboard__title {
      font-size: var(--wk-text-3xl);
      font-weight: var(--wk-font-bold);
      color: var(--wk-text-primary);
      margin: 0 0 var(--wk-space-2);
      display: flex;
      align-items: center;
      gap: var(--wk-space-3);
    }

    .dashboard__title-icon {
      width: 28px;
      height: 28px;
      color: var(--wk-warning);
      animation: pulse 2s ease-in-out infinite;
    }

    .dashboard__subtitle {
      color: var(--wk-text-secondary);
      margin: 0;
      font-size: var(--wk-text-lg);
    }

    .dashboard__section {
      margin-bottom: var(--wk-space-10);
      opacity: 0;
    }

    .section__header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: var(--wk-space-6);
    }

    .section__title-group {
      display: flex;
      align-items: center;
      gap: var(--wk-space-3);
    }

    .section__icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 36px;
      height: 36px;
      background: var(--wk-primary-glow);
      border-radius: var(--wk-radius-lg);
      color: var(--wk-primary);

      lucide-icon {
        width: 20px;
        height: 20px;
      }

      &--secondary {
        background: var(--wk-secondary-glow);
        color: var(--wk-secondary);
      }

      &--accent {
        background: var(--wk-accent-glow);
        color: var(--wk-accent);
      }
    }

    .section__title {
      font-size: var(--wk-text-xl);
      font-weight: var(--wk-font-semibold);
      color: var(--wk-text-primary);
      margin: 0;
    }

    .card-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: var(--wk-space-4);
    }

    .card {
      position: relative;
      background: var(--wk-glass-bg);
      backdrop-filter: blur(var(--wk-blur-md));
      -webkit-backdrop-filter: blur(var(--wk-blur-md));
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-xl);
      padding: var(--wk-space-5);
      text-decoration: none;
      animation: fadeInUp var(--wk-transition-smooth) forwards;
      opacity: 0;

      /* Glass shine */
      &::before {
        content: '';
        position: absolute;
        inset: 0;
        background: var(--wk-glass-shine);
        border-radius: inherit;
        pointer-events: none;
      }

      &--interactive {
        cursor: pointer;
        transition:
          border-color var(--wk-transition-fast),
          box-shadow var(--wk-transition-smooth),
          transform var(--wk-transition-smooth);

        &:hover {
          border-color: var(--wk-primary);
          box-shadow: 0 0 30px var(--wk-primary-glow), var(--wk-shadow-lg);
          transform: translateY(-4px);

          .card__action {
            opacity: 1;
            color: var(--wk-primary);
          }
        }
      }
    }

    .card__header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: var(--wk-space-3);
    }

    .card__avatar {
      width: 48px;
      height: 48px;
      background: linear-gradient(135deg, var(--wk-primary) 0%, var(--wk-primary-dark) 100%);
      border-radius: var(--wk-radius-lg);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: var(--wk-text-xl);
      font-weight: var(--wk-font-bold);
      color: white;
      margin-bottom: var(--wk-space-3);
      box-shadow: 0 0 15px var(--wk-primary-glow);
    }

    .card__title {
      font-size: var(--wk-text-lg);
      font-weight: var(--wk-font-semibold);
      color: var(--wk-text-primary);
      margin: 0 0 var(--wk-space-2);
    }

    .card__meta {
      display: flex;
      align-items: center;
      gap: var(--wk-space-2);
      font-size: var(--wk-text-sm);
      color: var(--wk-text-secondary);
      margin: 0;

      lucide-icon {
        width: 14px;
        height: 14px;
      }
    }

    .card__description {
      font-size: var(--wk-text-sm);
      color: var(--wk-text-secondary);
      margin: 0;
      line-height: var(--wk-leading-relaxed);
    }

    .card__action {
      display: flex;
      align-items: center;
      gap: var(--wk-space-2);
      margin-top: var(--wk-space-4);
      padding-top: var(--wk-space-3);
      border-top: 1px solid var(--wk-glass-border);
      font-size: var(--wk-text-sm);
      font-weight: var(--wk-font-medium);
      color: var(--wk-text-muted);
      opacity: 0.7;
      transition: opacity var(--wk-transition-fast), color var(--wk-transition-fast);

      lucide-icon {
        width: 16px;
        height: 16px;
      }
    }

    .badge {
      display: inline-flex;
      align-items: center;
      padding: var(--wk-space-1) var(--wk-space-3);
      font-size: var(--wk-text-xs);
      font-weight: var(--wk-font-medium);
      border-radius: var(--wk-radius-full);
      background: var(--wk-surface-elevated);
      color: var(--wk-text-secondary);
      border: 1px solid var(--wk-glass-border);
      text-transform: capitalize;

      &--success {
        background: var(--wk-success-glow);
        color: var(--wk-success);
        border-color: var(--wk-success);
      }

      &--warning {
        background: var(--wk-warning-glow);
        color: var(--wk-warning);
        border-color: var(--wk-warning);
      }
    }

    .empty-state {
      background: var(--wk-glass-bg);
      backdrop-filter: blur(var(--wk-blur-md));
      -webkit-backdrop-filter: blur(var(--wk-blur-md));
      border: 1px dashed var(--wk-glass-border);
      border-radius: var(--wk-radius-xl);
      padding: var(--wk-space-12);
      text-align: center;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: var(--wk-space-4);
    }

    .empty-state__icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 64px;
      height: 64px;
      background: var(--wk-primary-glow);
      border-radius: var(--wk-radius-xl);
      color: var(--wk-primary);

      lucide-icon {
        width: 32px;
        height: 32px;
      }

      &--secondary {
        background: var(--wk-secondary-glow);
        color: var(--wk-secondary);
      }

      &--accent {
        background: var(--wk-accent-glow);
        color: var(--wk-accent);
      }
    }

    .empty-state__title {
      font-size: var(--wk-text-lg);
      font-weight: var(--wk-font-semibold);
      color: var(--wk-text-primary);
      margin: 0;
    }

    .empty-state__description {
      color: var(--wk-text-secondary);
      margin: 0;
      max-width: 300px;
    }

    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: var(--wk-space-2);
      padding: var(--wk-space-2) var(--wk-space-4);
      border-radius: var(--wk-radius-lg);
      text-decoration: none;
      font-weight: var(--wk-font-medium);
      font-size: var(--wk-text-sm);
      border: 1px solid var(--wk-glass-border);
      color: var(--wk-text-primary);
      background: var(--wk-glass-bg-light);
      backdrop-filter: blur(var(--wk-blur-sm));
      cursor: pointer;
      transition:
        background var(--wk-transition-fast),
        border-color var(--wk-transition-fast),
        box-shadow var(--wk-transition-fast),
        transform var(--wk-transition-fast);

      lucide-icon {
        width: 16px;
        height: 16px;
      }

      &:hover {
        background: var(--wk-surface-hover);
        border-color: var(--wk-glass-border-hover);
        transform: translateY(-1px);
      }

      &--primary {
        background: linear-gradient(135deg, var(--wk-primary) 0%, var(--wk-primary-dark) 100%);
        border-color: var(--wk-primary);
        color: white;
        box-shadow: 0 0 15px var(--wk-primary-glow);

        &:hover {
          background: linear-gradient(135deg, var(--wk-primary-light) 0%, var(--wk-primary) 100%);
          box-shadow: var(--wk-shadow-glow-primary);
        }
      }
    }
  `]
})
export class DashboardComponent implements OnInit {
  private readonly campaignService = inject(CampaignService);
  private readonly characterService = inject(CharacterService);
  private readonly universeService = inject(UniverseService);
  private readonly authService = inject(AuthService);

  // Lucide icons
  readonly SwordsIcon = Swords;
  readonly UsersIcon = Users;
  readonly GlobeIcon = Globe;
  readonly PlusIcon = Plus;
  readonly PlayIcon = Play;
  readonly SparklesIcon = Sparkles;
  readonly BookOpenIcon = BookOpen;
  readonly CompassIcon = Compass;

  readonly campaigns = signal<Campaign[]>([]);
  readonly characters = signal<CharacterSheet[]>([]);
  readonly universes = signal<Universe[]>([]);
  readonly userName = signal<string | null>(null);

  ngOnInit(): void {
    this.loadData();
    const user = this.authService.user();
    if (user) {
      this.userName.set(user.username);
    }
  }

  private loadData(): void {
    this.campaignService.list({ page_size: 6 }).subscribe({
      next: (response) => this.campaigns.set(response.results),
      error: () => this.campaigns.set([])
    });

    this.characterService.list({ page_size: 6 }).subscribe({
      next: (response) => this.characters.set(response.results),
      error: () => this.characters.set([])
    });

    this.universeService.list({ page_size: 6 }).subscribe({
      next: (response) => this.universes.set(response.results),
      error: () => this.universes.set([])
    });
  }
}
