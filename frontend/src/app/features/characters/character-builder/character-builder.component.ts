import { Component, inject, input, signal, OnInit, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CharacterService, CatalogService } from '@core/services';
import { SrdRace, SrdClass, SrdBackground, CharacterSheet, AbilityScores } from '@core/models';
import {
  LucideAngularModule,
  ArrowLeft,
  User,
  Dices,
  CheckCircle2,
  Plus,
  Minus,
  HelpCircle,
  Sparkles,
  Save,
  Loader2,
  ChevronRight,
  ChevronLeft
} from 'lucide-angular';

type Step = 'race' | 'class' | 'background' | 'abilities' | 'details' | 'review';

@Component({
  selector: 'app-character-builder',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule, LucideAngularModule],
  template: `
    <div class="builder">
      <header class="builder__header">
        <a routerLink="/characters" class="back-link">
          <lucide-icon [img]="ArrowLeftIcon" />
          Back to characters
        </a>
        <h1>
          <lucide-icon [img]="UserIcon" class="header-icon" />
          {{ id() ? 'Edit Character' : 'Create Character' }}
        </h1>
      </header>

      <!-- Step indicator -->
      <nav class="steps" aria-label="Character creation steps">
        @for (s of steps; track s; let i = $index) {
          <button
            class="step"
            [class.step--active]="step() === s"
            [class.step--complete]="isStepComplete(s) && step() !== s"
            (click)="goToStep(s)"
            [disabled]="!canGoToStep(s)"
          >
            <span class="step__number">{{ i + 1 }}</span>
            <span class="step__label">{{ stepLabels[s] }}</span>
            @if (isStepComplete(s) && step() !== s) {
              <lucide-icon [img]="CheckIcon" class="step__check" />
            }
          </button>
        }
      </nav>

      <main class="builder__content">
        <!-- Race selection -->
        @if (step() === 'race') {
          <section class="step-content animate-fade-in-up">
            <div class="step-header">
              <h2>Choose a Race</h2>
              <button class="help-btn" (click)="showHelp('race')">
                <lucide-icon [img]="HelpIcon" />
              </button>
            </div>
            <p class="step-desc">Your race determines innate abilities and physical traits.</p>

            <div class="option-grid">
              @for (race of races(); track race.id) {
                <button
                  class="option-card"
                  [class.option-card--selected]="character.race === race.name"
                  (click)="selectRace(race)"
                >
                  <div class="option-card__header">
                    <h3 class="option-card__title">{{ race.name }}</h3>
                    @if (character.race === race.name) {
                      <lucide-icon [img]="CheckIcon" class="option-card__check" />
                    }
                  </div>
                  <p class="option-card__desc">{{ race.description | slice:0:100 }}...</p>
                  <div class="option-card__traits">
                    @for (trait of race.traits.slice(0, 2); track trait) {
                      <span class="trait">{{ trait }}</span>
                    }
                  </div>
                </button>
              }
            </div>

            <button class="homebrew-btn" (click)="showHomebrew.set(!showHomebrew())">
              <lucide-icon [img]="PlusIcon" />
              {{ showHomebrew() ? 'Cancel' : 'Add Homebrew Race' }}
            </button>

            @if (showHomebrew()) {
              <div class="homebrew-form animate-fade-in">
                <div class="form-group">
                  <label>Race Name</label>
                  <input [(ngModel)]="homebrewRace.name" placeholder="Enter race name" class="form-input" />
                </div>
                <div class="form-group">
                  <label>Description</label>
                  <textarea [(ngModel)]="homebrewRace.description" placeholder="Describe this race..." class="form-input" rows="3"></textarea>
                </div>
                <button class="btn btn--primary" (click)="addHomebrewRace()">
                  <lucide-icon [img]="PlusIcon" />
                  Add Race
                </button>
              </div>
            }
          </section>
        }

        <!-- Class selection -->
        @if (step() === 'class') {
          <section class="step-content animate-fade-in-up">
            <div class="step-header">
              <h2>Choose a Class</h2>
              <button class="help-btn" (click)="showHelp('class')">
                <lucide-icon [img]="HelpIcon" />
              </button>
            </div>
            <p class="step-desc">Your class defines combat style, abilities, and role.</p>

            <div class="option-grid">
              @for (cls of classes(); track cls.id) {
                <button
                  class="option-card"
                  [class.option-card--selected]="character.class_name === cls.name"
                  (click)="selectClass(cls)"
                >
                  <div class="option-card__header">
                    <h3 class="option-card__title">{{ cls.name }}</h3>
                    @if (character.class_name === cls.name) {
                      <lucide-icon [img]="CheckIcon" class="option-card__check" />
                    }
                  </div>
                  <div class="option-card__stats">
                    <span class="stat">
                      <lucide-icon [img]="DicesIcon" />
                      d{{ cls.hit_die }}
                    </span>
                    <span class="stat">{{ cls.primary_ability }}</span>
                  </div>
                </button>
              }
            </div>
          </section>
        }

        <!-- Background selection -->
        @if (step() === 'background') {
          <section class="step-content animate-fade-in-up">
            <div class="step-header">
              <h2>Choose a Background</h2>
              <button class="help-btn" (click)="showHelp('background')">
                <lucide-icon [img]="HelpIcon" />
              </button>
            </div>
            <p class="step-desc">Your background shapes your character's history.</p>

            <div class="option-grid">
              @for (bg of backgrounds(); track bg.id) {
                <button
                  class="option-card"
                  [class.option-card--selected]="character.background === bg.name"
                  (click)="selectBackground(bg)"
                >
                  <div class="option-card__header">
                    <h3 class="option-card__title">{{ bg.name }}</h3>
                    @if (character.background === bg.name) {
                      <lucide-icon [img]="CheckIcon" class="option-card__check" />
                    }
                  </div>
                  <p class="option-card__desc">{{ bg.description | slice:0:80 }}...</p>
                </button>
              }
            </div>
          </section>
        }

        <!-- Ability scores -->
        @if (step() === 'abilities') {
          <section class="step-content animate-fade-in-up">
            <div class="step-header">
              <h2>Ability Scores</h2>
              <button class="help-btn" (click)="showHelp('abilities')">
                <lucide-icon [img]="HelpIcon" />
              </button>
            </div>
            <p class="step-desc">
              Assign your scores using point-buy.
              <span class="points-badge" [class.points-badge--done]="pointsRemaining() === 0">
                {{ pointsRemaining() }} points remaining
              </span>
            </p>

            <div class="ability-grid">
              @for (ability of abilityNames; track ability) {
                <div class="ability-card">
                  <div class="ability-card__header">
                    <span class="ability-card__name">{{ ability | titlecase }}</span>
                    <span class="ability-card__mod">{{ getModifier(character.abilities![ability]) }}</span>
                  </div>
                  <div class="ability-card__controls">
                    <button
                      class="ability-btn"
                      (click)="decreaseAbility(ability)"
                      [disabled]="character.abilities![ability] <= 8"
                    >
                      <lucide-icon [img]="MinusIcon" />
                    </button>
                    <span class="ability-card__value">{{ character.abilities![ability] }}</span>
                    <button
                      class="ability-btn"
                      (click)="increaseAbility(ability)"
                      [disabled]="pointsRemaining() <= 0 || character.abilities![ability] >= 15"
                    >
                      <lucide-icon [img]="PlusIcon" />
                    </button>
                  </div>
                </div>
              }
            </div>
          </section>
        }

        <!-- Character details -->
        @if (step() === 'details') {
          <section class="step-content animate-fade-in-up">
            <div class="step-header">
              <h2>Character Details</h2>
            </div>
            <p class="step-desc">Give your character a name and personality.</p>

            <div class="details-form">
              <div class="form-row">
                <div class="form-group">
                  <label for="name">Character Name</label>
                  <input id="name" [(ngModel)]="character.name" class="form-input" placeholder="Enter name" required />
                </div>
                <div class="form-group">
                  <label for="alignment">Alignment</label>
                  <select id="alignment" [(ngModel)]="character.alignment" class="form-input">
                    @for (align of alignments; track align) {
                      <option [value]="align">{{ align }}</option>
                    }
                  </select>
                </div>
              </div>
              <div class="form-group">
                <label for="backstory">Backstory</label>
                <textarea
                  id="backstory"
                  [(ngModel)]="character.backstory"
                  class="form-input"
                  rows="5"
                  placeholder="Tell us about your character's history, motivations, and goals..."
                ></textarea>
              </div>
            </div>
          </section>
        }

        <!-- Review -->
        @if (step() === 'review') {
          <section class="step-content animate-fade-in-up">
            <div class="step-header">
              <h2>
                <lucide-icon [img]="SparklesIcon" />
                Review Character
              </h2>
            </div>

            <div class="review-card">
              <div class="review-card__header">
                <div class="review-card__avatar">
                  {{ (character.name || 'U').charAt(0).toUpperCase() }}
                </div>
                <div class="review-card__info">
                  <h3>{{ character.name || 'Unnamed Character' }}</h3>
                  <p>Level 1 {{ character.race }} {{ character.class_name }}</p>
                  <span class="review-card__badge">{{ character.background }}</span>
                  <span class="review-card__badge review-card__badge--secondary">{{ character.alignment }}</span>
                </div>
              </div>

              <div class="review-card__stats">
                @for (ability of abilityNames; track ability) {
                  <div class="review-stat">
                    <span class="review-stat__label">{{ ability | slice:0:3 | uppercase }}</span>
                    <span class="review-stat__value">{{ character.abilities![ability] }}</span>
                    <span class="review-stat__mod">{{ getModifier(character.abilities![ability]) }}</span>
                  </div>
                }
              </div>

              @if (character.backstory) {
                <div class="review-card__backstory">
                  <h4>Backstory</h4>
                  <p>{{ character.backstory }}</p>
                </div>
              }
            </div>
          </section>
        }
      </main>

      <footer class="builder__footer">
        <button class="btn" (click)="prevStep()" [disabled]="step() === 'race'">
          <lucide-icon [img]="ChevronLeftIcon" />
          Back
        </button>
        @if (step() !== 'review') {
          <button class="btn btn--primary" (click)="nextStep()" [disabled]="!isStepComplete(step())">
            Continue
            <lucide-icon [img]="ChevronRightIcon" />
          </button>
        } @else {
          <button class="btn btn--primary" (click)="saveCharacter()" [disabled]="isSaving()">
            @if (isSaving()) {
              <lucide-icon [img]="LoaderIcon" class="animate-spin" />
              Creating...
            } @else {
              <lucide-icon [img]="SaveIcon" />
              Create Character
            }
          </button>
        }
      </footer>
    </div>
  `,
  styles: [`
    .builder {
      display: flex;
      flex-direction: column;
      min-height: 100vh;
      animation: fadeIn var(--wk-transition-smooth) forwards;
    }

    .builder__header {
      padding: var(--wk-space-4) var(--wk-space-6);
      background: var(--wk-glass-bg);
      backdrop-filter: blur(var(--wk-blur-md));
      border-bottom: 1px solid var(--wk-glass-border);

      h1 {
        display: flex;
        align-items: center;
        gap: var(--wk-space-3);
        margin: var(--wk-space-2) 0 0;
        font-size: var(--wk-text-xl);
        font-weight: var(--wk-font-semibold);
      }

      .header-icon {
        width: 24px;
        height: 24px;
        color: var(--wk-primary);
      }
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

      &:hover {
        color: var(--wk-primary);
      }
    }

    /* Steps */
    .steps {
      display: flex;
      gap: var(--wk-space-2);
      padding: var(--wk-space-4) var(--wk-space-6);
      overflow-x: auto;
      background: var(--wk-glass-bg-light);
      border-bottom: 1px solid var(--wk-glass-border);
    }

    .step {
      display: flex;
      align-items: center;
      gap: var(--wk-space-2);
      padding: var(--wk-space-2) var(--wk-space-4);
      background: var(--wk-glass-bg);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-lg);
      color: var(--wk-text-secondary);
      font-size: var(--wk-text-sm);
      font-weight: var(--wk-font-medium);
      cursor: pointer;
      white-space: nowrap;
      transition: all var(--wk-transition-fast);

      &:disabled { opacity: 0.4; cursor: not-allowed; }

      &:hover:not(:disabled) {
        background: var(--wk-surface-hover);
        border-color: var(--wk-glass-border-hover);
      }

      .step__number {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        background: var(--wk-surface-elevated);
        border-radius: var(--wk-radius-full);
        font-size: var(--wk-text-xs);
      }

      .step__check {
        width: 16px;
        height: 16px;
        color: var(--wk-success);
      }

      &--active {
        background: var(--wk-primary-glow);
        border-color: var(--wk-primary);
        color: var(--wk-primary-light);

        .step__number {
          background: var(--wk-primary);
          color: white;
        }
      }

      &--complete {
        border-color: var(--wk-success);
        color: var(--wk-success);

        .step__number {
          background: var(--wk-success-glow);
          color: var(--wk-success);
        }
      }
    }

    /* Content */
    .builder__content {
      flex: 1;
      padding: var(--wk-space-6);
      overflow-y: auto;
    }

    .step-content {
      max-width: 900px;
      margin: 0 auto;
      opacity: 0;
    }

    .step-header {
      display: flex;
      align-items: center;
      gap: var(--wk-space-3);
      margin-bottom: var(--wk-space-2);

      h2 {
        display: flex;
        align-items: center;
        gap: var(--wk-space-2);
        font-size: var(--wk-text-xl);
        margin: 0;

        lucide-icon {
          width: 24px;
          height: 24px;
          color: var(--wk-warning);
        }
      }
    }

    .help-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 28px;
      height: 28px;
      background: var(--wk-glass-bg-light);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-full);
      color: var(--wk-text-muted);
      cursor: pointer;
      transition: all var(--wk-transition-fast);

      lucide-icon { width: 16px; height: 16px; }

      &:hover {
        color: var(--wk-primary);
        border-color: var(--wk-primary);
        background: var(--wk-primary-glow);
      }
    }

    .step-desc {
      color: var(--wk-text-secondary);
      margin-bottom: var(--wk-space-6);
      font-size: var(--wk-text-sm);
    }

    .points-badge {
      display: inline-flex;
      padding: var(--wk-space-1) var(--wk-space-3);
      background: var(--wk-warning-glow);
      border: 1px solid var(--wk-warning);
      border-radius: var(--wk-radius-full);
      color: var(--wk-warning);
      font-size: var(--wk-text-xs);
      font-weight: var(--wk-font-medium);
      margin-left: var(--wk-space-2);

      &--done {
        background: var(--wk-success-glow);
        border-color: var(--wk-success);
        color: var(--wk-success);
      }
    }

    /* Option cards */
    .option-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: var(--wk-space-4);
    }

    .option-card {
      position: relative;
      padding: var(--wk-space-4);
      background: var(--wk-glass-bg);
      backdrop-filter: blur(var(--wk-blur-sm));
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-xl);
      text-align: left;
      cursor: pointer;
      transition: all var(--wk-transition-fast);

      &::before {
        content: '';
        position: absolute;
        inset: 0;
        background: var(--wk-glass-shine);
        border-radius: inherit;
        pointer-events: none;
      }

      &:hover {
        border-color: var(--wk-primary);
        box-shadow: 0 0 20px var(--wk-primary-glow);
        transform: translateY(-2px);
      }

      &--selected {
        border-color: var(--wk-primary);
        background: var(--wk-primary-glow);
        box-shadow: 0 0 25px var(--wk-primary-glow);
      }

      &__header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: var(--wk-space-2);
      }

      &__title {
        font-size: var(--wk-text-base);
        font-weight: var(--wk-font-semibold);
        margin: 0;
        color: var(--wk-text-primary);
      }

      &__check {
        width: 20px;
        height: 20px;
        color: var(--wk-primary);
      }

      &__desc {
        font-size: var(--wk-text-xs);
        color: var(--wk-text-secondary);
        margin: 0 0 var(--wk-space-2);
        line-height: var(--wk-leading-relaxed);
      }

      &__traits {
        display: flex;
        gap: var(--wk-space-1);
        flex-wrap: wrap;
      }

      &__stats {
        display: flex;
        gap: var(--wk-space-3);
        margin-top: var(--wk-space-2);

        .stat {
          display: flex;
          align-items: center;
          gap: var(--wk-space-1);
          font-size: var(--wk-text-xs);
          color: var(--wk-text-muted);

          lucide-icon { width: 14px; height: 14px; }
        }
      }
    }

    .trait {
      font-size: 10px;
      padding: 2px 8px;
      background: var(--wk-surface-elevated);
      border-radius: var(--wk-radius-full);
      color: var(--wk-text-muted);
    }

    /* Homebrew */
    .homebrew-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: var(--wk-space-2);
      width: 100%;
      margin-top: var(--wk-space-6);
      padding: var(--wk-space-3);
      background: transparent;
      border: 1px dashed var(--wk-glass-border);
      border-radius: var(--wk-radius-lg);
      color: var(--wk-primary);
      font-size: var(--wk-text-sm);
      cursor: pointer;
      transition: all var(--wk-transition-fast);

      lucide-icon { width: 16px; height: 16px; }

      &:hover {
        background: var(--wk-primary-glow);
        border-color: var(--wk-primary);
      }
    }

    .homebrew-form {
      margin-top: var(--wk-space-4);
      padding: var(--wk-space-4);
      background: var(--wk-glass-bg);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-xl);
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-4);
      opacity: 0;
    }

    /* Ability cards */
    .ability-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
      gap: var(--wk-space-4);
    }

    .ability-card {
      background: var(--wk-glass-bg);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-xl);
      padding: var(--wk-space-4);
      text-align: center;

      &__header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: var(--wk-space-3);
      }

      &__name {
        font-size: var(--wk-text-sm);
        font-weight: var(--wk-font-medium);
        color: var(--wk-text-secondary);
      }

      &__mod {
        font-size: var(--wk-text-sm);
        font-weight: var(--wk-font-bold);
        color: var(--wk-primary);
      }

      &__controls {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: var(--wk-space-3);
      }

      &__value {
        font-size: var(--wk-text-2xl);
        font-weight: var(--wk-font-bold);
        color: var(--wk-text-primary);
        min-width: 40px;
      }
    }

    .ability-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 36px;
      height: 36px;
      background: var(--wk-glass-bg-light);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-lg);
      color: var(--wk-text-primary);
      cursor: pointer;
      transition: all var(--wk-transition-fast);

      lucide-icon { width: 16px; height: 16px; }

      &:hover:not(:disabled) {
        background: var(--wk-primary);
        border-color: var(--wk-primary);
        color: white;
      }

      &:disabled {
        opacity: 0.3;
        cursor: not-allowed;
      }
    }

    /* Forms */
    .details-form {
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-4);
    }

    .form-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: var(--wk-space-4);
    }

    .form-group {
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-2);

      label {
        font-size: var(--wk-text-sm);
        font-weight: var(--wk-font-medium);
        color: var(--wk-text-secondary);
      }
    }

    .form-input {
      padding: var(--wk-space-3) var(--wk-space-4);
      background: var(--wk-glass-bg);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-lg);
      color: var(--wk-text-primary);
      font-size: var(--wk-text-base);
      transition: all var(--wk-transition-fast);

      &::placeholder { color: var(--wk-text-muted); }

      &:hover {
        border-color: var(--wk-glass-border-hover);
      }

      &:focus {
        outline: none;
        border-color: var(--wk-primary);
        box-shadow: 0 0 0 3px var(--wk-primary-glow);
      }
    }

    textarea.form-input {
      resize: vertical;
      min-height: 100px;
    }

    select.form-input {
      cursor: pointer;
    }

    /* Review card */
    .review-card {
      background: var(--wk-glass-bg);
      backdrop-filter: blur(var(--wk-blur-md));
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-2xl);
      padding: var(--wk-space-6);
      position: relative;
      overflow: hidden;

      &::before {
        content: '';
        position: absolute;
        inset: 0;
        background: var(--wk-glass-shine);
        pointer-events: none;
      }

      &__header {
        display: flex;
        gap: var(--wk-space-4);
        margin-bottom: var(--wk-space-6);
      }

      &__avatar {
        width: 64px;
        height: 64px;
        background: linear-gradient(135deg, var(--wk-primary) 0%, var(--wk-primary-dark) 100%);
        border-radius: var(--wk-radius-xl);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: var(--wk-text-2xl);
        font-weight: var(--wk-font-bold);
        color: white;
        box-shadow: 0 0 20px var(--wk-primary-glow);
      }

      &__info {
        h3 {
          font-size: var(--wk-text-xl);
          margin: 0 0 var(--wk-space-1);
        }

        p {
          color: var(--wk-text-secondary);
          margin: 0 0 var(--wk-space-2);
          font-size: var(--wk-text-sm);
        }
      }

      &__badge {
        display: inline-flex;
        padding: var(--wk-space-1) var(--wk-space-3);
        background: var(--wk-primary-glow);
        border: 1px solid var(--wk-primary);
        border-radius: var(--wk-radius-full);
        color: var(--wk-primary-light);
        font-size: var(--wk-text-xs);
        font-weight: var(--wk-font-medium);
        margin-right: var(--wk-space-2);

        &--secondary {
          background: var(--wk-surface-elevated);
          border-color: var(--wk-glass-border);
          color: var(--wk-text-secondary);
        }
      }

      &__stats {
        display: flex;
        gap: var(--wk-space-4);
        padding: var(--wk-space-4) 0;
        border-top: 1px solid var(--wk-glass-border);
        border-bottom: 1px solid var(--wk-glass-border);
        margin-bottom: var(--wk-space-4);
      }

      &__backstory {
        h4 {
          font-size: var(--wk-text-sm);
          color: var(--wk-text-secondary);
          margin: 0 0 var(--wk-space-2);
        }

        p {
          font-size: var(--wk-text-sm);
          color: var(--wk-text-primary);
          line-height: var(--wk-leading-relaxed);
          margin: 0;
        }
      }
    }

    .review-stat {
      text-align: center;
      flex: 1;

      &__label {
        display: block;
        font-size: var(--wk-text-xs);
        color: var(--wk-text-muted);
        margin-bottom: var(--wk-space-1);
      }

      &__value {
        display: block;
        font-size: var(--wk-text-xl);
        font-weight: var(--wk-font-bold);
        color: var(--wk-text-primary);
      }

      &__mod {
        display: block;
        font-size: var(--wk-text-xs);
        color: var(--wk-primary);
        font-weight: var(--wk-font-medium);
      }
    }

    /* Footer */
    .builder__footer {
      display: flex;
      justify-content: space-between;
      padding: var(--wk-space-4) var(--wk-space-6);
      background: var(--wk-glass-bg);
      backdrop-filter: blur(var(--wk-blur-md));
      border-top: 1px solid var(--wk-glass-border);
    }

    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: var(--wk-space-2);
      padding: var(--wk-space-3) var(--wk-space-6);
      background: var(--wk-glass-bg-light);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-lg);
      color: var(--wk-text-primary);
      font-size: var(--wk-text-sm);
      font-weight: var(--wk-font-medium);
      cursor: pointer;
      transition: all var(--wk-transition-fast);

      lucide-icon { width: 18px; height: 18px; }

      &:hover:not(:disabled) {
        background: var(--wk-surface-hover);
        transform: translateY(-1px);
      }

      &:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      &--primary {
        background: linear-gradient(135deg, var(--wk-primary) 0%, var(--wk-primary-dark) 100%);
        border-color: var(--wk-primary);
        color: white;
        box-shadow: 0 0 15px var(--wk-primary-glow);

        &:hover:not(:disabled) {
          box-shadow: var(--wk-shadow-glow-primary);
        }
      }
    }
  `]
})
export class CharacterBuilderComponent implements OnInit {
  private readonly characterService = inject(CharacterService);
  private readonly catalogService = inject(CatalogService);
  private readonly router = inject(Router);

  // Lucide icons
  readonly ArrowLeftIcon = ArrowLeft;
  readonly UserIcon = User;
  readonly CheckIcon = CheckCircle2;
  readonly PlusIcon = Plus;
  readonly MinusIcon = Minus;
  readonly HelpIcon = HelpCircle;
  readonly DicesIcon = Dices;
  readonly SparklesIcon = Sparkles;
  readonly SaveIcon = Save;
  readonly LoaderIcon = Loader2;
  readonly ChevronRightIcon = ChevronRight;
  readonly ChevronLeftIcon = ChevronLeft;

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

  showHelp(topic: string): void {
    // Could open a modal or tooltip with help text
    console.log('Help for:', topic);
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
