import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { UniverseService, CharacterService, CampaignService } from '@core/services';
import { Universe, CharacterSheet, CampaignCreate } from '@core/models';

type Step = 'universe' | 'character' | 'details' | 'review';

@Component({
  selector: 'app-campaign-setup',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  template: `
    <div class="setup">
      <header class="setup__header">
        <a routerLink="/campaigns" class="back-link">Back to campaigns</a>
        <h1>New Campaign</h1>
      </header>

      <nav class="steps">
        @for (s of steps; track s) {
          <button class="step" [class.step--active]="step() === s" [class.step--completed]="isStepCompleted(s)" (click)="goToStep(s)">
            {{ stepLabels[s] }}
          </button>
        }
      </nav>

      <main class="setup__content">
        <!-- Universe Selection -->
        @if (step() === 'universe') {
          <section class="step-content">
            <h2 class="label-with-help">
              Select Universe
              <span class="help-trigger">?<span class="tooltip">{{ helpText['universe'] }}</span></span>
            </h2>
            <p class="step-desc">Choose the universe where your adventure will take place.</p>
            @if (isLoadingUniverses()) {
              <p class="loading">Loading universes...</p>
            } @else if (universes().length === 0) {
              <div class="empty-state">
                <p>You don't have any universes yet.</p>
                <a routerLink="/universes/new" class="btn btn--primary">Create Universe</a>
              </div>
            } @else {
              <div class="selection-grid">
                @for (u of universes(); track u.id) {
                  <button
                    class="selection-card"
                    [class.selection-card--selected]="campaign.universe === u.id"
                    (click)="selectUniverse(u)"
                  >
                    <h3>{{ u.name }}</h3>
                    <p>{{ u.description || 'No description' }}</p>
                  </button>
                }
              </div>
            }
          </section>
        }

        <!-- Character Selection -->
        @if (step() === 'character') {
          <section class="step-content">
            <h2 class="label-with-help">
              Select Character
              <span class="help-trigger">?<span class="tooltip">{{ helpText['character'] }}</span></span>
            </h2>
            <p class="step-desc">Choose your character for this campaign.</p>
            @if (isLoadingCharacters()) {
              <p class="loading">Loading characters...</p>
            } @else if (characters().length === 0) {
              <div class="empty-state">
                <p>You don't have any characters yet.</p>
                <a routerLink="/characters/new" class="btn btn--primary">Create Character</a>
              </div>
            } @else {
              <div class="selection-grid">
                @for (c of characters(); track c.id) {
                  <button
                    class="selection-card"
                    [class.selection-card--selected]="campaign.character === c.id"
                    (click)="selectCharacter(c)"
                  >
                    <h3>{{ c.name }}</h3>
                    <p>Level {{ c.level }} {{ c.race }} {{ c.class_name }}</p>
                  </button>
                }
              </div>
            }
          </section>
        }

        <!-- Campaign Details -->
        @if (step() === 'details') {
          <section class="step-content">
            <h2>Campaign Details</h2>
            <div class="form-grid">
              <div class="form-group">
                <label for="name" class="label-with-help">
                  Campaign Name
                  <span class="help-trigger">?<span class="tooltip">{{ helpText['name'] }}</span></span>
                </label>
                <input id="name" [(ngModel)]="campaign.name" class="form-input" placeholder="The Lost Mines..." />
              </div>
              <div class="form-group form-group--full">
                <label for="description" class="label-with-help">
                  Description (Optional)
                  <span class="help-trigger">?<span class="tooltip">{{ helpText['description'] }}</span></span>
                </label>
                <textarea id="description" [(ngModel)]="campaign.description" class="form-input" rows="3" placeholder="A brief description of your adventure..."></textarea>
              </div>
              <div class="form-group">
                <label for="difficulty" class="label-with-help">
                  Difficulty
                  <span class="help-trigger">?<span class="tooltip">{{ helpText['difficulty'] }}</span></span>
                </label>
                <select id="difficulty" [(ngModel)]="campaign.difficulty" class="form-input">
                  <option value="easy">Easy - Forgiving encounters</option>
                  <option value="normal">Normal - Balanced challenge</option>
                  <option value="hard">Hard - Deadly encounters</option>
                </select>
              </div>
              <div class="form-group">
                <label for="rating" class="label-with-help">
                  Content Rating
                  <span class="help-trigger">?<span class="tooltip">{{ helpText['content_rating'] }}</span></span>
                </label>
                <select id="rating" [(ngModel)]="campaign.content_rating" class="form-input">
                  <option value="G">G - General Audiences</option>
                  <option value="PG">PG - Parental Guidance</option>
                  <option value="PG13">PG-13 - Teen</option>
                  <option value="R">R - Mature</option>
                </select>
              </div>
            </div>
          </section>
        }

        <!-- Review -->
        @if (step() === 'review') {
          <section class="step-content">
            <h2>Review Campaign</h2>
            <div class="review-card">
              <h3>{{ campaign.name || 'Unnamed Campaign' }}</h3>
              @if (campaign.description) {
                <p class="review-desc">{{ campaign.description }}</p>
              }
              <dl class="review-details">
                <div class="review-item">
                  <dt>Universe</dt>
                  <dd>{{ selectedUniverse()?.name || 'Not selected' }}</dd>
                </div>
                <div class="review-item">
                  <dt>Character</dt>
                  <dd>{{ selectedCharacter()?.name || 'Not selected' }}</dd>
                </div>
                <div class="review-item">
                  <dt>Difficulty</dt>
                  <dd>{{ difficultyLabels[campaign.difficulty || 'normal'] }}</dd>
                </div>
                <div class="review-item">
                  <dt>Content Rating</dt>
                  <dd>{{ campaign.content_rating }}</dd>
                </div>
              </dl>
            </div>
          </section>
        }
      </main>

      <footer class="setup__footer">
        <button class="btn" (click)="prevStep()" [disabled]="step() === 'universe'">Back</button>
        @if (step() !== 'review') {
          <button class="btn btn--primary" (click)="nextStep()" [disabled]="!canProceed()">Continue</button>
        } @else {
          <button class="btn btn--primary" (click)="startCampaign()" [disabled]="isSaving() || !isValid()">
            {{ isSaving() ? 'Starting...' : 'Start Campaign' }}
          </button>
        }
      </footer>
    </div>
  `,
  styles: [`
    .setup { display: flex; flex-direction: column; min-height: 100vh; }
    .setup__header { padding: var(--wk-space-md) var(--wk-space-lg); border-bottom: 1px solid var(--wk-border); }
    .setup__header h1 { margin: var(--wk-space-sm) 0 0; font-size: 1.5rem; }
    .back-link { color: var(--wk-text-secondary); text-decoration: none; font-size: 0.875rem; }

    .steps { display: flex; gap: var(--wk-space-xs); padding: var(--wk-space-md); overflow-x: auto; border-bottom: 1px solid var(--wk-border); }
    .step { padding: var(--wk-space-sm) var(--wk-space-md); border: 1px solid var(--wk-border); border-radius: var(--wk-radius-md); background: none; color: var(--wk-text-secondary); cursor: pointer; }
    .step--active { border-color: var(--wk-primary); color: var(--wk-primary); }
    .step--completed { background: var(--wk-surface-elevated); }

    .setup__content { flex: 1; padding: var(--wk-space-lg); overflow-y: auto; }
    .step-content h2 { font-size: 1.25rem; margin: 0 0 var(--wk-space-md); }
    .step-desc { color: var(--wk-text-secondary); margin-bottom: var(--wk-space-md); }
    .loading { color: var(--wk-text-muted); }

    .empty-state { text-align: center; padding: var(--wk-space-xl); background: var(--wk-surface); border-radius: var(--wk-radius-lg); }
    .empty-state p { margin-bottom: var(--wk-space-md); color: var(--wk-text-secondary); }

    .selection-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: var(--wk-space-md); }
    .selection-card { padding: var(--wk-space-md); background: var(--wk-surface); border: 2px solid var(--wk-border); border-radius: var(--wk-radius-lg); text-align: left; cursor: pointer; transition: border-color 0.2s; }
    .selection-card:hover { border-color: var(--wk-primary); }
    .selection-card--selected { border-color: var(--wk-primary); background: var(--wk-surface-elevated); }
    .selection-card h3 { margin: 0 0 var(--wk-space-xs); font-size: 1rem; }
    .selection-card p { margin: 0; font-size: 0.875rem; color: var(--wk-text-secondary); }

    .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--wk-space-md); max-width: 600px; }
    .form-group { display: flex; flex-direction: column; gap: var(--wk-space-xs); }
    .form-group--full { grid-column: 1 / -1; }
    .form-group label { font-weight: 500; font-size: 0.875rem; }
    .form-input { padding: var(--wk-space-sm); border: 1px solid var(--wk-border); border-radius: var(--wk-radius-md); background: var(--wk-background); color: var(--wk-text-primary); }

    .review-card { background: var(--wk-surface); padding: var(--wk-space-lg); border-radius: var(--wk-radius-lg); max-width: 500px; }
    .review-card h3 { margin: 0 0 var(--wk-space-sm); font-size: 1.25rem; }
    .review-desc { color: var(--wk-text-secondary); margin-bottom: var(--wk-space-md); }
    .review-details { margin: 0; }
    .review-item { display: flex; justify-content: space-between; padding: var(--wk-space-sm) 0; border-bottom: 1px solid var(--wk-border); }
    .review-item:last-child { border-bottom: none; }
    .review-item dt { font-weight: 500; }
    .review-item dd { margin: 0; color: var(--wk-text-secondary); }

    .setup__footer { display: flex; justify-content: space-between; padding: var(--wk-space-md) var(--wk-space-lg); border-top: 1px solid var(--wk-border); background: var(--wk-surface); }
    .btn { padding: var(--wk-space-sm) var(--wk-space-lg); border: 1px solid var(--wk-border); border-radius: var(--wk-radius-md); background: none; color: var(--wk-text-primary); cursor: pointer; }
    .btn:disabled { opacity: 0.5; cursor: not-allowed; }
    .btn--primary { background: var(--wk-primary); border-color: var(--wk-primary); }

    /* Tooltip styles */
    .help-trigger {
      position: relative;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 16px;
      height: 16px;
      margin-left: 6px;
      border-radius: 50%;
      background: var(--wk-surface-elevated);
      border: 1px solid var(--wk-border);
      color: var(--wk-text-muted);
      font-size: 11px;
      font-weight: 600;
      cursor: help;
      vertical-align: middle;
    }
    .help-trigger:hover { border-color: var(--wk-primary); color: var(--wk-primary); }
    .tooltip {
      position: absolute;
      top: calc(100% + 8px);
      left: 0;
      transform: translateY(-4px);
      width: 280px;
      padding: var(--wk-space-sm) var(--wk-space-md);
      background: var(--wk-surface-elevated);
      border: 1px solid var(--wk-border);
      border-radius: var(--wk-radius-md);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
      color: var(--wk-text-primary);
      font-size: 0.8125rem;
      font-weight: 400;
      line-height: 1.5;
      white-space: pre-line;
      text-align: left;
      z-index: 1000;
      opacity: 0;
      visibility: hidden;
      transition: opacity 0.15s, transform 0.15s, visibility 0.15s;
      pointer-events: none;
    }
    .help-trigger:hover .tooltip { opacity: 1; visibility: visible; transform: translateY(0); }
    .tooltip::before {
      content: '';
      position: absolute;
      bottom: 100%;
      left: 8px;
      border: 6px solid transparent;
      border-bottom-color: var(--wk-border);
    }
    .label-with-help { display: flex; align-items: center; }
  `]
})
export class CampaignSetupComponent implements OnInit {
  private readonly universeService = inject(UniverseService);
  private readonly characterService = inject(CharacterService);
  private readonly campaignService = inject(CampaignService);
  private readonly router = inject(Router);

