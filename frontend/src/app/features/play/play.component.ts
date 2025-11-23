import { Component, inject, input, signal, OnInit, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CampaignService, CharacterService, AuthService } from '@core/services';
import { Campaign, TurnEvent, CharacterSheet, UserSettings } from '@core/models';
import {
  LucideAngularModule,
  Swords,
  User,
  Heart,
  Shield,
  Dices,
  ChevronLeft,
  ChevronRight,
  History,
  LogOut,
  Send,
  Loader2,
  Sparkles,
  MessageSquare,
  X,
  RotateCcw
} from 'lucide-angular';

interface DiceRoll {
  id: string;
  type: string;
  roll: number;
  modifier: number;
  total: number;
  success: boolean | null;
  timestamp: Date;
}

@Component({
  selector: 'app-play',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule, LucideAngularModule],
  template: `
    <div class="play-screen">
      <!-- Animated background -->
      <div class="play-bg">
        <div class="play-bg__orb play-bg__orb--1"></div>
        <div class="play-bg__orb play-bg__orb--2"></div>
      </div>

      <!-- Sidebar -->
      <aside class="sidebar" [class.sidebar--collapsed]="sidebarCollapsed()">
        <button
          class="sidebar__toggle"
          (click)="toggleSidebar()"
          [attr.aria-expanded]="!sidebarCollapsed()"
          [attr.aria-label]="sidebarCollapsed() ? 'Expand sidebar' : 'Collapse sidebar'"
        >
          <lucide-icon [img]="sidebarCollapsed() ? ChevronRightIcon : ChevronLeftIcon" />
        </button>

        @if (!sidebarCollapsed()) {
          <div class="sidebar__content animate-fade-in">
            <section class="sidebar__section">
              <div class="sidebar__section-header">
                <lucide-icon [img]="SwordsIcon" />
                <h3 class="sidebar__title">Campaign</h3>
              </div>
              <p class="sidebar__text">{{ campaign()?.name || 'Loading...' }}</p>
              <p class="sidebar__meta">Turn {{ campaign()?.turn_count || 0 }}</p>
            </section>

            @if (character()) {
              <section class="sidebar__section">
                <div class="sidebar__section-header">
                  <lucide-icon [img]="UserIcon" />
                  <h3 class="sidebar__title">{{ character()?.name }}</h3>
                </div>
                <p class="sidebar__meta">Level {{ character()?.level }} {{ character()?.class_name }}</p>
                <div class="stats-grid">
                  <div class="stat stat--hp">
                    <lucide-icon [img]="HeartIcon" class="stat__icon" />
                    <span class="stat__label">HP</span>
                    <span class="stat__value">{{ character()?.hit_points?.current }}/{{ character()?.hit_points?.maximum }}</span>
                  </div>
                  <div class="stat stat--ac">
                    <lucide-icon [img]="ShieldIcon" class="stat__icon" />
                    <span class="stat__label">AC</span>
                    <span class="stat__value">{{ character()?.armor_class }}</span>
                  </div>
                </div>
              </section>
            }

            <section class="sidebar__section sidebar__section--dice">
              <div class="sidebar__section-header">
                <lucide-icon [img]="DicesIcon" />
                <h3 class="sidebar__title">Dice Log</h3>
              </div>
              <div class="dice-log">
                @for (roll of diceRolls(); track roll.id) {
                  <div class="dice-roll" [class.dice-roll--success]="roll.success === true" [class.dice-roll--fail]="roll.success === false">
                    <span class="dice-roll__type">{{ roll.type }}</span>
                    <span class="dice-roll__result">{{ roll.roll }} + {{ roll.modifier }} = {{ roll.total }}</span>
                  </div>
                }
                @empty {
                  <p class="sidebar__meta sidebar__meta--empty">No rolls yet</p>
                }
              </div>
            </section>

            <div class="sidebar__actions">
              <button class="btn btn--ghost btn--sm" (click)="showRewindModal.set(true)">
                <lucide-icon [img]="HistoryIcon" />
                Rewind
              </button>
              <a routerLink="/campaigns" class="btn btn--ghost btn--sm">
                <lucide-icon [img]="LogOutIcon" />
                Exit
              </a>
            </div>
          </div>
        }
      </aside>

      <!-- Main chat area -->
      <main class="chat-area" id="main-content">
        <div class="chat-messages" #messagesContainer>
          @for (turn of turns(); track turn.id) {
            <div class="message message--player animate-fade-in-up">
              <div class="message__bubble">
                <div class="message__avatar message__avatar--player">
                  <lucide-icon [img]="UserIcon" />
                </div>
                <div class="message__content">{{ turn.player_input }}</div>
              </div>
            </div>
            <div class="message message--dm animate-fade-in-up">
              <div class="message__bubble">
                <div class="message__avatar message__avatar--dm">
                  <lucide-icon [img]="SparklesIcon" />
                </div>
                <div class="message__content">{{ turn.dm_narrative }}</div>
              </div>
            </div>
          }
          @if (isLoading()) {
            <div class="message message--dm message--loading animate-fade-in">
              <div class="message__bubble">
                <div class="message__avatar message__avatar--dm">
                  <lucide-icon [img]="SparklesIcon" />
                </div>
                <div class="message__content">
                  <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            </div>
          }
        </div>

        <!-- Decision menu mode -->
        @if (showDecisionMenu() && currentChoices().length > 0) {
          <div class="decision-menu animate-fade-in-up">
            <div class="decision-menu__header">
              <lucide-icon [img]="MessageSquareIcon" />
              <h4 class="decision-menu__title">What do you do?</h4>
            </div>
            <div class="decision-menu__choices">
              @for (choice of currentChoices(); track choice) {
                <button class="decision-menu__choice" (click)="selectChoice(choice)">
                  <lucide-icon [img]="ChevronRightIcon" />
                  {{ choice }}
                </button>
              }
            </div>
            <button class="decision-menu__custom" (click)="showDecisionMenu.set(false)">
              <lucide-icon [img]="MessageSquareIcon" />
              Custom action...
            </button>
          </div>
        } @else {
          <form class="chat-input animate-fade-in-up" (ngSubmit)="submitTurn()">
            <input
              type="text"
              [(ngModel)]="playerInput"
              name="playerInput"
              class="chat-input__field"
              placeholder="What do you do?"
              [disabled]="isLoading()"
              autocomplete="off"
            />
            <button type="submit" class="chat-input__submit" [disabled]="isLoading() || !playerInput.trim()">
              @if (isLoading()) {
                <lucide-icon [img]="Loader2Icon" class="animate-spin" />
              } @else {
                <lucide-icon [img]="SendIcon" />
              }
            </button>
          </form>
        }
      </main>

      <!-- Rewind Modal -->
      @if (showRewindModal()) {
        <div class="modal-overlay animate-fade-in" (click)="showRewindModal.set(false)">
          <div class="modal animate-scale-in" (click)="$event.stopPropagation()">
            <button class="modal__close" (click)="showRewindModal.set(false)" aria-label="Close modal">
              <lucide-icon [img]="XIcon" />
            </button>

            <div class="modal__header">
              <div class="modal__icon">
                <lucide-icon [img]="RotateCcwIcon" />
              </div>
              <h3 class="modal__title">Rewind Campaign</h3>
            </div>

            <p class="modal__text">Select a turn to rewind to. All progress after this turn will be lost.</p>

            <div class="rewind-list">
              @for (turn of turns(); track turn.id) {
                <button
                  class="rewind-item"
                  [class.rewind-item--selected]="rewindTarget() === turn.sequence_number"
                  (click)="rewindTarget.set(turn.sequence_number)"
                >
                  <span class="rewind-item__turn">Turn {{ turn.sequence_number }}</span>
                  <span class="rewind-item__text">{{ turn.player_input | slice:0:40 }}...</span>
                </button>
              }
            </div>

            <div class="modal__actions">
              <button class="btn btn--ghost" (click)="showRewindModal.set(false)">Cancel</button>
              <button class="btn btn--danger" (click)="confirmRewind()" [disabled]="rewindTarget() === null">
                <lucide-icon [img]="RotateCcwIcon" />
                Rewind
              </button>
            </div>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .play-screen {
      display: flex;
      height: 100vh;
      position: relative;
      overflow: hidden;
    }

    /* Animated background */
    .play-bg {
      position: absolute;
      inset: 0;
      pointer-events: none;
      overflow: hidden;
    }

    .play-bg__orb {
      position: absolute;
      border-radius: 50%;
      filter: blur(100px);
      opacity: 0.15;
      animation: float 30s ease-in-out infinite;
    }

    .play-bg__orb--1 {
      width: 500px;
      height: 500px;
      background: var(--wk-primary);
      top: -200px;
      right: -100px;
    }

    .play-bg__orb--2 {
      width: 400px;
      height: 400px;
      background: var(--wk-secondary);
      bottom: -150px;
      left: 20%;
      animation-delay: -10s;
    }

    @keyframes float {
      0%, 100% { transform: translate(0, 0) scale(1); }
      25% { transform: translate(20px, -30px) scale(1.03); }
      50% { transform: translate(-15px, 20px) scale(0.97); }
      75% { transform: translate(-25px, -15px) scale(1.01); }
    }

    /* Sidebar */
    .sidebar {
      width: 280px;
      background: var(--wk-glass-bg);
      backdrop-filter: blur(var(--wk-blur-lg));
      -webkit-backdrop-filter: blur(var(--wk-blur-lg));
      border-right: 1px solid var(--wk-glass-border);
      display: flex;
      flex-direction: column;
      transition: width var(--wk-transition-smooth);
      position: relative;
      z-index: 10;

      &--collapsed {
        width: 48px;
      }
    }

    .sidebar__toggle {
      position: absolute;
      right: -14px;
      top: 50%;
      transform: translateY(-50%);
      width: 28px;
      height: 56px;
      background: var(--wk-glass-bg);
      backdrop-filter: blur(var(--wk-blur-sm));
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-md);
      cursor: pointer;
      color: var(--wk-text-secondary);
      z-index: 10;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all var(--wk-transition-fast);

      lucide-icon {
        width: 16px;
        height: 16px;
      }

      &:hover {
        color: var(--wk-primary);
        border-color: var(--wk-primary);
        box-shadow: 0 0 15px var(--wk-primary-glow);
      }
    }

    .sidebar__content {
      padding: var(--wk-space-4);
      overflow-y: auto;
      flex: 1;
    }

    .sidebar__section {
      margin-bottom: var(--wk-space-4);
      padding-bottom: var(--wk-space-4);
      border-bottom: 1px solid var(--wk-glass-border);

      &--dice {
        flex: 1;
        display: flex;
        flex-direction: column;
        min-height: 0;
      }
    }

    .sidebar__section-header {
      display: flex;
      align-items: center;
      gap: var(--wk-space-2);
      margin-bottom: var(--wk-space-2);

      lucide-icon {
        width: 16px;
        height: 16px;
        color: var(--wk-primary);
      }
    }

    .sidebar__title {
      font-size: var(--wk-text-sm);
      font-weight: var(--wk-font-semibold);
      color: var(--wk-text-primary);
      margin: 0;
    }

    .sidebar__text {
      color: var(--wk-text-primary);
      margin: 0;
      font-size: var(--wk-text-sm);
    }

    .sidebar__meta {
      font-size: var(--wk-text-xs);
      color: var(--wk-text-secondary);
      margin: var(--wk-space-1) 0 0;

      &--empty {
        text-align: center;
        padding: var(--wk-space-4);
        opacity: 0.6;
      }
    }

    /* Stats Grid */
    .stats-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: var(--wk-space-2);
      margin-top: var(--wk-space-3);
    }

    .stat {
      background: var(--wk-surface-elevated);
      border: 1px solid var(--wk-glass-border);
      padding: var(--wk-space-3);
      border-radius: var(--wk-radius-lg);
      text-align: center;
      transition: all var(--wk-transition-fast);

      &:hover {
        border-color: var(--wk-glass-border-hover);
      }

      &--hp {
        .stat__icon { color: var(--wk-error); }
        &:hover { box-shadow: 0 0 15px var(--wk-error-glow); }
      }

      &--ac {
        .stat__icon { color: var(--wk-info); }
        &:hover { box-shadow: 0 0 15px var(--wk-info-glow); }
      }
    }

    .stat__icon {
      width: 16px;
      height: 16px;
      margin-bottom: var(--wk-space-1);
    }

    .stat__label {
      display: block;
      font-size: var(--wk-text-xs);
      color: var(--wk-text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .stat__value {
      font-size: var(--wk-text-lg);
      font-weight: var(--wk-font-bold);
      color: var(--wk-text-primary);
    }

    /* Dice Log */
    .dice-log {
      flex: 1;
      overflow-y: auto;
      min-height: 100px;
      max-height: 180px;
    }

    .dice-roll {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: var(--wk-space-2) var(--wk-space-3);
      font-size: var(--wk-text-xs);
      border-radius: var(--wk-radius-md);
      margin-bottom: var(--wk-space-1);
      background: var(--wk-surface-elevated);
      border: 1px solid transparent;
      transition: all var(--wk-transition-fast);

      &--success {
        background: var(--wk-success-glow);
        border-color: rgba(16, 185, 129, 0.3);
      }

      &--fail {
        background: var(--wk-error-glow);
        border-color: rgba(239, 68, 68, 0.3);
      }
    }

    .dice-roll__type {
      color: var(--wk-text-secondary);
      font-weight: var(--wk-font-medium);
    }

    .dice-roll__result {
      color: var(--wk-text-primary);
      font-weight: var(--wk-font-semibold);
      font-family: var(--wk-font-mono);
    }

    /* Sidebar Actions */
    .sidebar__actions {
      display: flex;
      gap: var(--wk-space-2);
      padding-top: var(--wk-space-4);
      border-top: 1px solid var(--wk-glass-border);
    }

    /* Chat Area */
    .chat-area {
      flex: 1;
      display: flex;
      flex-direction: column;
      position: relative;
      z-index: 1;
    }

    .chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: var(--wk-space-6);
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-4);
    }

    /* Messages */
    .message {
      max-width: 75%;
      animation-duration: 0.4s;

      &--player {
        align-self: flex-end;
      }

      &--dm {
        align-self: flex-start;
      }
    }

    .message__bubble {
      display: flex;
      gap: var(--wk-space-3);
      align-items: flex-start;
    }

    .message--player .message__bubble {
      flex-direction: row-reverse;
    }

    .message__avatar {
      width: 36px;
      height: 36px;
      border-radius: var(--wk-radius-full);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;

      lucide-icon {
        width: 18px;
        height: 18px;
      }

      &--player {
        background: linear-gradient(135deg, var(--wk-primary) 0%, var(--wk-primary-dark) 100%);
        box-shadow: 0 0 15px var(--wk-primary-glow);
        color: white;
      }

      &--dm {
        background: linear-gradient(135deg, var(--wk-secondary) 0%, var(--wk-accent) 100%);
        box-shadow: 0 0 15px var(--wk-secondary-glow);
        color: white;
      }
    }

    .message__content {
      padding: var(--wk-space-4);
      border-radius: var(--wk-radius-xl);
      line-height: var(--wk-leading-relaxed);
      white-space: pre-wrap;
      font-size: var(--wk-text-sm);
    }

    .message--player .message__content {
      background: linear-gradient(135deg, var(--wk-primary) 0%, var(--wk-primary-dark) 100%);
      color: white;
      border-bottom-right-radius: var(--wk-radius-sm);
      box-shadow: 0 4px 20px var(--wk-primary-glow);
    }

    .message--dm .message__content {
      background: var(--wk-glass-bg);
      backdrop-filter: blur(var(--wk-blur-md));
      border: 1px solid var(--wk-glass-border);
      color: var(--wk-text-primary);
      border-bottom-left-radius: var(--wk-radius-sm);
    }

    /* Typing Indicator */
    .typing-indicator {
      display: flex;
      gap: 4px;
      padding: var(--wk-space-2) 0;

      span {
        width: 8px;
        height: 8px;
        background: var(--wk-text-muted);
        border-radius: 50%;
        animation: typing 1.4s ease-in-out infinite;

        &:nth-child(2) { animation-delay: 0.2s; }
        &:nth-child(3) { animation-delay: 0.4s; }
      }
    }

    @keyframes typing {
      0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
      30% { transform: translateY(-4px); opacity: 1; }
    }

    /* Decision Menu */
    .decision-menu {
      padding: var(--wk-space-6);
      background: var(--wk-glass-bg);
      backdrop-filter: blur(var(--wk-blur-lg));
      border-top: 1px solid var(--wk-glass-border);
    }

    .decision-menu__header {
      display: flex;
      align-items: center;
      gap: var(--wk-space-2);
      margin-bottom: var(--wk-space-4);

      lucide-icon {
        width: 18px;
        height: 18px;
        color: var(--wk-primary);
      }
    }

    .decision-menu__title {
      font-size: var(--wk-text-sm);
      font-weight: var(--wk-font-semibold);
      color: var(--wk-text-primary);
      margin: 0;
    }

    .decision-menu__choices {
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-2);
    }

    .decision-menu__choice {
      display: flex;
      align-items: center;
      gap: var(--wk-space-3);
      width: 100%;
      padding: var(--wk-space-3) var(--wk-space-4);
      background: var(--wk-surface-elevated);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-lg);
      color: var(--wk-text-primary);
      text-align: left;
      cursor: pointer;
      font-size: var(--wk-text-sm);
      transition: all var(--wk-transition-fast);

      lucide-icon {
        width: 16px;
        height: 16px;
        color: var(--wk-text-muted);
        transition: all var(--wk-transition-fast);
      }

      &:hover {
        border-color: var(--wk-primary);
        background: var(--wk-primary-glow);
        transform: translateX(4px);

        lucide-icon {
          color: var(--wk-primary);
        }
      }
    }

    .decision-menu__custom {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: var(--wk-space-2);
      width: 100%;
      padding: var(--wk-space-3);
      margin-top: var(--wk-space-3);
      background: none;
      border: 1px dashed var(--wk-glass-border);
      border-radius: var(--wk-radius-lg);
      color: var(--wk-text-secondary);
      cursor: pointer;
      font-size: var(--wk-text-sm);
      transition: all var(--wk-transition-fast);

      lucide-icon {
        width: 16px;
        height: 16px;
      }

      &:hover {
        color: var(--wk-primary);
        border-color: var(--wk-primary);
      }
    }

    /* Chat Input */
    .chat-input {
      display: flex;
      padding: var(--wk-space-4);
      gap: var(--wk-space-3);
      background: var(--wk-glass-bg);
      backdrop-filter: blur(var(--wk-blur-lg));
      border-top: 1px solid var(--wk-glass-border);
    }

    .chat-input__field {
      flex: 1;
      padding: var(--wk-space-3) var(--wk-space-4);
      background: var(--wk-surface-elevated);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-xl);
      color: var(--wk-text-primary);
      font-size: var(--wk-text-sm);
      transition: all var(--wk-transition-fast);

      &::placeholder {
        color: var(--wk-text-muted);
      }

      &:focus {
        outline: none;
        border-color: var(--wk-primary);
        box-shadow: 0 0 0 3px var(--wk-primary-glow);
      }

      &:disabled {
        opacity: 0.6;
      }
    }

    .chat-input__submit {
      width: 48px;
      height: 48px;
      background: linear-gradient(135deg, var(--wk-primary) 0%, var(--wk-primary-dark) 100%);
      border: none;
      border-radius: var(--wk-radius-full);
      color: white;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all var(--wk-transition-fast);
      box-shadow: 0 0 20px var(--wk-primary-glow);

      lucide-icon {
        width: 20px;
        height: 20px;
      }

      &:hover:not(:disabled) {
        transform: scale(1.05);
        box-shadow: 0 0 30px var(--wk-primary-glow);
      }

      &:disabled {
        opacity: 0.5;
        cursor: not-allowed;
        box-shadow: none;
      }
    }

    /* Buttons */
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: var(--wk-space-2);
      padding: var(--wk-space-2) var(--wk-space-4);
      border-radius: var(--wk-radius-lg);
      font-size: var(--wk-text-sm);
      font-weight: var(--wk-font-medium);
      cursor: pointer;
      text-decoration: none;
      transition: all var(--wk-transition-fast);

      lucide-icon {
        width: 16px;
        height: 16px;
      }

      &--ghost {
        background: transparent;
        border: 1px solid var(--wk-glass-border);
        color: var(--wk-text-secondary);

        &:hover {
          background: var(--wk-surface-elevated);
          color: var(--wk-text-primary);
          border-color: var(--wk-glass-border-hover);
        }
      }

      &--danger {
        background: var(--wk-error-glow);
        border: 1px solid var(--wk-error);
        color: var(--wk-error);

        &:hover {
          background: var(--wk-error);
          color: white;
          box-shadow: 0 0 20px var(--wk-error-glow);
        }

        &:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      }

      &--sm {
        padding: var(--wk-space-2) var(--wk-space-3);
        font-size: var(--wk-text-xs);

        lucide-icon {
          width: 14px;
          height: 14px;
        }
      }
    }

    /* Modal */
    .modal-overlay {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.6);
      backdrop-filter: blur(4px);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 100;
      padding: var(--wk-space-4);
    }

    .modal {
      background: var(--wk-glass-bg);
      backdrop-filter: blur(var(--wk-blur-xl));
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-2xl);
      padding: var(--wk-space-8);
      max-width: 480px;
      width: 100%;
      max-height: 80vh;
      overflow-y: auto;
      position: relative;

      /* Glass shine */
      &::before {
        content: '';
        position: absolute;
        inset: 0;
        background: var(--wk-glass-shine);
        border-radius: inherit;
        pointer-events: none;
      }
    }

    .modal__close {
      position: absolute;
      top: var(--wk-space-4);
      right: var(--wk-space-4);
      width: 32px;
      height: 32px;
      background: var(--wk-surface-elevated);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-full);
      color: var(--wk-text-secondary);
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
        color: var(--wk-text-primary);
        border-color: var(--wk-glass-border-hover);
      }
    }

    .modal__header {
      display: flex;
      align-items: center;
      gap: var(--wk-space-3);
      margin-bottom: var(--wk-space-4);
    }

    .modal__icon {
      width: 48px;
      height: 48px;
      background: var(--wk-warning-glow);
      border-radius: var(--wk-radius-xl);
      display: flex;
      align-items: center;
      justify-content: center;

      lucide-icon {
        width: 24px;
        height: 24px;
        color: var(--wk-warning);
      }
    }

    .modal__title {
      font-size: var(--wk-text-xl);
      font-weight: var(--wk-font-semibold);
      color: var(--wk-text-primary);
      margin: 0;
    }

    .modal__text {
      color: var(--wk-text-secondary);
      margin: 0 0 var(--wk-space-6);
      line-height: var(--wk-leading-relaxed);
    }

    .modal__actions {
      display: flex;
      gap: var(--wk-space-3);
      justify-content: flex-end;
      margin-top: var(--wk-space-6);
    }

    /* Rewind List */
    .rewind-list {
      max-height: 240px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-2);
    }

    .rewind-item {
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-1);
      width: 100%;
      padding: var(--wk-space-3) var(--wk-space-4);
      background: var(--wk-surface-elevated);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-lg);
      text-align: left;
      cursor: pointer;
      transition: all var(--wk-transition-fast);

      &:hover {
        border-color: var(--wk-primary);
        transform: translateX(4px);
      }

      &--selected {
        border-color: var(--wk-primary);
        background: var(--wk-primary-glow);
        box-shadow: 0 0 15px var(--wk-primary-glow);
      }
    }

    .rewind-item__turn {
      font-size: var(--wk-text-xs);
      font-weight: var(--wk-font-semibold);
      color: var(--wk-primary);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .rewind-item__text {
      font-size: var(--wk-text-sm);
      color: var(--wk-text-secondary);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    /* Animations */
    .animate-fade-in {
      animation: fadeIn 0.3s ease-out forwards;
    }

    .animate-fade-in-up {
      animation: fadeInUp 0.4s ease-out forwards;
    }

    .animate-scale-in {
      animation: scaleIn 0.3s ease-out forwards;
    }

    .animate-spin {
      animation: spin 1s linear infinite;
    }

    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    @keyframes fadeInUp {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    @keyframes scaleIn {
      from { opacity: 0; transform: scale(0.95); }
      to { opacity: 1; transform: scale(1); }
    }

    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
  `]
})
export class PlayComponent implements OnInit {
  @ViewChild('messagesContainer') messagesContainer!: ElementRef;

