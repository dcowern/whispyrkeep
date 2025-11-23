import { Component, inject, input, signal, OnInit, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CharacterService, CatalogService } from '@core/services';
import { SrdRace, SrdClass, SrdBackground, CharacterSheet, AbilityScores } from '@core/models';

type Step = 'race' | 'class' | 'background' | 'abilities' | 'details' | 'review';

@Component({
  selector: 'app-character-builder',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  template: `
    <div class="builder">
      <header class="builder__header">
        <a routerLink="/characters" class="back-link">Back to characters</a>
        <h1>{{ id() ? 'Edit Character' : 'Create Character' }}</h1>
      </header>

      <!-- Step indicator -->
      <nav class="steps" aria-label="Character creation steps">
        @for (s of steps; track s) {
          <button
            class="step"
            [class.step--active]="step() === s"
            [class.step--complete]="isStepComplete(s)"
            (click)="goToStep(s)"
            [disabled]="!canGoToStep(s)"
          >
            {{ stepLabels[s] }}
          </button>
        }
      </nav>

      <main class="builder__content">
        <!-- Race selection -->
        @if (step() === 'race') {
          <section class="step-content">
            <h2>Choose a Race</h2>
            <div class="option-grid">
              @for (race of races(); track race.id) {
                <button
                  class="option-card"
                  [class.option-card--selected]="character.race === race.name"
                  (click)="selectRace(race)"
                >
                  <h3 class="option-card__title">{{ race.name }}</h3>
                  <p class="option-card__desc">{{ race.description | slice:0:100 }}...</p>
                  <div class="option-card__traits">
                    @for (trait of race.traits.slice(0, 2); track trait) {
                      <span class="trait">{{ trait }}</span>
                    }
                  </div>
                </button>
              }
            </div>
            <!-- Homebrew toggle -->
            <button class="homebrew-btn" (click)="showHomebrew.set(!showHomebrew())">
              {{ showHomebrew() ? 'Hide' : 'Add' }} Homebrew
            </button>
            @if (showHomebrew()) {
              <div class="homebrew-form">
                <input [(ngModel)]="homebrewRace.name" placeholder="Race name" class="form-input" />
                <textarea [(ngModel)]="homebrewRace.description" placeholder="Description" class="form-input"></textarea>
                <button class="btn btn--primary" (click)="addHomebrewRace()">Add Custom Race</button>
              </div>
            }
          </section>
        }

        <!-- Class selection -->
        @if (step() === 'class') {
          <section class="step-content">
            <h2>Choose a Class</h2>
            <div class="option-grid">
              @for (cls of classes(); track cls.id) {
                <button
                  class="option-card"
                  [class.option-card--selected]="character.class_name === cls.name"
                  (click)="selectClass(cls)"
                >
                  <h3 class="option-card__title">{{ cls.name }}</h3>
                  <p class="option-card__desc">Hit Die: d{{ cls.hit_die }}</p>
                  <p class="option-card__desc">Primary: {{ cls.primary_ability }}</p>
                </button>
              }
            </div>
          </section>
        }

        <!-- Background selection -->
        @if (step() === 'background') {
          <section class="step-content">
            <h2>Choose a Background</h2>
            <div class="option-grid">
              @for (bg of backgrounds(); track bg.id) {
                <button
                  class="option-card"
                  [class.option-card--selected]="character.background === bg.name"
                  (click)="selectBackground(bg)"
                >
                  <h3 class="option-card__title">{{ bg.name }}</h3>
                  <p class="option-card__desc">{{ bg.description | slice:0:80 }}...</p>
                </button>
              }
            </div>
          </section>
        }

        <!-- Ability scores -->
        @if (step() === 'abilities') {
          <section class="step-content">
            <h2>Ability Scores</h2>
            <p class="step-desc">Assign your ability scores. You have {{ pointsRemaining() }} points remaining.</p>
            <div class="ability-grid">
              @for (ability of abilityNames; track ability) {
                <div class="ability-row">
                  <label class="ability-label">{{ ability | titlecase }}</label>
                  <button class="ability-btn" (click)="decreaseAbility(ability)" [disabled]="character.abilities![ability] <= 8">-</button>
                  <span class="ability-value">{{ character.abilities![ability] }}</span>
                  <button class="ability-btn" (click)="increaseAbility(ability)" [disabled]="pointsRemaining() <= 0 || character.abilities![ability] >= 15">+</button>
                  <span class="ability-mod">{{ getModifier(character.abilities![ability]) }}</span>
                </div>
              }
            </div>
          </section>
        }

        <!-- Character details -->
        @if (step() === 'details') {
          <section class="step-content">
            <h2>Character Details</h2>
            <div class="form-grid">
              <div class="form-group">
                <label for="name">Character Name</label>
                <input id="name" [(ngModel)]="character.name" class="form-input" required />
              </div>
              <div class="form-group">
                <label for="alignment">Alignment</label>
                <select id="alignment" [(ngModel)]="character.alignment" class="form-input">
                  @for (align of alignments; track align) {
                    <option [value]="align">{{ align }}</option>
                  }
                </select>
              </div>
              <div class="form-group form-group--full">
                <label for="backstory">Backstory</label>
                <textarea id="backstory" [(ngModel)]="character.backstory" class="form-input" rows="4"></textarea>
              </div>
            </div>
          </section>
        }

        <!-- Review -->
        @if (step() === 'review') {
          <section class="step-content">
            <h2>Review Character</h2>
            <div class="review-card">
              <h3>{{ character.name || 'Unnamed Character' }}</h3>
              <p>Level 1 {{ character.race }} {{ character.class_name }}</p>
              <p>{{ character.background }} - {{ character.alignment }}</p>
              <div class="review-stats">
                @for (ability of abilityNames; track ability) {
                  <div class="review-stat">
                    <span class="review-stat__label">{{ ability | slice:0:3 | uppercase }}</span>
                    <span class="review-stat__value">{{ character.abilities![ability] }}</span>
                  </div>
                }
              </div>
            </div>
          </section>
        }
      </main>

      <footer class="builder__footer">
        <button class="btn" (click)="prevStep()" [disabled]="step() === 'race'">Back</button>
        @if (step() !== 'review') {
          <button class="btn btn--primary" (click)="nextStep()" [disabled]="!isStepComplete(step())">
            Continue
          </button>
        } @else {
          <button class="btn btn--primary" (click)="saveCharacter()" [disabled]="isSaving()">
            {{ isSaving() ? 'Saving...' : 'Create Character' }}
          </button>
        }
      </footer>
    </div>
  `,
  styles: [`
    .builder { display: flex; flex-direction: column; min-height: 100vh; }
    .builder__header { padding: var(--wk-space-md) var(--wk-space-lg); border-bottom: 1px solid var(--wk-border); }
    .builder__header h1 { margin: var(--wk-space-sm) 0 0; font-size: 1.5rem; }
    .back-link { color: var(--wk-text-secondary); text-decoration: none; font-size: 0.875rem; }
    .back-link:hover { color: var(--wk-text-primary); }

    .steps { display: flex; gap: var(--wk-space-xs); padding: var(--wk-space-md); overflow-x: auto; border-bottom: 1px solid var(--wk-border); }
    .step { padding: var(--wk-space-sm) var(--wk-space-md); border: 1px solid var(--wk-border); border-radius: var(--wk-radius-md); background: none; color: var(--wk-text-secondary); cursor: pointer; white-space: nowrap; }
    .step:disabled { opacity: 0.5; cursor: not-allowed; }
    .step--active { border-color: var(--wk-primary); color: var(--wk-primary); }
    .step--complete { border-color: var(--wk-success); color: var(--wk-success); }

    .builder__content { flex: 1; padding: var(--wk-space-lg); overflow-y: auto; }
    .step-content h2 { font-size: 1.25rem; margin: 0 0 var(--wk-space-md); }
    .step-desc { color: var(--wk-text-secondary); margin-bottom: var(--wk-space-md); }

    .option-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: var(--wk-space-md); }
    .option-card { padding: var(--wk-space-md); border: 1px solid var(--wk-border); border-radius: var(--wk-radius-lg); background: var(--wk-surface); text-align: left; cursor: pointer; }
    .option-card:hover { border-color: var(--wk-primary); }
    .option-card--selected { border-color: var(--wk-primary); background: rgba(99, 102, 241, 0.1); }
    .option-card__title { font-size: 1rem; font-weight: 600; margin: 0 0 var(--wk-space-xs); color: var(--wk-text-primary); }
    .option-card__desc { font-size: 0.75rem; color: var(--wk-text-secondary); margin: 0; }
    .option-card__traits { display: flex; gap: var(--wk-space-xs); flex-wrap: wrap; margin-top: var(--wk-space-sm); }
    .trait { font-size: 0.625rem; padding: 2px 6px; background: var(--wk-background); border-radius: var(--wk-radius-sm); color: var(--wk-text-muted); }

    .homebrew-btn { margin-top: var(--wk-space-lg); padding: var(--wk-space-sm); background: none; border: 1px dashed var(--wk-border); border-radius: var(--wk-radius-md); color: var(--wk-primary); cursor: pointer; width: 100%; }
    .homebrew-form { margin-top: var(--wk-space-md); display: flex; flex-direction: column; gap: var(--wk-space-sm); }

    .ability-grid { display: flex; flex-direction: column; gap: var(--wk-space-sm); max-width: 400px; }
    .ability-row { display: flex; align-items: center; gap: var(--wk-space-md); }
    .ability-label { width: 100px; font-weight: 500; }
    .ability-btn { width: 32px; height: 32px; border: 1px solid var(--wk-border); border-radius: var(--wk-radius-sm); background: var(--wk-surface); color: var(--wk-text-primary); cursor: pointer; }
    .ability-btn:disabled { opacity: 0.3; cursor: not-allowed; }
    .ability-value { width: 40px; text-align: center; font-size: 1.25rem; font-weight: 600; }
    .ability-mod { color: var(--wk-text-secondary); }

    .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--wk-space-md); }
    .form-group { display: flex; flex-direction: column; gap: var(--wk-space-xs); }
    .form-group--full { grid-column: 1 / -1; }
    .form-group label { font-weight: 500; font-size: 0.875rem; }
    .form-input { padding: var(--wk-space-sm); border: 1px solid var(--wk-border); border-radius: var(--wk-radius-md); background: var(--wk-background); color: var(--wk-text-primary); }

    .review-card { background: var(--wk-surface); padding: var(--wk-space-lg); border-radius: var(--wk-radius-lg); }
    .review-card h3 { margin: 0 0 var(--wk-space-xs); }
    .review-card p { color: var(--wk-text-secondary); margin: var(--wk-space-xs) 0; }
    .review-stats { display: flex; gap: var(--wk-space-md); margin-top: var(--wk-space-md); }
    .review-stat { text-align: center; }
    .review-stat__label { display: block; font-size: 0.625rem; color: var(--wk-text-muted); }
    .review-stat__value { font-size: 1.25rem; font-weight: 600; }

    .builder__footer { display: flex; justify-content: space-between; padding: var(--wk-space-md) var(--wk-space-lg); border-top: 1px solid var(--wk-border); background: var(--wk-surface); }
    .btn { padding: var(--wk-space-sm) var(--wk-space-lg); border: 1px solid var(--wk-border); border-radius: var(--wk-radius-md); background: none; color: var(--wk-text-primary); cursor: pointer; }
    .btn:disabled { opacity: 0.5; cursor: not-allowed; }
    .btn--primary { background: var(--wk-primary); border-color: var(--wk-primary); }
  `]
})
export class CharacterBuilderComponent implements OnInit {
  private readonly characterService = inject(CharacterService);
  private readonly catalogService = inject(CatalogService);
  private readonly router = inject(Router);