  readonly steps: Step[] = ['universe', 'character', 'details', 'review'];
  readonly stepLabels: Record<Step, string> = {
    universe: 'Universe', character: 'Character', details: 'Details', review: 'Review'
  };
  readonly difficultyLabels: Record<string, string> = {
    easy: 'Easy', normal: 'Normal', hard: 'Hard'
  };

  readonly helpText: Record<string, string> = {
    universe: 'The universe defines the world setting, tone, and rules for your campaign. It includes lore, homebrew content, and gameplay modifiers that shape your adventure.',
    character: 'Select the character you\'ll play as in this campaign. Your character\'s abilities, class, and backstory will influence gameplay and story options.',
    name: 'A memorable name for your campaign. This helps you identify it in your campaign list and can reflect the adventure\'s theme or your character\'s journey.',
    description: 'An optional summary of your campaign\'s premise or goals. Useful for remembering the context when returning to a campaign later.',
    difficulty: 'Easy: Encounters are forgiving, enemies deal less damage, and death saves are more lenient.\n\nNormal: Standard SRD 5.2 balance with fair but challenging encounters.\n\nHard: Deadly encounters, smarter enemies, limited resources. Recommended for experienced players.',
    content_rating: 'G: Family-friendly content, no violence or mature themes.\n\nPG: Mild peril and fantasy violence, suitable for all ages.\n\nPG-13: Moderate violence, mild horror elements, some mature themes.\n\nR: Graphic violence, horror, and mature themes. Adult content only.'
  };

