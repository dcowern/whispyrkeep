import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { CampaignService, CharacterService, UniverseService, AuthService } from '@core/services';
import { Campaign, CharacterSheet, Universe } from '@core/models';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="dashboard">
      <header class="dashboard__header">
        <h1 class="dashboard__title">Welcome back{{ userName() ? ', ' + userName() : '' }}</h1>
        <p class="dashboard__subtitle">Continue your adventures</p>
      </header>

      <section class="dashboard__section">
        <div class="section__header">
          <h2 class="section__title">Active Campaigns</h2>
          <a routerLink="/campaigns/new" class="btn btn--primary">New Campaign</a>
        </div>

        @if (campaigns().length === 0) {
          <div class="empty-state">
            <p>No campaigns yet. Start your first adventure!</p>
            <a routerLink="/campaigns/new" class="btn btn--primary">Create Campaign</a>
          </div>
        } @else {
          <div class="card-grid">
            @for (campaign of campaigns(); track campaign.id) {
              <a [routerLink]="['/play', campaign.id]" class="card">
                <h3 class="card__title">{{ campaign.name }}</h3>
                <p class="card__meta">Turn {{ campaign.turn_count }}</p>
                <span class="card__badge" [class.card__badge--active]="campaign.status === 'active'">
                  {{ campaign.status }}
                </span>
              </a>
            }
          </div>
        }
      </section>

      <section class="dashboard__section">
        <div class="section__header">
          <h2 class="section__title">Characters</h2>
          <a routerLink="/characters/new" class="btn">New Character</a>
        </div>

        @if (characters().length === 0) {
          <div class="empty-state">
            <p>Create your first character to begin.</p>
            <a routerLink="/characters/new" class="btn">Create Character</a>
          </div>
        } @else {
          <div class="card-grid">
            @for (character of characters(); track character.id) {
              <a [routerLink]="['/characters', character.id]" class="card">
                <h3 class="card__title">{{ character.name }}</h3>
                <p class="card__meta">Level {{ character.level }} {{ character.race }} {{ character.class_name }}</p>
              </a>
            }
          </div>
        }
      </section>

      <section class="dashboard__section">
        <div class="section__header">
          <h2 class="section__title">Universes</h2>
          <a routerLink="/universes/new" class="btn">New Universe</a>
        </div>

        @if (universes().length === 0) {
          <div class="empty-state">
            <p>Build your first universe to set the stage.</p>
            <a routerLink="/universes/new" class="btn">Create Universe</a>
          </div>
        } @else {
          <div class="card-grid">
            @for (universe of universes(); track universe.id) {
              <a [routerLink]="['/universes', universe.id]" class="card">
                <h3 class="card__title">{{ universe.name }}</h3>
                <p class="card__meta">{{ universe.description | slice:0:60 }}...</p>
              </a>
            }
          </div>
        }
      </section>
    </div>
  `,
  styles: [`
    .dashboard {
      padding: var(--wk-space-xl);
      max-width: 1200px;
    }

    .dashboard__header {
      margin-bottom: var(--wk-space-xl);
    }

    .dashboard__title {
      font-size: 2rem;
      font-weight: 700;
      color: var(--wk-text-primary);
      margin: 0 0 var(--wk-space-xs);
    }

    .dashboard__subtitle {
      color: var(--wk-text-secondary);
      margin: 0;
    }

    .dashboard__section {
      margin-bottom: var(--wk-space-xl);
    }

    .section__header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: var(--wk-space-md);
    }

    .section__title {
      font-size: 1.25rem;
      font-weight: 600;
      color: var(--wk-text-primary);
      margin: 0;
    }

    .card-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: var(--wk-space-md);
    }

    .card {
      background-color: var(--wk-surface);
      border: 1px solid var(--wk-border);
      border-radius: var(--wk-radius-lg);
      padding: var(--wk-space-md);
      text-decoration: none;
      transition: border-color 0.2s, transform 0.2s;

      &:hover {
        border-color: var(--wk-primary);
        transform: translateY(-2px);
      }
    }

    .card__title {
      font-size: 1rem;
      font-weight: 600;
      color: var(--wk-text-primary);
      margin: 0 0 var(--wk-space-xs);
    }

    .card__meta {
      font-size: 0.875rem;
      color: var(--wk-text-secondary);
      margin: 0;
    }

    .card__badge {
      display: inline-block;
      margin-top: var(--wk-space-sm);
      padding: 2px 8px;
      font-size: 0.75rem;
      border-radius: var(--wk-radius-sm);
      background-color: var(--wk-surface-elevated);
      color: var(--wk-text-muted);

      &--active {
        background-color: rgba(16, 185, 129, 0.2);
        color: var(--wk-success);
      }
    }

    .empty-state {
      background-color: var(--wk-surface);
      border: 1px dashed var(--wk-border);
      border-radius: var(--wk-radius-lg);
      padding: var(--wk-space-xl);
      text-align: center;

      p {
        color: var(--wk-text-secondary);
        margin: 0 0 var(--wk-space-md);
      }
    }

    .btn {
      display: inline-block;
      padding: var(--wk-space-sm) var(--wk-space-md);
      border-radius: var(--wk-radius-md);
      text-decoration: none;
      font-weight: 500;
      font-size: 0.875rem;
      border: 1px solid var(--wk-border);
      color: var(--wk-text-primary);
      background-color: transparent;
      cursor: pointer;
      transition: background-color 0.2s;

      &:hover {
        background-color: var(--wk-surface-elevated);
      }

      &--primary {
        background-color: var(--wk-primary);
        border-color: var(--wk-primary);
        color: var(--wk-text-primary);

        &:hover {
          background-color: var(--wk-primary-dark);
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