  id = input<string>();

  readonly steps: Step[] = ['race', 'class', 'background', 'abilities', 'details', 'review'];
  readonly stepLabels: Record<Step, string> = {
    race: 'Race', class: 'Class', background: 'Background',
    abilities: 'Abilities', details: 'Details', review: 'Review'
  };
  readonly abilityNames: (keyof AbilityScores)[] = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'];
  readonly alignments = ['Lawful Good', 'Neutral Good', 'Chaotic Good', 'Lawful Neutral', 'True Neutral', 'Chaotic Neutral', 'Lawful Evil', 'Neutral Evil', 'Chaotic Evil'];

  readonly step = signal<Step>('race');
  readonly races = signal<SrdRace[]>([]);
  readonly classes = signal<SrdClass[]>([]);
  readonly backgrounds = signal<SrdBackground[]>([]);
  readonly showHomebrew = signal(false);
  readonly isSaving = signal(false);

  homebrewRace = { name: '', description: '' };

  character: Partial<CharacterSheet> = {
    name: '', race: '', class_name: '', background: '', alignment: 'True Neutral', backstory: '',
    abilities: { strength: 8, dexterity: 8, constitution: 8, intelligence: 8, wisdom: 8, charisma: 8 },
    level: 1
  };

  readonly pointsRemaining = computed(() => {
    const total = Object.values(this.character.abilities!).reduce((sum, val) => sum + this.getPointCost(val), 0);
    return 27 - total;
  });

