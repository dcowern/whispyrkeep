import { Component, inject, input, signal, OnInit, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { UniverseService, WorldgenService } from '@core/services';
import { UniverseCreate, WorldgenStepName } from '@core/models';
import { AiAssistPopupComponent } from '../ai-assist-popup/ai-assist-popup.component';
import {
  LucideAngularModule,
  Globe,
  ArrowLeft,
  Sparkles,
  SlidersHorizontal,
  Settings,
  MessageSquare,
  FileText,
  CheckCircle,
  HelpCircle,
  Send,
  Loader2,
  Upload,
  X,
  Check,
  ChevronRight,
  ChevronLeft,
  Wand2
} from 'lucide-angular';

type Step = 'basics' | 'tone' | 'rules' | 'cowrite' | 'lore' | 'review';

@Component({
  selector: 'app-universe-builder',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule, LucideAngularModule, AiAssistPopupComponent],
  template: `
    <div class="builder">
      <!-- Animated background -->
      <div class="builder__bg">
        <div class="builder__orb builder__orb--1"></div>
        <div class="builder__orb builder__orb--2"></div>
      </div>

      <header class="builder__header animate-fade-in-down">
        <a routerLink="/universes" class="back-link">
          <lucide-icon [img]="ArrowLeftIcon" />
          Back to universes
        </a>
        <div class="builder__title">
          <div class="builder__title-icon">
            <lucide-icon [img]="GlobeIcon" />
          </div>
          <h1>{{ id() ? 'Edit Universe' : 'Create Universe' }}</h1>
        </div>
      </header>

      <nav class="steps animate-fade-in">
        @for (s of steps; track s; let i = $index) {
          <button
            class="step"
            [class.step--active]="step() === s"
            [class.step--completed]="steps.indexOf(step()) > i"
            (click)="step.set(s)"
          >
            <span class="step__number">{{ i + 1 }}</span>
            <span class="step__label">{{ stepLabels[s] }}</span>
            <lucide-icon [img]="stepIcons[s]" class="step__icon" />
          </button>
        }
      </nav>

      <main class="builder__content">
        <!-- Basics -->
        @if (step() === 'basics') {
          <section class="step-content animate-fade-in-up">
            <div class="step-header">
              <lucide-icon [img]="GlobeIcon" class="step-header__icon" />
              <div>
                <h2>Universe Basics</h2>
                <p class="step-desc">Define the foundation of your world.</p>
              </div>
              <button class="btn btn--ai-assist" (click)="showAiAssist('basics')" title="Ask Whispyr for help">
                <lucide-icon [img]="Wand2Icon" />
                Ask Whispyr
              </button>
            </div>
            <div class="form-grid">
              <div class="form-group">
                <label for="name" class="label-with-help">
                  Universe Name
                  <span class="help-trigger">
                    <lucide-icon [img]="HelpCircleIcon" />
                    <span class="tooltip">{{ helpText['name'] }}</span>
                  </span>
                </label>
                <input id="name" [(ngModel)]="universe.name" class="form-input" placeholder="Enter a name..." />
              </div>
              <div class="form-group form-group--full">
                <label for="description" class="label-with-help">
                  Description
                  <span class="help-trigger">
                    <lucide-icon [img]="HelpCircleIcon" />
                    <span class="tooltip">{{ helpText['description'] }}</span>
                  </span>
                </label>
                <textarea id="description" [(ngModel)]="universe.description" class="form-input form-textarea" rows="4" placeholder="Describe your universe..."></textarea>
              </div>
            </div>
          </section>
        }

        <!-- Tone sliders -->
        @if (step() === 'tone') {
          <section class="step-content animate-fade-in-up">
            <div class="step-header">
              <lucide-icon [img]="SlidersHorizontalIcon" class="step-header__icon step-header__icon--secondary" />
              <div>
                <h2>Universe Tone</h2>
                <p class="step-desc">Adjust sliders to set the tone of your universe.</p>
              </div>
              <button class="btn btn--ai-assist" (click)="showAiAssist('tone')" title="Ask Whispyr for suggestions">
                <lucide-icon [img]="Wand2Icon" />
                Ask Whispyr
              </button>
            </div>
            <div class="sliders-container">
              @for (slider of toneSliders; track slider.key) {
                <div class="slider-group">
                  <label class="slider-label label-with-help">
                    {{ slider.label }}
                    <span class="help-trigger">
                      <lucide-icon [img]="HelpCircleIcon" />
                      <span class="tooltip">{{ helpText[slider.key] }}</span>
                    </span>
                  </label>
                  <div class="slider-track">
                    <input type="range" min="0" max="100" [(ngModel)]="universe.tone![slider.key]" class="slider" />
                    <div class="slider-fill" [style.width.%]="universe.tone![slider.key]"></div>
                  </div>
                  <span class="slider-value">{{ universe.tone![slider.key] }}</span>
                </div>
              }
            </div>
          </section>
        }

        <!-- Rules -->
        @if (step() === 'rules') {
          <section class="step-content animate-fade-in-up">
            <div class="step-header">
              <lucide-icon [img]="SettingsIcon" class="step-header__icon step-header__icon--accent" />
              <div>
                <h2>Optional Rules</h2>
                <p class="step-desc">Enable or disable optional gameplay rules.</p>
              </div>
              <button class="btn btn--ai-assist" (click)="showAiAssist('rules')" title="Ask Whispyr for recommendations">
                <lucide-icon [img]="Wand2Icon" />
                Ask Whispyr
              </button>
            </div>
            <div class="rules-list">
              <label class="rule-toggle" [class.rule-toggle--active]="universe.rules!.permadeath">
                <div class="rule-toggle__checkbox">
                  <input type="checkbox" [(ngModel)]="universe.rules!.permadeath" />
                  <lucide-icon [img]="CheckIcon" class="rule-toggle__check" />
                </div>
                <div class="rule-toggle__content">
                  <span class="rule-toggle__label label-with-help">
                    Permadeath
                    <span class="help-trigger">
                      <lucide-icon [img]="HelpCircleIcon" />
                      <span class="tooltip">{{ helpText['permadeath'] }}</span>
                    </span>
                  </span>
                  <span class="rule-toggle__desc">Death is permanent, no resurrection</span>
                </div>
              </label>
              <label class="rule-toggle" [class.rule-toggle--active]="universe.rules!.critical_fumbles">
                <div class="rule-toggle__checkbox">
                  <input type="checkbox" [(ngModel)]="universe.rules!.critical_fumbles" />
                  <lucide-icon [img]="CheckIcon" class="rule-toggle__check" />
                </div>
                <div class="rule-toggle__content">
                  <span class="rule-toggle__label label-with-help">
                    Critical Fumbles
                    <span class="help-trigger">
                      <lucide-icon [img]="HelpCircleIcon" />
                      <span class="tooltip">{{ helpText['critical_fumbles'] }}</span>
                    </span>
                  </span>
                  <span class="rule-toggle__desc">Natural 1s cause additional mishaps</span>
                </div>
              </label>
              <label class="rule-toggle" [class.rule-toggle--active]="universe.rules!.encumbrance">
                <div class="rule-toggle__checkbox">
                  <input type="checkbox" [(ngModel)]="universe.rules!.encumbrance" />
                  <lucide-icon [img]="CheckIcon" class="rule-toggle__check" />
                </div>
                <div class="rule-toggle__content">
                  <span class="rule-toggle__label label-with-help">
                    Encumbrance Tracking
                    <span class="help-trigger">
                      <lucide-icon [img]="HelpCircleIcon" />
                      <span class="tooltip">{{ helpText['encumbrance'] }}</span>
                    </span>
                  </span>
                  <span class="rule-toggle__desc">Carry weight affects movement</span>
                </div>
              </label>
            </div>
          </section>
        }

        <!-- Co-write chat -->
        @if (step() === 'cowrite') {
          <section class="step-content animate-fade-in-up">
            <div class="step-header">
              <lucide-icon [img]="MessageSquareIcon" class="step-header__icon step-header__icon--info" />
              <div>
                <h2 class="label-with-help">
                  Co-write with AI
                  <span class="help-trigger">
                    <lucide-icon [img]="HelpCircleIcon" />
                    <span class="tooltip">{{ helpText['cowrite'] }}</span>
                  </span>
                </h2>
                <p class="step-desc">Chat with the AI to develop your universe's lore and details.</p>
              </div>
            </div>
            <div class="chat-box">
              @for (msg of chatMessages(); track $index) {
                <div class="chat-msg" [class.chat-msg--user]="msg.role === 'user'">
                  <div class="chat-msg__avatar" [class.chat-msg__avatar--user]="msg.role === 'user'">
                    <lucide-icon [img]="msg.role === 'user' ? GlobeIcon : SparklesIcon" />
                  </div>
                  <div class="chat-msg__content">{{ msg.content }}</div>
                </div>
              }
              @if (chatMessages().length === 0) {
                <div class="chat-empty">
                  <lucide-icon [img]="SparklesIcon" />
                  <p>Start chatting to develop your universe...</p>
                </div>
              }
            </div>
            <form class="chat-form" (ngSubmit)="sendChatMessage()">
              <input [(ngModel)]="chatInput" name="chatInput" class="form-input" placeholder="Ask about your universe..." />
              <button type="submit" class="btn btn--primary btn--icon" [disabled]="isGenerating()">
                @if (isGenerating()) {
                  <lucide-icon [img]="Loader2Icon" class="animate-spin" />
                } @else {
                  <lucide-icon [img]="SendIcon" />
                }
              </button>
            </form>
          </section>
        }

        <!-- Lore upload -->
        @if (step() === 'lore') {
          <section class="step-content animate-fade-in-up">
            <div class="step-header">
              <lucide-icon [img]="FileTextIcon" class="step-header__icon step-header__icon--warning" />
              <div>
                <h2 class="label-with-help">
                  Upload Lore Documents
                  <span class="help-trigger">
                    <lucide-icon [img]="HelpCircleIcon" />
                    <span class="tooltip">{{ helpText['lore'] }}</span>
                  </span>
                </h2>
                <p class="step-desc">Upload existing documents to establish hard canon for your universe.</p>
              </div>
            </div>
            <div class="upload-area" (click)="fileInput.click()" (dragover)="$event.preventDefault()" (drop)="onFileDrop($event)">
              <lucide-icon [img]="UploadIcon" class="upload-area__icon" />
              <p class="upload-area__text">Drag files here or click to upload</p>
              <p class="upload-hint">Supports .txt, .md, .pdf</p>
            </div>
            <input #fileInput type="file" (change)="onFileSelect($event)" accept=".txt,.md,.pdf" hidden multiple />
            @if (uploadedFiles().length > 0) {
              <ul class="file-list">
                @for (file of uploadedFiles(); track file.name) {
                  <li class="file-item">
                    <lucide-icon [img]="FileTextIcon" class="file-item__icon" />
                    <span class="file-item__name">{{ file.name }}</span>
                    <button class="file-remove" (click)="removeFile(file)" type="button">
                      <lucide-icon [img]="XIcon" />
                    </button>
                  </li>
                }
              </ul>
            }
          </section>
        }

        <!-- Review -->
        @if (step() === 'review') {
          <section class="step-content animate-fade-in-up">
            <div class="step-header">
              <lucide-icon [img]="CheckCircleIcon" class="step-header__icon step-header__icon--success" />
              <div>
                <h2>Review Universe</h2>
                <p class="step-desc">Review your universe settings before creating.</p>
              </div>
            </div>
            <div class="review-card">
              <div class="review-card__header">
                <div class="review-card__icon">
                  <lucide-icon [img]="GlobeIcon" />
                </div>
                <div>
                  <h3>{{ universe.name || 'Unnamed Universe' }}</h3>
                  <p class="review-card__desc">{{ universe.description || 'No description provided' }}</p>
                </div>
              </div>
              <div class="review-tone">
                <h4>Tone Settings</h4>
                @for (slider of toneSliders; track slider.key) {
                  <div class="tone-bar">
                    <span class="tone-bar__label">{{ slider.label }}</span>
                    <div class="tone-bar__track">
                      <div class="tone-bar__fill" [style.width.%]="universe.tone![slider.key]"></div>
                    </div>
                    <span class="tone-bar__value">{{ universe.tone![slider.key] }}</span>
                  </div>
                }
              </div>
              <div class="review-rules">
                <h4>Active Rules</h4>
                <div class="review-rules__list">
                  @if (universe.rules!.permadeath) {
                    <span class="review-rule">Permadeath</span>
                  }
                  @if (universe.rules!.critical_fumbles) {
                    <span class="review-rule">Critical Fumbles</span>
                  }
                  @if (universe.rules!.encumbrance) {
                    <span class="review-rule">Encumbrance</span>
                  }
                  @if (!universe.rules!.permadeath && !universe.rules!.critical_fumbles && !universe.rules!.encumbrance) {
                    <span class="review-rule review-rule--none">Standard Rules</span>
                  }
                </div>
              </div>
            </div>
          </section>
        }
      </main>

      <footer class="builder__footer animate-fade-in-up">
        <button class="btn btn--ghost" (click)="prevStep()" [disabled]="step() === 'basics'">
          <lucide-icon [img]="ChevronLeftIcon" />
          Back
        </button>
        @if (step() !== 'review') {
          <button class="btn btn--primary" (click)="nextStep()">
            Continue
            <lucide-icon [img]="ChevronRightIcon" />
          </button>
        } @else {
          <button class="btn btn--primary" (click)="saveUniverse()" [disabled]="isSaving()">
            @if (isSaving()) {
              <lucide-icon [img]="Loader2Icon" class="animate-spin" />
              Creating...
            } @else {
              <lucide-icon [img]="CheckIcon" />
              Create Universe
            }
          </button>
        }
      </footer>

      <!-- AI Assist Popup -->
      <app-ai-assist-popup
        #aiAssistPopup
        [sessionId]="worldgenSessionId()"
        [currentStep]="aiAssistStep()"
        (closed)="onAiAssistClosed()"
        (dataUpdated)="onAiDataUpdated()"
      />
    </div>
  `,
  styles: [`
    .builder {
      display: flex;
      flex-direction: column;
      min-height: 100vh;
      position: relative;
      overflow: hidden;
    }

    /* Animated background */
    .builder__bg {
      position: absolute;
      inset: 0;
      pointer-events: none;
      overflow: hidden;
    }

    .builder__orb {
      position: absolute;
      border-radius: 50%;
      filter: blur(100px);
      opacity: 0.15;
      animation: float 30s ease-in-out infinite;
    }

    .builder__orb--1 {
      width: 500px;
      height: 500px;
      background: var(--wk-secondary);
      top: -200px;
      right: -100px;
    }

    .builder__orb--2 {
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
    .builder__header {
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

    .builder__title {
      display: flex;
      align-items: center;
      gap: var(--wk-space-3);
      margin-top: var(--wk-space-3);
    }

    .builder__title-icon {
      width: 48px;
      height: 48px;
      background: linear-gradient(135deg, var(--wk-secondary) 0%, var(--wk-accent) 100%);
      border-radius: var(--wk-radius-xl);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 0 20px var(--wk-secondary-glow);

      lucide-icon {
        width: 24px;
        height: 24px;
        color: white;
      }
    }

    .builder__header h1 {
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
        width: 20px;
        height: 20px;
        background: var(--wk-glass-border);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: var(--wk-text-xs);
        font-weight: var(--wk-font-bold);
      }

      .step__icon {
        width: 16px;
        height: 16px;
        opacity: 0.6;
      }

      &:hover {
        border-color: var(--wk-glass-border-hover);
        color: var(--wk-text-primary);
      }

      &--active {
        background: var(--wk-primary-glow);
        border-color: var(--wk-primary);
        color: var(--wk-primary-light);
        box-shadow: 0 0 15px var(--wk-primary-glow);

        .step__number {
          background: var(--wk-primary);
          color: white;
        }

        .step__icon {
          opacity: 1;
          color: var(--wk-primary);
        }
      }

      &--completed {
        .step__number {
          background: var(--wk-success);
          color: white;
        }
      }
    }

    /* Content */
    .builder__content {
      flex: 1;
      padding: var(--wk-space-8);
      overflow-y: auto;
      position: relative;
      z-index: 5;
    }

    .step-content {
      max-width: 700px;
      margin: 0 auto;
    }

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

      &--secondary {
        background: var(--wk-secondary-glow);
        color: var(--wk-secondary);
      }

      &--accent {
        background: var(--wk-accent-glow);
        color: var(--wk-accent);
      }

      &--info {
        background: var(--wk-info-glow);
        color: var(--wk-info);
      }

      &--warning {
        background: var(--wk-warning-glow);
        color: var(--wk-warning);
      }

      &--success {
        background: var(--wk-success-glow);
        color: var(--wk-success);
      }
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

    /* Forms */
    .form-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: var(--wk-space-4);
    }

    .form-group {
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-2);
    }

    .form-group--full {
      grid-column: 1 / -1;
    }

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
      min-height: 100px;
    }

    /* Sliders */
    .sliders-container {
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-4);
    }

    .slider-group {
      display: flex;
      align-items: center;
      gap: var(--wk-space-4);
      padding: var(--wk-space-4);
      background: var(--wk-glass-bg);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-xl);
    }

    .slider-label {
      width: 140px;
      font-weight: var(--wk-font-medium);
      font-size: var(--wk-text-sm);
      color: var(--wk-text-primary);
      flex-shrink: 0;
    }

    .slider-track {
      flex: 1;
      position: relative;
      height: 8px;
      background: var(--wk-surface-elevated);
      border-radius: var(--wk-radius-full);
    }

    .slider {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      opacity: 0;
      cursor: pointer;
      z-index: 2;
    }

    .slider-fill {
      position: absolute;
      top: 0;
      left: 0;
      height: 100%;
      background: linear-gradient(90deg, var(--wk-primary), var(--wk-secondary));
      border-radius: var(--wk-radius-full);
      transition: width 0.1s;
    }

    .slider-value {
      width: 48px;
      text-align: center;
      padding: var(--wk-space-1) var(--wk-space-2);
      background: var(--wk-primary-glow);
      border-radius: var(--wk-radius-md);
      font-size: var(--wk-text-sm);
      font-weight: var(--wk-font-semibold);
      color: var(--wk-primary);
    }

    /* Rules */
    .rules-list {
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-3);
    }

    .rule-toggle {
      display: flex;
      align-items: center;
      gap: var(--wk-space-4);
      padding: var(--wk-space-4);
      background: var(--wk-glass-bg);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-xl);
      cursor: pointer;
      transition: all var(--wk-transition-fast);

      input { display: none; }

      &:hover {
        border-color: var(--wk-glass-border-hover);
      }

      &--active {
        border-color: var(--wk-primary);
        background: var(--wk-primary-glow);

        .rule-toggle__checkbox {
          background: var(--wk-primary);
          border-color: var(--wk-primary);
        }

        .rule-toggle__check {
          opacity: 1;
          transform: scale(1);
        }
      }
    }

    .rule-toggle__checkbox {
      width: 24px;
      height: 24px;
      background: var(--wk-surface-elevated);
      border: 2px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      transition: all var(--wk-transition-fast);
    }

    .rule-toggle__check {
      width: 14px;
      height: 14px;
      color: white;
      opacity: 0;
      transform: scale(0.5);
      transition: all var(--wk-transition-fast);
    }

    .rule-toggle__content {
      flex: 1;
    }

    .rule-toggle__label {
      font-weight: var(--wk-font-medium);
      color: var(--wk-text-primary);
    }

    .rule-toggle__desc {
      display: block;
      font-size: var(--wk-text-xs);
      color: var(--wk-text-secondary);
      margin-top: var(--wk-space-1);
    }

    /* Chat */
    .chat-box {
      background: var(--wk-glass-bg);
      backdrop-filter: blur(var(--wk-blur-md));
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-xl);
      padding: var(--wk-space-4);
      min-height: 250px;
      max-height: 350px;
      overflow-y: auto;
      margin-bottom: var(--wk-space-4);
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-3);
    }

    .chat-empty {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      color: var(--wk-text-muted);
      text-align: center;

      lucide-icon {
        width: 48px;
        height: 48px;
        margin-bottom: var(--wk-space-3);
        opacity: 0.5;
      }

      p {
        margin: 0;
        font-size: var(--wk-text-sm);
      }
    }

    .chat-msg {
      display: flex;
      gap: var(--wk-space-3);
      max-width: 85%;

      &--user {
        flex-direction: row-reverse;
        margin-left: auto;
      }
    }

    .chat-msg__avatar {
      width: 32px;
      height: 32px;
      background: linear-gradient(135deg, var(--wk-secondary) 0%, var(--wk-accent) 100%);
      border-radius: var(--wk-radius-full);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;

      lucide-icon {
        width: 16px;
        height: 16px;
        color: white;
      }

      &--user {
        background: linear-gradient(135deg, var(--wk-primary) 0%, var(--wk-primary-dark) 100%);
      }
    }

    .chat-msg__content {
      padding: var(--wk-space-3) var(--wk-space-4);
      background: var(--wk-surface-elevated);
      border-radius: var(--wk-radius-lg);
      font-size: var(--wk-text-sm);
      line-height: var(--wk-leading-relaxed);
    }

    .chat-msg--user .chat-msg__content {
      background: linear-gradient(135deg, var(--wk-primary) 0%, var(--wk-primary-dark) 100%);
      color: white;
    }

    .chat-form {
      display: flex;
      gap: var(--wk-space-3);
    }

    .chat-form .form-input {
      flex: 1;
    }

    /* Upload */
    .upload-area {
      border: 2px dashed var(--wk-glass-border);
      border-radius: var(--wk-radius-xl);
      padding: var(--wk-space-10);
      text-align: center;
      cursor: pointer;
      transition: all var(--wk-transition-fast);
      background: var(--wk-glass-bg);

      &:hover {
        border-color: var(--wk-primary);
        background: var(--wk-primary-glow);
      }
    }

    .upload-area__icon {
      width: 48px;
      height: 48px;
      color: var(--wk-text-muted);
      margin-bottom: var(--wk-space-3);
    }

    .upload-area__text {
      margin: 0 0 var(--wk-space-2);
      color: var(--wk-text-primary);
      font-weight: var(--wk-font-medium);
    }

    .upload-hint {
      font-size: var(--wk-text-xs);
      color: var(--wk-text-muted);
      margin: 0;
    }

    .file-list {
      list-style: none;
      padding: 0;
      margin: var(--wk-space-4) 0 0;
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-2);
    }

    .file-item {
      display: flex;
      align-items: center;
      gap: var(--wk-space-3);
      padding: var(--wk-space-3) var(--wk-space-4);
      background: var(--wk-glass-bg);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-lg);
    }

    .file-item__icon {
      width: 20px;
      height: 20px;
      color: var(--wk-warning);
    }

    .file-item__name {
      flex: 1;
      font-size: var(--wk-text-sm);
      color: var(--wk-text-primary);
    }

    .file-remove {
      width: 28px;
      height: 28px;
      background: var(--wk-error-glow);
      border: none;
      border-radius: var(--wk-radius-md);
      color: var(--wk-error);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all var(--wk-transition-fast);

      lucide-icon {
        width: 16px;
        height: 16px;
      }

      &:hover {
        background: var(--wk-error);
        color: white;
      }
    }

    /* Review */
    .review-card {
      background: var(--wk-glass-bg);
      backdrop-filter: blur(var(--wk-blur-md));
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-2xl);
      padding: var(--wk-space-6);
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
      background: linear-gradient(135deg, var(--wk-secondary) 0%, var(--wk-accent) 100%);
      border-radius: var(--wk-radius-xl);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 0 20px var(--wk-secondary-glow);
      flex-shrink: 0;

      lucide-icon {
        width: 28px;
        height: 28px;
        color: white;
      }
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

    .review-tone, .review-rules {
      margin-bottom: var(--wk-space-6);
    }

    .review-tone h4, .review-rules h4 {
      font-size: var(--wk-text-sm);
      font-weight: var(--wk-font-semibold);
      color: var(--wk-text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin: 0 0 var(--wk-space-3);
    }

    .tone-bar {
      display: flex;
      align-items: center;
      gap: var(--wk-space-3);
      margin-bottom: var(--wk-space-2);
    }

    .tone-bar__label {
      width: 100px;
      font-size: var(--wk-text-sm);
      color: var(--wk-text-secondary);
    }

    .tone-bar__track {
      flex: 1;
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

    .tone-bar__value {
      width: 32px;
      text-align: right;
      font-size: var(--wk-text-sm);
      font-weight: var(--wk-font-semibold);
      color: var(--wk-primary);
    }

    .review-rules__list {
      display: flex;
      flex-wrap: wrap;
      gap: var(--wk-space-2);
    }

    .review-rule {
      padding: var(--wk-space-2) var(--wk-space-3);
      background: var(--wk-primary-glow);
      border: 1px solid var(--wk-primary);
      border-radius: var(--wk-radius-full);
      font-size: var(--wk-text-xs);
      font-weight: var(--wk-font-medium);
      color: var(--wk-primary);

      &--none {
        background: var(--wk-surface-elevated);
        border-color: var(--wk-glass-border);
        color: var(--wk-text-secondary);
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

      lucide-icon {
        width: 18px;
        height: 18px;
      }

      &:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

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

      &--icon {
        width: 48px;
        height: 48px;
        padding: 0;
        border-radius: var(--wk-radius-full);
      }

      &--ai-assist {
        margin-left: auto;
        background: linear-gradient(135deg, var(--wk-secondary) 0%, var(--wk-accent) 100%);
        border: 1px solid var(--wk-secondary);
        color: white;
        padding: var(--wk-space-2) var(--wk-space-4);
        box-shadow: 0 0 15px var(--wk-secondary-glow);

        lucide-icon {
          width: 16px;
          height: 16px;
        }

        &:hover:not(:disabled) {
          box-shadow: 0 0 25px var(--wk-secondary-glow);
          transform: translateY(-2px);
        }
      }
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

      lucide-icon {
        width: 12px;
        height: 12px;
      }

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

    .label-with-help {
      display: inline-flex;
      align-items: center;
    }

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
export class UniverseBuilderComponent implements OnInit {
  private readonly universeService = inject(UniverseService);
  private readonly worldgenService = inject(WorldgenService);
  private readonly router = inject(Router);

  @ViewChild('aiAssistPopup') aiAssistPopup?: AiAssistPopupComponent;

  // Lucide icons
  readonly GlobeIcon = Globe;
  readonly ArrowLeftIcon = ArrowLeft;
  readonly SparklesIcon = Sparkles;
  readonly SlidersHorizontalIcon = SlidersHorizontal;
  readonly SettingsIcon = Settings;
  readonly MessageSquareIcon = MessageSquare;
  readonly FileTextIcon = FileText;
  readonly CheckCircleIcon = CheckCircle;
  readonly HelpCircleIcon = HelpCircle;
  readonly SendIcon = Send;
  readonly Loader2Icon = Loader2;
  readonly UploadIcon = Upload;
  readonly XIcon = X;
  readonly CheckIcon = Check;
  readonly ChevronRightIcon = ChevronRight;
  readonly ChevronLeftIcon = ChevronLeft;
  readonly Wand2Icon = Wand2;

  id = input<string>();

  readonly steps: Step[] = ['basics', 'tone', 'rules', 'cowrite', 'lore', 'review'];
  readonly stepLabels: Record<Step, string> = {
    basics: 'Basics', tone: 'Tone', rules: 'Rules', cowrite: 'Co-write', lore: 'Lore', review: 'Review'
  };
  readonly stepIcons: Record<Step, typeof Globe> = {
    basics: Globe, tone: SlidersHorizontal, rules: Settings, cowrite: MessageSquare, lore: FileText, review: CheckCircle
  };
  readonly toneSliders = [
    { key: 'darkness' as const, label: 'Darkness' },
    { key: 'humor' as const, label: 'Humor' },
    { key: 'realism' as const, label: 'Realism' },
    { key: 'magic_level' as const, label: 'Magic Level' }
  ];

  readonly helpText: Record<string, string> = {
    // Basics
    name: 'A unique name for your universe. This will be displayed in your universe list and when selecting a universe for campaigns.',
    description: 'A brief overview of your universe\'s setting, themes, and unique characteristics. This helps the AI understand the world and maintain consistency during gameplay.',

    // Tone sliders
    darkness: 'Controls the overall mood and content intensity.\n\n0 (Light): Uplifting themes, minimal violence, happy endings common.\n\n50 (Balanced): Mix of light and dark elements, moderate stakes.\n\n100 (Dark): Grim themes, high stakes, morally complex situations, mature content.',
    humor: 'Sets how much comedic relief appears in narratives.\n\n0 (Serious): Dramatic tone, realistic dialogue, minimal jokes.\n\n50 (Balanced): Occasional wit and levity mixed with serious moments.\n\n100 (Comedic): Frequent humor, absurd situations, witty banter throughout.',
    realism: 'Determines how grounded or fantastical the world feels.\n\n0 (Cinematic): Rule of cool prevails, dramatic license, heroes perform impossible feats.\n\n50 (Balanced): Generally realistic with moments of dramatic flair.\n\n100 (Gritty): Realistic consequences, limited resources matter, injuries are serious.',
    magic_level: 'Controls magic\'s prevalence and power in your world.\n\n0 (Low Magic): Magic is rare and mysterious, few practitioners exist.\n\n50 (Standard Fantasy): Magic is known but not commonplace, follows SRD rules.\n\n100 (High Magic): Magic is everywhere, powerful spells are common, magical solutions abound.',

    // Rules
    permadeath: 'When ENABLED: Character death is permanent. If your character dies, they cannot be resurrected by any means. Creates high-stakes gameplay with meaningful consequences.\n\nWhen DISABLED: Standard resurrection rules apply. Characters can be brought back through spells like Revivify or Raise Dead.',
    critical_fumbles: 'When ENABLED: Rolling a natural 1 on attack rolls causes additional negative effects beyond simply missing—dropped weapons, friendly fire, or embarrassing mishaps.\n\nWhen DISABLED: Natural 1s are automatic misses with no additional penalties (standard SRD rules).',
    encumbrance: 'When ENABLED: Carrying capacity matters. Exceeding weight limits reduces speed and imposes disadvantage. You\'ll need to track what you carry.\n\nWhen DISABLED: Inventory is loosely tracked. Carry reasonable amounts without precise weight calculations.',

    // Steps
    cowrite: 'Chat with AI to collaboratively develop your universe\'s lore, factions, notable locations, and history. The AI will help you brainstorm and refine ideas while maintaining internal consistency.',
    lore: 'Upload existing documents (stories, world guides, notes) to establish "Hard Canon"—facts the AI will never contradict. Useful for adapting existing settings or maintaining strict continuity with your written lore.'
  };

  readonly step = signal<Step>('basics');
  readonly chatMessages = signal<{ role: 'user' | 'assistant'; content: string }[]>([]);
  readonly uploadedFiles = signal<File[]>([]);
  readonly isGenerating = signal(false);
  readonly isSaving = signal(false);

  // AI Assist state
  readonly worldgenSessionId = signal<string | undefined>(undefined);
  readonly aiAssistStep = signal<WorldgenStepName>('basics');
  private isCreatingSession = false;

  chatInput = '';

  universe: UniverseCreate = {
    name: '', description: '', is_public: false,
    tone: { darkness: 50, humor: 50, realism: 50, magic_level: 50 },
    rules: { permadeath: false, critical_fumbles: false, encumbrance: false, optional_rules: [] }
  };

  ngOnInit(): void {
    if (this.id()) {
      this.universeService.get(this.id()!).subscribe(u => {
        this.universe = { name: u.name, description: u.description, is_public: u.is_public, tone: u.tone, rules: u.rules };
      });
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

  sendChatMessage(): void {
    if (!this.chatInput.trim() || this.isGenerating()) return;
    const msg = this.chatInput;
    this.chatInput = '';
    this.chatMessages.update(m => [...m, { role: 'user', content: msg }]);
    this.isGenerating.set(true);

    // Simulate AI response (would call universeService.generateWithLlm in production)
    setTimeout(() => {
      this.chatMessages.update(m => [...m, {
        role: 'assistant',
        content: `Interesting idea! "${msg}" could work well in your universe. Would you like to expand on this?`
      }]);
      this.isGenerating.set(false);
    }, 1000);
  }

  onFileSelect(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files) {
      this.uploadedFiles.update(f => [...f, ...Array.from(input.files!)]);
    }
  }

  onFileDrop(event: DragEvent): void {
    event.preventDefault();
    if (event.dataTransfer?.files) {
      this.uploadedFiles.update(f => [...f, ...Array.from(event.dataTransfer!.files)]);
    }
  }

  removeFile(file: File): void {
    this.uploadedFiles.update(f => f.filter(x => x !== file));
  }

  saveUniverse(): void {
    this.isSaving.set(true);
    this.universeService.create(this.universe).subscribe({
      next: (u) => this.router.navigate(['/universes', u.id]),
      error: () => this.isSaving.set(false)
    });
  }

  // AI Assist methods
  showAiAssist(step: Step): void {
    // Map builder step to worldgen step name (cowrite/review don't have AI assist in manual mode)
    const stepMap: Partial<Record<Step, WorldgenStepName>> = {
      basics: 'basics',
      tone: 'tone',
      rules: 'rules'
    };

    const worldgenStep = stepMap[step];
    if (!worldgenStep) return;

    this.aiAssistStep.set(worldgenStep);

    // Create a worldgen session if we don't have one
    if (!this.worldgenSessionId() && !this.isCreatingSession) {
      this.isCreatingSession = true;

      // Check LLM status first
      this.worldgenService.checkLlmStatus().subscribe({
        next: status => {
          if (!status.configured) {
            // Redirect to settings if LLM not configured
            this.router.navigate(['/settings'], { queryParams: { setup: 'llm' } });
            this.isCreatingSession = false;
            return;
          }

          // Create a manual mode session
          this.worldgenService.createSession('manual').subscribe({
            next: session => {
              this.worldgenSessionId.set(session.id);
              this.isCreatingSession = false;
              this.aiAssistPopup?.show();
            },
            error: err => {
              console.error('Failed to create worldgen session:', err);
              this.isCreatingSession = false;
            }
          });
        },
        error: err => {
          console.error('Failed to check LLM status:', err);
          this.isCreatingSession = false;
        }
      });
    } else if (this.worldgenSessionId()) {
      this.aiAssistPopup?.show();
    }
  }

  onAiAssistClosed(): void {
    // Popup was closed, nothing special to do
  }

  onAiDataUpdated(): void {
    // AI generated some data - could sync it to the form if desired
    // For now, we just keep the manual form separate
    const session = this.worldgenService.currentSession();
    if (session?.draft_data_json) {
      // Optionally update local universe data from AI suggestions
      const draft = session.draft_data_json;
      if (draft.basics?.name && !this.universe.name) {
        this.universe.name = draft.basics.name;
      }
      if (draft.basics?.description && !this.universe.description) {
        this.universe.description = draft.basics.description;
      }
      // Could also sync tone and rules if desired
    }
  }
}