  readonly step = signal<Step>('universe');
  readonly universes = signal<Universe[]>([]);
  readonly characters = signal<CharacterSheet[]>([]);
  readonly isLoadingUniverses = signal(true);
  readonly isLoadingCharacters = signal(true);
  readonly isSaving = signal(false);

  campaign: CampaignCreate = {
    name: '',
    description: '',
    universe: '',
    character: '',
    difficulty: 'normal',
    content_rating: 'PG13'
  };

  ngOnInit(): void {
    this.universeService.list().subscribe({
      next: (res) => { this.universes.set(res.results); this.isLoadingUniverses.set(false); },
      error: () => this.isLoadingUniverses.set(false)
    });
    this.characterService.list().subscribe({
      next: (res) => { this.characters.set(res.results); this.isLoadingCharacters.set(false); },
      error: () => this.isLoadingCharacters.set(false)
    });
  }

  selectedUniverse = () => this.universes().find(u => u.id === this.campaign.universe);
  selectedCharacter = () => this.characters().find(c => c.id === this.campaign.character);

  selectUniverse(u: Universe): void {
    this.campaign.universe = u.id;
  }

  selectCharacter(c: CharacterSheet): void {
    this.campaign.character = c.id;
  }

  isStepCompleted(s: Step): boolean {
    switch (s) {
      case 'universe': return !!this.campaign.universe;
      case 'character': return !!this.campaign.character;
      case 'details': return !!this.campaign.name;
      default: return false;
    }
  }

  canProceed(): boolean {
    switch (this.step()) {
      case 'universe': return !!this.campaign.universe;
      case 'character': return !!this.campaign.character;
      case 'details': return !!this.campaign.name;
      default: return true;
    }
  }

  isValid(): boolean {
    return !!this.campaign.universe && !!this.campaign.character && !!this.campaign.name;
  }

  goToStep(s: Step): void {
    const targetIdx = this.steps.indexOf(s);
    const currentIdx = this.steps.indexOf(this.step());
    if (targetIdx <= currentIdx || this.canProceed()) {
      this.step.set(s);
    }
  }

  nextStep(): void {
    const idx = this.steps.indexOf(this.step());
    if (idx < this.steps.length - 1) this.step.set(this.steps[idx + 1]);
  }

  prevStep(): void {
    const idx = this.steps.indexOf(this.step());
    if (idx > 0) this.step.set(this.steps[idx - 1]);
  }

  startCampaign(): void {
    if (!this.isValid()) return;
    this.isSaving.set(true);
    this.campaignService.create(this.campaign).subscribe({
      next: (c) => this.router.navigate(['/play', c.id]),
      error: () => this.isSaving.set(false)
    });
  }
}