  ngOnInit(): void {
    this.catalogService.listRaces().subscribe(r => this.races.set(r.results));
    this.catalogService.listClasses().subscribe(c => this.classes.set(c.results));
    this.catalogService.listBackgrounds().subscribe(b => this.backgrounds.set(b.results));
  }

  selectRace(race: SrdRace): void { this.character.race = race.name; }
  selectClass(cls: SrdClass): void { this.character.class_name = cls.name; }
  selectBackground(bg: SrdBackground): void { this.character.background = bg.name; }

  addHomebrewRace(): void {
    if (this.homebrewRace.name) {
      this.races.update(r => [...r, { id: 'custom', ...this.homebrewRace, ability_bonuses: {}, traits: [], speed: 30, size: 'Medium' }]);
      this.showHomebrew.set(false);
    }
  }

  getPointCost(score: number): number {
    if (score <= 13) return score - 8;
    if (score === 14) return 7;
    return 9;
  }

  increaseAbility(ability: keyof AbilityScores): void {
    if (this.character.abilities![ability] < 15 && this.pointsRemaining() > 0) {
      this.character.abilities![ability]++;
    }
  }

  decreaseAbility(ability: keyof AbilityScores): void {
    if (this.character.abilities![ability] > 8) {
      this.character.abilities![ability]--;
    }
  }