  private readonly campaignService = inject(CampaignService);
  private readonly characterService = inject(CharacterService);
  private readonly authService = inject(AuthService);

  // Lucide icons
  readonly SwordsIcon = Swords;
  readonly UserIcon = User;
  readonly HeartIcon = Heart;
  readonly ShieldIcon = Shield;
  readonly DicesIcon = Dices;
  readonly ChevronLeftIcon = ChevronLeft;
  readonly ChevronRightIcon = ChevronRight;
  readonly HistoryIcon = History;
  readonly LogOutIcon = LogOut;
  readonly SendIcon = Send;
  readonly Loader2Icon = Loader2;
  readonly SparklesIcon = Sparkles;
  readonly MessageSquareIcon = MessageSquare;
  readonly XIcon = X;
  readonly RotateCcwIcon = RotateCcw;

  campaignId = input.required<string>();

  readonly campaign = signal<Campaign | null>(null);
  readonly character = signal<CharacterSheet | null>(null);
  readonly turns = signal<TurnEvent[]>([]);
  readonly diceRolls = signal<DiceRoll[]>([]);
  readonly isLoading = signal(false);
  readonly sidebarCollapsed = signal(false);
  readonly showDecisionMenu = signal(false);
  readonly currentChoices = signal<string[]>([]);
  readonly showRewindModal = signal(false);
  readonly rewindTarget = signal<number | null>(null);

