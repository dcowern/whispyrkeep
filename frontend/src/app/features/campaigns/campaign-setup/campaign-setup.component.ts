import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { UniverseService, CharacterService, CampaignService } from '@core/services';
import { Universe, CharacterSheet, CampaignCreate } from '@core/models';
import {
  LucideAngularModule,
  Swords,
  ArrowLeft,
  Globe,
  User,
  FileText,
  CheckCircle,
  HelpCircle,
  Loader2,
  Plus,
  ChevronRight,
  ChevronLeft,
  Check,
  Play,
  Shield,
  Sparkles
} from 'lucide-angular';

type Step = 'universe' | 'character' | 'details' | 'review';

@Component({
  selector: 'app-campaign-setup',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule, LucideAngularModule],
  template: `
    <div class="setup">
      <!-- Animated background -->
      <div class="setup__bg">
        <div class="setup__orb setup__orb--1"></div>
        <div class="setup__orb setup__orb--2"></div>
      </div>

      <header class="setup__header animate-fade-in-down">
        <a routerLink="/campaigns" class="back-link">
          <lucide-icon [img]="ArrowLeftIcon" />
          Back to campaigns
        </a>
        <div class="setup__title">
          <div class="setup__title-icon">
            <lucide-icon [img]="SwordsIcon" />
          </div>
          <h1>New Campaign</h1>
        </div>
      </header>

      <nav class="steps animate-fade-in">
        @for (s of steps; track s; let i = $index) {
          <button
            class="step"
            [class.step--active]="step() === s"
            [class.step--completed]="isStepCompleted(s)"
            (click)="goToStep(s)"
          >
            <span class="step__number">
              @if (isStepCompleted(s) && step() !== s) {
                <lucide-icon [img]="CheckIcon" />
              } @else {
                {{ i + 1 }}
              }
            </span>
            <span class="step__label">{{ stepLabels[s] }}</span>
            <lucide-icon [img]="stepIcons[s]" class="step__icon" />
          </button>
        }
      </nav>

      <main class="setup__content">
        <!-- Universe Selection -->
        @if (step() === 'universe') {
          <section class="step-content animate-fade-in-up">
            <div class="step-header">
              <lucide-icon [img]="GlobeIcon" class="step-header__icon step-header__icon--secondary" />
              <div>
                <h2 class="label-with-help">
                  Select Universe
                  <span class="help-trigger">
                    <lucide-icon [img]="HelpCircleIcon" />
                    <span class="tooltip">{{ helpText['universe'] }}</span>
                  </span>
                </h2>
                <p class="step-desc">Choose the universe where your adventure will take place.</p>
              </div>
            </div>
            @if (isLoadingUniverses()) {
              <div class="loading-state">
                <lucide-icon [img]="Loader2Icon" class="animate-spin" />
                <p>Loading universes...</p>
              </div>
            } @else if (universes().length === 0) {
              <div class="empty-state">
                <lucide-icon [img]="GlobeIcon" class="empty-state__icon" />
                <p>You don't have any universes yet.</p>
                <a routerLink="/universes/new" class="btn btn--primary">
                  <lucide-icon [img]="PlusIcon" />
                  Create Universe
                </a>
              </div>
            } @else {
              <div class="selection-grid">
                @for (u of universes(); track u.id) {
                  <button
                    class="selection-card"
                    [class.selection-card--selected]="campaign.universe === u.id"
                    (click)="selectUniverse(u)"
                  >
                    <div class="selection-card__icon">
                      <lucide-icon [img]="GlobeIcon" />
                    </div>
                    <div class="selection-card__content">
                      <h3>{{ u.name }}</h3>
                      <p>{{ u.description || 'No description' }}</p>
                    </div>
                    @if (campaign.universe === u.id) {
                      <div class="selection-card__check">
                        <lucide-icon [img]="CheckIcon" />
                      </div>
                    }
                  </button>
                }
              </div>
            }
          </section>
        }

        <!-- Character Selection -->
        @if (step() === 'character') {
          <section class="step-content animate-fade-in-up">
            <div class="step-header">
              <lucide-icon [img]="UserIcon" class="step-header__icon step-header__icon--accent" />
              <div>
                <h2 class="label-with-help">
                  Select Character
                  <span class="help-trigger">
                    <lucide-icon [img]="HelpCircleIcon" />
                    <span class="tooltip">{{ helpText['character'] }}</span>
                  </span>
                </h2>
                <p class="step-desc">Choose your character for this campaign.</p>
              </div>
            </div>
            @if (isLoadingCharacters()) {
              <div class="loading-state">
                <lucide-icon [img]="Loader2Icon" class="animate-spin" />
                <p>Loading characters...</p>
              </div>
            } @else if (characters().length === 0) {
              <div class="empty-state">
                <lucide-icon [img]="UserIcon" class="empty-state__icon" />
                <p>You don't have any characters yet.</p>
                <a routerLink="/characters/new" class="btn btn--primary">
                  <lucide-icon [img]="PlusIcon" />
                  Create Character
                </a>
              </div>
            } @else {
              <div class="selection-grid">
                @for (c of characters(); track c.id) {
                  <button
                    class="selection-card"
                    [class.selection-card--selected]="campaign.character === c.id"
                    (click)="selectCharacter(c)"
                  >
                    <div class="selection-card__avatar">
                      {{ c.name.charAt(0).toUpperCase() }}
                    </div>
                    <div class="selection-card__content">
                      <h3>{{ c.name }}</h3>
                      <p>Level {{ c.level }} {{ c.race }} {{ c.class_name }}</p>
                    </div>
                    @if (campaign.character === c.id) {
                      <div class="selection-card__check">
                        <lucide-icon [img]="CheckIcon" />
                      </div>
                    }
                  </button>
                }
              </div>
            }
          </section>
        }

        <!-- Campaign Details -->
        @if (step() === 'details') {
          <section class="step-content animate-fade-in-up">
            <div class="step-header">
              <lucide-icon [img]="FileTextIcon" class="step-header__icon step-header__icon--info" />
              <div>
                <h2>Campaign Details</h2>
                <p class="step-desc">Configure your campaign settings.</p>
              </div>
            </div>
            <div class="form-grid">
              <div class="form-group form-group--full">
                <label for="name" class="label-with-help">
                  Campaign Name
                  <span class="help-trigger">
                    <lucide-icon [img]="HelpCircleIcon" />
                    <span class="tooltip">{{ helpText['name'] }}</span>
                  </span>
                </label>
                <input id="name" [(ngModel)]="campaign.name" class="form-input" placeholder="The Lost Mines..." />
              </div>
              <div class="form-group form-group--full">
                <label for="description" class="label-with-help">
                  Description (Optional)
                  <span class="help-trigger">
                    <lucide-icon [img]="HelpCircleIcon" />
                    <span class="tooltip">{{ helpText['description'] }}</span>
                  </span>
                </label>
                <textarea id="description" [(ngModel)]="campaign.description" class="form-input form-textarea" rows="3" placeholder="A brief description of your adventure..."></textarea>
              </div>
              <div class="form-group">
                <label for="difficulty" class="label-with-help">
                  Difficulty
                  <span class="help-trigger">
                    <lucide-icon [img]="HelpCircleIcon" />
                    <span class="tooltip">{{ helpText['difficulty'] }}</span>
                  </span>
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
                  <span class="help-trigger">
                    <lucide-icon [img]="HelpCircleIcon" />
                    <span class="tooltip">{{ helpText['content_rating'] }}</span>
                  </span>
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
          <section class="step-content animate-fade-in-up">
            <div class="step-header">
              <lucide-icon [img]="CheckCircleIcon" class="step-header__icon step-header__icon--success" />
              <div>
                <h2>Review Campaign</h2>
                <p class="step-desc">Review your campaign settings before starting.</p>
              </div>
            </div>
            <div class="review-card">
              <div class="review-card__header">
                <div class="review-card__icon">
                  <lucide-icon [img]="SwordsIcon" />
                </div>
                <div>
                  <h3>{{ campaign.name || 'Unnamed Campaign' }}</h3>
                  @if (campaign.description) {
                    <p class="review-card__desc">{{ campaign.description }}</p>
                  }
                </div>
              </div>
              <dl class="review-details">
                <div class="review-item">
                  <dt>
                    <lucide-icon [img]="GlobeIcon" />
                    Universe
                  </dt>
                  <dd>{{ selectedUniverse()?.name || 'Not selected' }}</dd>
                </div>
                <div class="review-item">
                  <dt>
                    <lucide-icon [img]="UserIcon" />
                    Character
                  </dt>
                  <dd>{{ selectedCharacter()?.name || 'Not selected' }}</dd>
                </div>
                <div class="review-item">
                  <dt>
                    <lucide-icon [img]="ShieldIcon" />
                    Difficulty
                  </dt>
                  <dd>{{ difficultyLabels[campaign.difficulty || 'normal'] }}</dd>
                </div>
                <div class="review-item">
                  <dt>
                    <lucide-icon [img]="SparklesIcon" />
                    Content Rating
                  </dt>
                  <dd>{{ campaign.content_rating }}</dd>
                </div>
              </dl>
            </div>
          </section>
        }
      </main>

      <footer class="setup__footer animate-fade-in-up">
        <button class="btn btn--ghost" (click)="prevStep()" [disabled]="step() === 'universe'">
          <lucide-icon [img]="ChevronLeftIcon" />
          Back
        </button>
        @if (step() !== 'review') {
          <button class="btn btn--primary" (click)="nextStep()" [disabled]="!canProceed()">
            Continue
            <lucide-icon [img]="ChevronRightIcon" />
          </button>
        } @else {
          <button class="btn btn--primary btn--glow" (click)="startCampaign()" [disabled]="isSaving() || !isValid()">
            @if (isSaving()) {
              <lucide-icon [img]="Loader2Icon" class="animate-spin" />
              Starting...
            } @else {
              <lucide-icon [img]="PlayIcon" />
              Start Campaign
            }
          </button>
        }
      </footer>
    </div>
  `,
  styles: [`
    .setup {
      display: flex;
      flex-direction: column;
      min-height: 100vh;
      position: relative;
      overflow: hidden;
    }

    /* Animated background */
    .setup__bg {
      position: absolute;
      inset: 0;
      pointer-events: none;
      overflow: hidden;
    }

    .setup__orb {
      position: absolute;
      border-radius: 50%;
      filter: blur(100px);
      opacity: 0.15;
      animation: float 30s ease-in-out infinite;
    }

    .setup__orb--1 {
      width: 500px;
      height: 500px;
      background: var(--wk-primary);
      top: -200px;
      right: -100px;
    }

    .setup__orb--2 {
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

    /* Header */
    .setup__header {
      padding: var(--wk-space-4) var(--wk-space-6);
      background: var(--wk-glass-bg);
      backdrop-filter: blur(var(--wk-blur-md));
      border-bottom: 1px solid var(--wk-glass-border);
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

    .setup__title {
      display: flex;
      align-items: center;
      gap: var(--wk-space-3);
      margin-top: var(--wk-space-3);
    }

    .setup__title-icon {
      width: 48px;
      height: 48px;
      background: linear-gradient(135deg, var(--wk-primary) 0%, var(--wk-primary-dark) 100%);
      border-radius: var(--wk-radius-xl);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 0 20px var(--wk-primary-glow);

      lucide-icon { width: 24px; height: 24px; color: white; }
    }

    .setup__header h1 {
      margin: 0;
      font-size: var(--wk-text-2xl);
      font-weight: var(--wk-font-bold);
      color: var(--wk-text-primary);
    }

    /* Steps nav */
    .steps {
      display: flex;
      gap: var(--wk-space-2);
      padding: var(--wk-space-4) var(--wk-space-6);
      overflow-x: auto;
      background: var(--wk-glass-bg);
      backdrop-filter: blur(var(--wk-blur-sm));
      border-bottom: 1px solid var(--wk-glass-border);
      position: relative;
      z-index: 10;
    }

    .step {
      display: flex;
      align-items: center;
      gap: var(--wk-space-2);
      padding: var(--wk-space-2) var(--wk-space-4);
      background: var(--wk-surface-elevated);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-full);
      color: var(--wk-text-secondary);
      cursor: pointer;
      font-size: var(--wk-text-sm);
      font-weight: var(--wk-font-medium);
      transition: all var(--wk-transition-fast);
      white-space: nowrap;

      .step__number {
        width: 22px;
        height: 22px;
        background: var(--wk-glass-border);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: var(--wk-text-xs);
        font-weight: var(--wk-font-bold);

        lucide-icon { width: 14px; height: 14px; }
      }

      .step__icon { width: 16px; height: 16px; opacity: 0.6; }

      &:hover {
        border-color: var(--wk-glass-border-hover);
        color: var(--wk-text-primary);
      }

      &--active {
        background: var(--wk-primary-glow);
        border-color: var(--wk-primary);
        color: var(--wk-primary-light);
        box-shadow: 0 0 15px var(--wk-primary-glow);

        .step__number { background: var(--wk-primary); color: white; }
        .step__icon { opacity: 1; color: var(--wk-primary); }
      }

      &--completed .step__number {
        background: var(--wk-success);
        color: white;
      }
    }

    /* Content */
    .setup__content {
      flex: 1;
      padding: var(--wk-space-8);
      overflow-y: auto;
      position: relative;
      z-index: 5;
    }

    .step-content { max-width: 800px; margin: 0 auto; }

    .step-header {
      display: flex;
      align-items: flex-start;
      gap: var(--wk-space-4);
      margin-bottom: var(--wk-space-6);
    }

    .step-header__icon {
      width: 48px;
      height: 48px;
      padding: var(--wk-space-3);
      background: var(--wk-primary-glow);
      border-radius: var(--wk-radius-xl);
      color: var(--wk-primary);
      flex-shrink: 0;

      &--secondary { background: var(--wk-secondary-glow); color: var(--wk-secondary); }
      &--accent { background: var(--wk-accent-glow); color: var(--wk-accent); }
      &--info { background: var(--wk-info-glow); color: var(--wk-info); }
      &--success { background: var(--wk-success-glow); color: var(--wk-success); }
    }

    .step-content h2 {
      font-size: var(--wk-text-xl);
      font-weight: var(--wk-font-semibold);
      margin: 0 0 var(--wk-space-1);
      color: var(--wk-text-primary);
    }

    .step-desc {
      color: var(--wk-text-secondary);
      margin: 0;
      font-size: var(--wk-text-sm);
    }

    /* Loading & Empty states */
    .loading-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: var(--wk-space-10);
      color: var(--wk-text-muted);

      lucide-icon { width: 32px; height: 32px; margin-bottom: var(--wk-space-3); }
      p { margin: 0; }
    }

    .empty-state {
      text-align: center;
      padding: var(--wk-space-10);
      background: var(--wk-glass-bg);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-2xl);
    }

    .empty-state__icon {
      width: 48px;
      height: 48px;
      color: var(--wk-text-muted);
      margin-bottom: var(--wk-space-4);
      opacity: 0.5;
    }

    .empty-state p {
      margin: 0 0 var(--wk-space-4);
      color: var(--wk-text-secondary);
    }

    /* Selection grid */
    .selection-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: var(--wk-space-4);
    }

    .selection-card {
      display: flex;
      align-items: center;
      gap: var(--wk-space-4);
      padding: var(--wk-space-4);
      background: var(--wk-glass-bg);
      border: 2px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-xl);
      text-align: left;
      cursor: pointer;
      transition: all var(--wk-transition-fast);
      position: relative;

      &:hover {
        border-color: var(--wk-primary);
        transform: translateY(-2px);
      }

      &--selected {
        border-color: var(--wk-primary);
        background: var(--wk-primary-glow);
        box-shadow: 0 0 20px var(--wk-primary-glow);
      }
    }

    .selection-card__icon {
      width: 44px;
      height: 44px;
      background: var(--wk-secondary-glow);
      border-radius: var(--wk-radius-lg);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;

      lucide-icon { width: 22px; height: 22px; color: var(--wk-secondary); }
    }

    .selection-card__avatar {
      width: 44px;
      height: 44px;
      background: linear-gradient(135deg, var(--wk-accent) 0%, var(--wk-primary) 100%);
      border-radius: var(--wk-radius-full);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      font-size: var(--wk-text-lg);
      font-weight: var(--wk-font-bold);
      color: white;
    }

    .selection-card__content {
      flex: 1;
      min-width: 0;
    }

    .selection-card h3 {
      margin: 0 0 var(--wk-space-1);
      font-size: var(--wk-text-base);
      font-weight: var(--wk-font-semibold);
      color: var(--wk-text-primary);
    }

    .selection-card p {
      margin: 0;
      font-size: var(--wk-text-sm);
      color: var(--wk-text-secondary);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .selection-card__check {
      width: 28px;
      height: 28px;
      background: var(--wk-primary);
      border-radius: var(--wk-radius-full);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;

      lucide-icon { width: 16px; height: 16px; color: white; }
    }

    /* Form grid */
    .form-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: var(--wk-space-4);
      max-width: 600px;
    }

    .form-group {
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-2);
    }

    .form-group--full { grid-column: 1 / -1; }

    .form-group label {
      font-weight: var(--wk-font-medium);
      font-size: var(--wk-text-sm);
      color: var(--wk-text-primary);
    }

    .form-input {
      padding: var(--wk-space-3) var(--wk-space-4);
      background: var(--wk-surface-elevated);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-lg);
      color: var(--wk-text-primary);
      font-size: var(--wk-text-sm);
      transition: all var(--wk-transition-fast);

      &::placeholder { color: var(--wk-text-muted); }

      &:focus {
        outline: none;
        border-color: var(--wk-primary);
        box-shadow: 0 0 0 3px var(--wk-primary-glow);
      }
    }

    .form-textarea {
      resize: vertical;
      min-height: 80px;
    }

    /* Review card */
    .review-card {
      background: var(--wk-glass-bg);
      backdrop-filter: blur(var(--wk-blur-md));
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-2xl);
      padding: var(--wk-space-6);
      max-width: 500px;
    }

    .review-card__header {
      display: flex;
      gap: var(--wk-space-4);
      margin-bottom: var(--wk-space-6);
      padding-bottom: var(--wk-space-6);
      border-bottom: 1px solid var(--wk-glass-border);
    }

    .review-card__icon {
      width: 56px;
      height: 56px;
      background: linear-gradient(135deg, var(--wk-primary) 0%, var(--wk-primary-dark) 100%);
      border-radius: var(--wk-radius-xl);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 0 20px var(--wk-primary-glow);
      flex-shrink: 0;

      lucide-icon { width: 28px; height: 28px; color: white; }
    }

    .review-card h3 {
      margin: 0 0 var(--wk-space-2);
      font-size: var(--wk-text-xl);
      font-weight: var(--wk-font-semibold);
      color: var(--wk-text-primary);
    }

    .review-card__desc {
      margin: 0;
      color: var(--wk-text-secondary);
      font-size: var(--wk-text-sm);
      line-height: var(--wk-leading-relaxed);
    }

    .review-details { margin: 0; }

    .review-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: var(--wk-space-3) 0;
      border-bottom: 1px solid var(--wk-glass-border);

      &:last-child { border-bottom: none; }
    }

    .review-item dt {
      display: flex;
      align-items: center;
      gap: var(--wk-space-2);
      font-weight: var(--wk-font-medium);
      font-size: var(--wk-text-sm);
      color: var(--wk-text-secondary);

      lucide-icon { width: 16px; height: 16px; }
    }

    .review-item dd {
      margin: 0;
      font-size: var(--wk-text-sm);
      font-weight: var(--wk-font-medium);
      color: var(--wk-text-primary);
    }

    /* Footer */
    .setup__footer {
      display: flex;
      justify-content: space-between;
      padding: var(--wk-space-4) var(--wk-space-6);
      background: var(--wk-glass-bg);
      backdrop-filter: blur(var(--wk-blur-md));
      border-top: 1px solid var(--wk-glass-border);
      position: relative;
      z-index: 10;
    }

    /* Buttons */
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: var(--wk-space-2);
      padding: var(--wk-space-3) var(--wk-space-6);
      border-radius: var(--wk-radius-lg);
      font-size: var(--wk-text-sm);
      font-weight: var(--wk-font-medium);
      cursor: pointer;
      transition: all var(--wk-transition-fast);
      text-decoration: none;

      lucide-icon { width: 18px; height: 18px; }

      &:disabled { opacity: 0.5; cursor: not-allowed; }

      &--ghost {
        background: transparent;
        border: 1px solid var(--wk-glass-border);
        color: var(--wk-text-secondary);

        &:hover:not(:disabled) {
          background: var(--wk-surface-elevated);
          color: var(--wk-text-primary);
          border-color: var(--wk-glass-border-hover);
        }
      }

      &--primary {
        background: linear-gradient(135deg, var(--wk-primary) 0%, var(--wk-primary-dark) 100%);
        border: 1px solid var(--wk-primary);
        color: white;
        box-shadow: 0 0 20px var(--wk-primary-glow);

        &:hover:not(:disabled) {
          box-shadow: 0 0 30px var(--wk-primary-glow);
          transform: translateY(-2px);
        }
      }

      &--glow {
        animation: glow 2s ease-in-out infinite;
      }
    }

    @keyframes glow {
      0%, 100% { box-shadow: 0 0 20px var(--wk-primary-glow); }
      50% { box-shadow: 0 0 35px var(--wk-primary-glow), 0 0 50px var(--wk-primary-glow); }
    }

    /* Tooltip styles */
    .help-trigger {
      position: relative;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 18px;
      height: 18px;
      margin-left: var(--wk-space-2);
      border-radius: 50%;
      background: var(--wk-surface-elevated);
      border: 1px solid var(--wk-glass-border);
      color: var(--wk-text-muted);
      cursor: help;
      vertical-align: middle;
      transition: all var(--wk-transition-fast);

      lucide-icon { width: 12px; height: 12px; }

      &:hover {
        border-color: var(--wk-primary);
        color: var(--wk-primary);
        box-shadow: 0 0 10px var(--wk-primary-glow);
      }
    }

    .tooltip {
      position: absolute;
      top: calc(100% + 8px);
      left: 50%;
      transform: translateX(-50%) translateY(-4px);
      width: 280px;
      padding: var(--wk-space-3) var(--wk-space-4);
      background: var(--wk-surface-elevated);
      backdrop-filter: blur(var(--wk-blur-md));
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-lg);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
      color: var(--wk-text-primary);
      font-size: var(--wk-text-xs);
      font-weight: var(--wk-font-normal);
      line-height: var(--wk-leading-relaxed);
      white-space: pre-line;
      text-align: left;
      z-index: 1000;
      opacity: 0;
      visibility: hidden;
      transition: opacity 0.2s, transform 0.2s, visibility 0.2s;
      pointer-events: none;
    }

    .help-trigger:hover .tooltip {
      opacity: 1;
      visibility: visible;
      transform: translateX(-50%) translateY(0);
    }

    .label-with-help { display: inline-flex; align-items: center; }

    /* Animations */
    .animate-fade-in { animation: fadeIn 0.3s ease-out forwards; }
    .animate-fade-in-down { animation: fadeInDown 0.3s ease-out forwards; }
    .animate-fade-in-up { animation: fadeInUp 0.4s ease-out forwards; }
    .animate-spin { animation: spin 1s linear infinite; }

    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    @keyframes fadeInDown {
      from { opacity: 0; transform: translateY(-10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    @keyframes fadeInUp {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
  `]
})
export class CampaignSetupComponent implements OnInit {
  private readonly universeService = inject(UniverseService);
  private readonly characterService = inject(CharacterService);
  private readonly campaignService = inject(CampaignService);
  private readonly router = inject(Router);

  // Lucide icons
  readonly SwordsIcon = Swords;
  readonly ArrowLeftIcon = ArrowLeft;
  readonly GlobeIcon = Globe;
  readonly UserIcon = User;
  readonly FileTextIcon = FileText;
  readonly CheckCircleIcon = CheckCircle;
  readonly HelpCircleIcon = HelpCircle;
  readonly Loader2Icon = Loader2;
  readonly PlusIcon = Plus;
  readonly ChevronRightIcon = ChevronRight;
  readonly ChevronLeftIcon = ChevronLeft;
  readonly CheckIcon = Check;
  readonly PlayIcon = Play;
  readonly ShieldIcon = Shield;
  readonly SparklesIcon = Sparkles;

  readonly steps: Step[] = ['universe', 'character', 'details', 'review'];
  readonly stepLabels: Record<Step, string> = {
    universe: 'Universe', character: 'Character', details: 'Details', review: 'Review'
  };
  readonly stepIcons: Record<Step, typeof Globe> = {
    universe: Globe, character: User, details: FileText, review: CheckCircle
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