  getModifier(score: number): string {
    const mod = Math.floor((score - 10) / 2);
    return mod >= 0 ? `+${mod}` : `${mod}`;
  }

  isStepComplete(s: Step): boolean {
    switch (s) {
      case 'race': return !!this.character.race;
      case 'class': return !!this.character.class_name;
      case 'background': return !!this.character.background;
      case 'abilities': return this.pointsRemaining() === 0;
      case 'details': return !!this.character.name;
      case 'review': return true;
    }
  }

  canGoToStep(s: Step): boolean {
    const idx = this.steps.indexOf(s);
    return this.steps.slice(0, idx).every(step => this.isStepComplete(step));
  }

  goToStep(s: Step): void { if (this.canGoToStep(s)) this.step.set(s); }
  nextStep(): void { const idx = this.steps.indexOf(this.step()); if (idx < this.steps.length - 1) this.step.set(this.steps[idx + 1]); }
  prevStep(): void { const idx = this.steps.indexOf(this.step()); if (idx > 0) this.step.set(this.steps[idx - 1]); }

  saveCharacter(): void {
    this.isSaving.set(true);
    this.characterService.create(this.character).subscribe({
      next: (char) => this.router.navigate(['/characters', char.id]),
      error: () => this.isSaving.set(false)
    });
  }
}