  playerInput = '';

  ngOnInit(): void {
    this.loadCampaign();
  }

  private loadCampaign(): void {
    this.campaignService.get(this.campaignId()).subscribe({
      next: (campaign) => {
        this.campaign.set(campaign);
        this.loadTurns();
        if (campaign.character) {
          this.loadCharacter(campaign.character);
        }
      }
    });
  }

  private loadCharacter(characterId: string): void {
    this.characterService.get(characterId).subscribe({
      next: (character) => this.character.set(character)
    });
  }

  private loadTurns(): void {
    this.campaignService.listTurns(this.campaignId(), { ordering: 'sequence_number' }).subscribe({
      next: (response) => {
        this.turns.set(response.results);
        this.scrollToBottom();
      }
    });
  }

  toggleSidebar(): void {
    this.sidebarCollapsed.set(!this.sidebarCollapsed());
  }

  submitTurn(): void {
    if (!this.playerInput.trim() || this.isLoading()) return;

    this.isLoading.set(true);
    const input = this.playerInput;
    this.playerInput = '';

    this.campaignService.submitTurn(this.campaignId(), { player_input: input }).subscribe({
      next: (response) => {
        this.turns.update(turns => [...turns, response.turn]);
        this.processRolls(response.turn);
        this.isLoading.set(false);
        this.scrollToBottom();
      },
      error: () => {
        this.isLoading.set(false);
        this.playerInput = input;
      }
    });
  }

  selectChoice(choice: string): void {
    this.playerInput = choice;
    this.showDecisionMenu.set(false);
    this.submitTurn();
  }

  private processRolls(turn: TurnEvent): void {
    if (turn.dm_json?.roll_requests) {
      const newRolls: DiceRoll[] = turn.dm_json.roll_requests.map((req, i) => ({
        id: `${turn.id}-${i}`,
        type: req.type,
        roll: Math.floor(Math.random() * 20) + 1,
        modifier: 0,
        total: 0,
        success: null,
        timestamp: new Date()
      }));
      this.diceRolls.update(rolls => [...newRolls, ...rolls].slice(0, 20));
    }
  }

  confirmRewind(): void {
    const target = this.rewindTarget();
    if (target === null) return;

    this.campaignService.rewind(this.campaignId(), target).subscribe({
      next: () => {
        this.showRewindModal.set(false);
        this.rewindTarget.set(null);
        this.loadTurns();
        this.loadCampaign();
      }
    });
  }

  private scrollToBottom(): void {
    setTimeout(() => {
      if (this.messagesContainer) {
        this.messagesContainer.nativeElement.scrollTop = this.messagesContainer.nativeElement.scrollHeight;
      }
    }, 100);
  }
}
