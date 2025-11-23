import { Component, inject, input, signal, OnInit, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CampaignService, CharacterService, AuthService } from '@core/services';
import { Campaign, TurnEvent, CharacterSheet, UserSettings } from '@core/models';

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
  imports: [CommonModule, RouterLink, FormsModule],
  template: `
    <div class="play-screen">
      <!-- Sidebar -->
      <aside class="sidebar" [class.sidebar--collapsed]="sidebarCollapsed()">
        <button class="sidebar__toggle" (click)="toggleSidebar()" [attr.aria-expanded]="!sidebarCollapsed()">
          {{ sidebarCollapsed() ? '>' : '<' }}
        </button>

        @if (!sidebarCollapsed()) {
          <div class="sidebar__content">
            <section class="sidebar__section">
              <h3 class="sidebar__title">Campaign</h3>
              <p class="sidebar__text">{{ campaign()?.name || 'Loading...' }}</p>
              <p class="sidebar__meta">Turn {{ campaign()?.turn_count || 0 }}</p>
            </section>

            @if (character()) {
              <section class="sidebar__section">
                <h3 class="sidebar__title">{{ character()?.name }}</h3>
                <p class="sidebar__meta">Level {{ character()?.level }} {{ character()?.class_name }}</p>
                <div class="stats-grid">
                  <div class="stat">
                    <span class="stat__label">HP</span>
                    <span class="stat__value">{{ character()?.hit_points?.current }}/{{ character()?.hit_points?.maximum }}</span>
                  </div>
                  <div class="stat">
                    <span class="stat__label">AC</span>
                    <span class="stat__value">{{ character()?.armor_class }}</span>
                  </div>
                </div>
              </section>
            }

            <section class="sidebar__section">
              <h3 class="sidebar__title">Dice Log</h3>
              <div class="dice-log">
                @for (roll of diceRolls(); track roll.id) {
                  <div class="dice-roll" [class.dice-roll--success]="roll.success === true" [class.dice-roll--fail]="roll.success === false">
                    <span class="dice-roll__type">{{ roll.type }}</span>
                    <span class="dice-roll__result">{{ roll.roll }} + {{ roll.modifier }} = {{ roll.total }}</span>
                  </div>
                }
                @empty {
                  <p class="sidebar__meta">No rolls yet</p>
                }
              </div>
            </section>

            <div class="sidebar__actions">
              <button class="btn btn--sm" (click)="showRewindModal.set(true)">Rewind</button>
              <a routerLink="/campaigns" class="btn btn--sm">Exit</a>
            </div>
          </div>
        }
      </aside>

      <!-- Main chat area -->
      <main class="chat-area" id="main-content">
        <div class="chat-messages" #messagesContainer>
          @for (turn of turns(); track turn.id) {
            <div class="message message--player">
              <div class="message__content">{{ turn.player_input }}</div>
            </div>
            <div class="message message--dm">
              <div class="message__content">{{ turn.dm_narrative }}</div>
            </div>
          }
          @if (isLoading()) {
            <div class="message message--dm message--loading">
              <div class="message__content">The DM is thinking...</div>
            </div>
          }
        </div>

        <!-- Decision menu mode -->
        @if (showDecisionMenu() && currentChoices().length > 0) {
          <div class="decision-menu">
            <h4 class="decision-menu__title">What do you do?</h4>
            @for (choice of currentChoices(); track choice) {
              <button class="decision-menu__choice" (click)="selectChoice(choice)">
                {{ choice }}
              </button>
            }
            <button class="decision-menu__custom" (click)="showDecisionMenu.set(false)">
              Custom action...
            </button>
          </div>
        } @else {
          <form class="chat-input" (ngSubmit)="submitTurn()">
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
              Send
            </button>
          </form>
        }
      </main>

      <!-- Rewind Modal -->
      @if (showRewindModal()) {
        <div class="modal-overlay" (click)="showRewindModal.set(false)">
          <div class="modal" (click)="$event.stopPropagation()">
            <h3 class="modal__title">Rewind Campaign</h3>
            <p class="modal__text">Select a turn to rewind to. All progress after this turn will be lost.</p>

            <div class="rewind-list">
              @for (turn of turns(); track turn.id) {
                <button
                  class="rewind-item"
                  [class.rewind-item--selected]="rewindTarget() === turn.sequence_number"
                  (click)="rewindTarget.set(turn.sequence_number)"
                >
                  Turn {{ turn.sequence_number }}: {{ turn.player_input | slice:0:50 }}...
                </button>
              }
            </div>

            <div class="modal__actions">
              <button class="btn" (click)="showRewindModal.set(false)">Cancel</button>
              <button class="btn btn--danger" (click)="confirmRewind()" [disabled]="rewindTarget() === null">
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
      background-color: var(--wk-background);
    }

    .sidebar {
      width: 280px;
      background-color: var(--wk-surface);
      border-right: 1px solid var(--wk-border);
      display: flex;
      flex-direction: column;
      transition: width 0.2s;
      position: relative;

      &--collapsed {
        width: 40px;
      }
    }

    .sidebar__toggle {
      position: absolute;
      right: -12px;
      top: 50%;
      transform: translateY(-50%);
      width: 24px;
      height: 48px;
      background-color: var(--wk-surface);
      border: 1px solid var(--wk-border);
      border-radius: var(--wk-radius-sm);
      cursor: pointer;
      color: var(--wk-text-secondary);
      z-index: 10;

      &:hover {
        color: var(--wk-text-primary);
      }
    }

    .sidebar__content {
      padding: var(--wk-space-md);
      overflow-y: auto;
      flex: 1;
    }

    .sidebar__section {
      margin-bottom: var(--wk-space-lg);
      padding-bottom: var(--wk-space-md);
      border-bottom: 1px solid var(--wk-border);
    }

    .sidebar__title {
      font-size: 0.875rem;
      font-weight: 600;
      color: var(--wk-text-primary);
      margin: 0 0 var(--wk-space-xs);
    }

    .sidebar__text {
      color: var(--wk-text-primary);
      margin: 0;
    }

    .sidebar__meta {
      font-size: 0.75rem;
      color: var(--wk-text-secondary);
      margin: var(--wk-space-xs) 0 0;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: var(--wk-space-sm);
      margin-top: var(--wk-space-sm);
    }

    .stat {
      background-color: var(--wk-background);
      padding: var(--wk-space-sm);
      border-radius: var(--wk-radius-sm);
      text-align: center;
    }

    .stat__label {
      display: block;
      font-size: 0.625rem;
      color: var(--wk-text-muted);
      text-transform: uppercase;
    }

    .stat__value {
      font-size: 1rem;
      font-weight: 600;
      color: var(--wk-text-primary);
    }

    .dice-log {
      max-height: 150px;
      overflow-y: auto;
    }

    .dice-roll {
      display: flex;
      justify-content: space-between;
      padding: var(--wk-space-xs);
      font-size: 0.75rem;
      border-radius: var(--wk-radius-sm);
      margin-bottom: 2px;

      &--success { background-color: rgba(16, 185, 129, 0.1); }
      &--fail { background-color: rgba(239, 68, 68, 0.1); }
    }

    .dice-roll__type { color: var(--wk-text-secondary); }
    .dice-roll__result { color: var(--wk-text-primary); font-weight: 500; }

    .sidebar__actions {
      display: flex;
      gap: var(--wk-space-sm);
      padding-top: var(--wk-space-md);
    }

    .chat-area {
      flex: 1;
      display: flex;
      flex-direction: column;
    }

    .chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: var(--wk-space-lg);
    }

    .message {
      max-width: 80%;
      margin-bottom: var(--wk-space-md);

      &--player {
        margin-left: auto;
      }

      &--dm {
        margin-right: auto;
      }

      &--loading .message__content {
        opacity: 0.6;
        font-style: italic;
      }
    }

    .message__content {
      padding: var(--wk-space-md);
      border-radius: var(--wk-radius-lg);
      line-height: 1.6;
      white-space: pre-wrap;
    }

    .message--player .message__content {
      background-color: var(--wk-primary);
      color: var(--wk-text-primary);
    }

    .message--dm .message__content {
      background-color: var(--wk-surface);
      color: var(--wk-text-primary);
    }

    .decision-menu {
      padding: var(--wk-space-lg);
      background-color: var(--wk-surface);
      border-top: 1px solid var(--wk-border);
    }

    .decision-menu__title {
      font-size: 0.875rem;
      color: var(--wk-text-secondary);
      margin: 0 0 var(--wk-space-md);
    }

    .decision-menu__choice {
      display: block;
      width: 100%;
      padding: var(--wk-space-sm) var(--wk-space-md);
      margin-bottom: var(--wk-space-xs);
      background-color: var(--wk-background);
      border: 1px solid var(--wk-border);
      border-radius: var(--wk-radius-md);
      color: var(--wk-text-primary);
      text-align: left;
      cursor: pointer;

      &:hover {
        border-color: var(--wk-primary);
      }
    }

    .decision-menu__custom {
      display: block;
      width: 100%;
      padding: var(--wk-space-xs);
      background: none;
      border: none;
      color: var(--wk-primary);
      cursor: pointer;
      font-size: 0.875rem;
    }

    .chat-input {
      display: flex;
      padding: var(--wk-space-md);
      gap: var(--wk-space-sm);
      background-color: var(--wk-surface);
      border-top: 1px solid var(--wk-border);
    }

    .chat-input__field {
      flex: 1;
      padding: var(--wk-space-sm) var(--wk-space-md);
      background-color: var(--wk-background);
      border: 1px solid var(--wk-border);
      border-radius: var(--wk-radius-md);
      color: var(--wk-text-primary);
      font-size: 1rem;

      &:focus {
        outline: none;
        border-color: var(--wk-primary);
      }
    }

    .chat-input__submit {
      padding: var(--wk-space-sm) var(--wk-space-lg);
      background-color: var(--wk-primary);
      border: none;
      border-radius: var(--wk-radius-md);
      color: var(--wk-text-primary);
      font-weight: 500;
      cursor: pointer;

      &:hover:not(:disabled) {
        background-color: var(--wk-primary-dark);
      }

      &:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
    }

    .btn {
      padding: var(--wk-space-xs) var(--wk-space-md);
      border-radius: var(--wk-radius-md);
      border: 1px solid var(--wk-border);
      background: none;
      color: var(--wk-text-primary);
      cursor: pointer;
      text-decoration: none;
      font-size: 0.875rem;

      &:hover { background-color: var(--wk-surface-elevated); }
      &--sm { padding: var(--wk-space-xs) var(--wk-space-sm); font-size: 0.75rem; }
      &--danger { border-color: var(--wk-error); color: var(--wk-error); }
    }

    .modal-overlay {
      position: fixed;
      inset: 0;
      background-color: rgba(0, 0, 0, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 100;
    }

    .modal {
      background-color: var(--wk-surface);
      border-radius: var(--wk-radius-lg);
      padding: var(--wk-space-xl);
      max-width: 500px;
      width: 90%;
      max-height: 80vh;
      overflow-y: auto;
    }

    .modal__title {
      font-size: 1.25rem;
      margin: 0 0 var(--wk-space-sm);
    }

    .modal__text {
      color: var(--wk-text-secondary);
      margin: 0 0 var(--wk-space-lg);
    }

    .modal__actions {
      display: flex;
      gap: var(--wk-space-sm);
      justify-content: flex-end;
      margin-top: var(--wk-space-lg);
    }

    .rewind-list {
      max-height: 200px;
      overflow-y: auto;
    }

    .rewind-item {
      display: block;
      width: 100%;
      padding: var(--wk-space-sm);
      margin-bottom: var(--wk-space-xs);
      background: none;
      border: 1px solid var(--wk-border);
      border-radius: var(--wk-radius-md);
      text-align: left;
      color: var(--wk-text-primary);
      cursor: pointer;

      &:hover { border-color: var(--wk-primary); }
      &--selected { border-color: var(--wk-primary); background-color: rgba(99, 102, 241, 0.1); }
    }
  `]
})
export class PlayComponent implements OnInit {
  @ViewChild('messagesContainer') messagesContainer!: ElementRef;

  private readonly campaignService = inject(CampaignService);
  private readonly characterService = inject(CharacterService);
  private readonly authService = inject(AuthService);

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
