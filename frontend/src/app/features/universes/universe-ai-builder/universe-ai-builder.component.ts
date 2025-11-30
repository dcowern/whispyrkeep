import { Component, inject, signal, computed, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { WorldgenService, WORLDGEN_STEPS } from '@core/services/worldgen.service';
import { WorldgenStepName } from '@core/models';
import {
  LucideAngularModule,
  ArrowLeft,
  Sparkles,
  Send,
  Loader2,
  Check,
  Circle,
  Bot,
  User,
  PenTool,
  ChevronDown
} from 'lucide-angular';

@Component({
  selector: 'app-universe-ai-builder',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule, LucideAngularModule],
  template: `
    <div class="builder">
      <div class="builder__bg">
        <div class="builder__orb builder__orb--1"></div>
        <div class="builder__orb builder__orb--2"></div>
      </div>

      <!-- Header -->
      <header class="builder__header">
        <a routerLink="/universes/new" class="back-link">
          <lucide-icon [img]="ArrowLeftIcon" />
          Back
        </a>
        <div class="builder__title">
          <div class="builder__title-icon">
            <lucide-icon [img]="modeIcon" />
          </div>
          <div>
            <h1>{{ universeName() || 'New Universe' }}</h1>
            <span class="builder__mode-badge" [class.builder__mode-badge--ai]="mode() === 'ai_collab'">
              {{ mode() === 'ai_collab' ? 'With Whispyr' : 'Manual' }}
            </span>
          </div>
        </div>
        <div class="builder__actions">
          <button class="btn btn--ghost btn--sm" (click)="switchMode()" [disabled]="isStreaming()">
            <lucide-icon [img]="mode() === 'ai_collab' ? PenToolIcon : BotIcon" />
            Switch to {{ mode() === 'ai_collab' ? 'Manual' : 'Whispyr' }}
          </button>
          <button
            class="btn btn--primary btn--sm"
            (click)="finalize()"
            [disabled]="!canFinalize() || isStreaming()"
          >
            <lucide-icon [img]="CheckIcon" />
            Create Universe
          </button>
        </div>
      </header>

      <div class="builder__body">
        <!-- Sidebar with step checklist -->
        <aside class="sidebar">
          <h3 class="sidebar__title">Progress</h3>
          <ul class="step-list">
            @for (step of steps; track step.name) {
              <li
                class="step-item"
                [class.step-item--active]="currentStep() === step.name"
                [class.step-item--complete]="isStepComplete(step.name)"
                [class.step-item--required]="step.required"
              >
                <div class="step-item__icon">
                  @if (isStepComplete(step.name)) {
                    <lucide-icon [img]="CheckIcon" />
                  } @else {
                    <lucide-icon [img]="CircleIcon" />
                  }
                </div>
                <div class="step-item__content">
                  <span class="step-item__name">{{ step.displayName }}</span>
                  <span class="step-item__desc">{{ step.description }}</span>
                </div>
                @if (step.required) {
                  <span class="step-item__required">Required</span>
                }
              </li>
            }
          </ul>
        </aside>

        <!-- Chat area -->
        <main class="chat-area">
          @if (errorMessage()) {
            <div class="chat-error">
              {{ errorMessage() }}
            </div>
          }

          <div class="chat-messages" #chatContainer (scroll)="onScroll()">
            @for (msg of messages(); track $index) {
              <div class="message" [class.message--user]="msg.role === 'user'" [class.message--assistant]="msg.role === 'assistant'">
                <div class="message__avatar">
                  <lucide-icon [img]="msg.role === 'user' ? UserIcon : SparklesIcon" />
                </div>
                <div class="message__content">
                  <span class="message__role">{{ msg.role === 'user' ? 'You' : 'Whispyr' }}</span>
                  @if (msg.role === 'assistant') {
                    <div class="message__text" [innerHTML]="renderMarkdownSafe(msg.content)"></div>
                  } @else {
                    <div class="message__text">{{ msg.content }}</div>
                  }
                </div>
              </div>
            }

            @if (pendingUserMessage()) {
              <div class="message message--user">
                <div class="message__avatar">
                  <lucide-icon [img]="UserIcon" />
                </div>
                <div class="message__content">
                  <span class="message__role">You</span>
                  <div class="message__text">{{ pendingUserMessage() }}</div>
                </div>
              </div>
            }

            @if (isStreaming()) {
              <div class="message message--assistant">
                <div class="message__avatar">
                  <lucide-icon [img]="SparklesIcon" />
                </div>
                <div class="message__content">
                  <span class="message__role">Whispyr</span>
                  <div class="message__text">
                    <span class="typing-indicator">
                      <span></span><span></span><span></span>
                    </span>
                  </div>
                </div>
              </div>
            }

            @if (messages().length === 0 && !isStreaming()) {
              <div class="chat-empty">
                <lucide-icon [img]="SparklesIcon" />
                <h3>Let's Build Your Universe</h3>
                <p>Start chatting to develop your world. I'll guide you through each step.</p>
              </div>
            }
          </div>

          @if (showScrollButton()) {
            <button class="scroll-to-bottom" (click)="scrollToBottom()" type="button">
              <lucide-icon [img]="ChevronDownIcon" />
            </button>
          }

          <!-- Chat input -->
          <form class="chat-input" (ngSubmit)="sendMessage()">
            <textarea
              [(ngModel)]="inputText"
              name="message"
              placeholder="Describe your universe..."
              [disabled]="isStreaming()"
              class="chat-input__field"
              rows="1"
              (input)="adjustTextareaHeight($event)"
              (keydown.enter)="onEnterKey($event)"
            ></textarea>
            <button type="submit" class="chat-input__btn" [disabled]="!inputText.trim() || isStreaming()">
              @if (isStreaming()) {
                <lucide-icon [img]="Loader2Icon" class="animate-spin" />
              } @else {
                <lucide-icon [img]="SendIcon" />
              }
            </button>
          </form>
        </main>
      </div>
    </div>
  `,
  styles: [`
    .builder {
      display: flex;
      flex-direction: column;
      height: 100vh;
      position: relative;
      overflow: hidden;
    }

    .builder__bg {
      position: absolute;
      inset: 0;
      pointer-events: none;
    }

    .builder__orb {
      position: absolute;
      border-radius: 50%;
      filter: blur(100px);
      opacity: 0.1;
    }

    .builder__orb--1 {
      width: 400px;
      height: 400px;
      background: var(--wk-secondary);
      top: -150px;
      right: -100px;
    }

    .builder__orb--2 {
      width: 300px;
      height: 300px;
      background: var(--wk-accent);
      bottom: -100px;
      left: 10%;
    }

    .builder__header {
      display: flex;
      align-items: center;
      gap: var(--wk-space-4);
      padding: var(--wk-space-4) var(--wk-space-6);
      background: var(--wk-glass-bg);
      backdrop-filter: blur(var(--wk-blur-md));
      border-bottom: 1px solid var(--wk-glass-border);
      position: relative;
      z-index: 10;
    }

    .back-link {
      display: flex;
      align-items: center;
      gap: var(--wk-space-2);
      padding: var(--wk-space-2);
      color: var(--wk-text-secondary);
      text-decoration: none;
      border-radius: var(--wk-radius-md);
      transition: all var(--wk-transition-fast);
      lucide-icon { width: 18px; height: 18px; }
      &:hover { color: var(--wk-text-primary); background: var(--wk-surface-elevated); }
    }

    .builder__title {
      display: flex;
      align-items: center;
      gap: var(--wk-space-3);
      flex: 1;
    }

    .builder__title-icon {
      width: 40px;
      height: 40px;
      background: linear-gradient(135deg, var(--wk-secondary) 0%, var(--wk-accent) 100%);
      border-radius: var(--wk-radius-lg);
      display: flex;
      align-items: center;
      justify-content: center;
      lucide-icon { width: 20px; height: 20px; color: white; }
    }

    .builder__title h1 {
      margin: 0;
      font-size: var(--wk-text-lg);
      font-weight: var(--wk-font-semibold);
      color: var(--wk-text-primary);
    }

    .builder__mode-badge {
      display: inline-block;
      padding: var(--wk-space-1) var(--wk-space-2);
      background: var(--wk-surface-elevated);
      border-radius: var(--wk-radius-sm);
      font-size: var(--wk-text-xs);
      color: var(--wk-text-secondary);

      &--ai {
        background: var(--wk-secondary-glow);
        color: var(--wk-secondary);
      }
    }

    .builder__actions {
      display: flex;
      gap: var(--wk-space-3);
    }

    .builder__body {
      display: flex;
      flex: 1;
      overflow: hidden;
      position: relative;
      z-index: 5;
    }

    /* Sidebar */
    .sidebar {
      width: 280px;
      background: var(--wk-glass-bg);
      backdrop-filter: blur(var(--wk-blur-md));
      border-right: 1px solid var(--wk-glass-border);
      padding: var(--wk-space-4);
      overflow-y: auto;
      flex-shrink: 0;
    }

    .sidebar__title {
      margin: 0 0 var(--wk-space-4);
      padding-bottom: var(--wk-space-3);
      border-bottom: 1px solid var(--wk-glass-border);
      font-size: var(--wk-text-sm);
      font-weight: var(--wk-font-semibold);
      color: var(--wk-text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .step-list {
      list-style: none;
      padding: 0;
      margin: 0;
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-2);
    }

    .step-item {
      display: flex;
      align-items: flex-start;
      gap: var(--wk-space-3);
      padding: var(--wk-space-3);
      border-radius: var(--wk-radius-lg);
      background: transparent;
      transition: all var(--wk-transition-fast);
    }

    .step-item__icon {
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background: var(--wk-surface-elevated);
      border: 2px solid var(--wk-glass-border);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      lucide-icon { width: 12px; height: 12px; color: var(--wk-text-muted); }
    }

    .step-item--complete .step-item__icon {
      background: var(--wk-success);
      border-color: var(--wk-success);
      lucide-icon { color: white; }
    }

    .step-item--active {
      background: var(--wk-primary-glow);
      .step-item__icon { border-color: var(--wk-primary); }
      .step-item__name { color: var(--wk-primary); }
    }

    .step-item__content {
      flex: 1;
      min-width: 0;
    }

    .step-item__name {
      display: block;
      font-weight: var(--wk-font-medium);
      color: var(--wk-text-primary);
      font-size: var(--wk-text-sm);
    }

    .step-item__desc {
      display: block;
      font-size: var(--wk-text-xs);
      color: var(--wk-text-muted);
      margin-top: var(--wk-space-1);
    }

    .step-item__required {
      font-size: var(--wk-text-xs);
      color: var(--wk-warning);
      flex-shrink: 0;
    }

    /* Chat area */
    .chat-area {
      flex: 1;
      display: flex;
      flex-direction: column;
      min-width: 0;
      position: relative;
    }

    .chat-error {
      background: rgba(255, 99, 99, 0.12);
      border: 1px solid rgba(255, 99, 99, 0.4);
      color: #f05d5d;
      padding: var(--wk-space-3);
      border-radius: var(--wk-radius-md);
      margin: var(--wk-space-4) var(--wk-space-6) 0;
      font-size: var(--wk-text-sm);
    }

    .chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: var(--wk-space-6);
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-4);
    }

    .chat-empty {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      color: var(--wk-text-muted);

      lucide-icon {
        width: 64px;
        height: 64px;
        margin-bottom: var(--wk-space-4);
        opacity: 0.5;
      }

      h3 {
        margin: 0 0 var(--wk-space-2);
        font-size: var(--wk-text-xl);
        color: var(--wk-text-primary);
      }

      p {
        margin: 0;
        font-size: var(--wk-text-sm);
        max-width: 300px;
      }
    }

    .message {
      display: flex;
      gap: var(--wk-space-3);
      max-width: 80%;
    }

    .message--user {
      flex-direction: row-reverse;
      margin-left: auto;
    }

    .message__avatar {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      lucide-icon { width: 18px; height: 18px; color: white; }
    }

    .message--assistant .message__avatar {
      background: linear-gradient(135deg, var(--wk-secondary) 0%, var(--wk-accent) 100%);
    }

    .message--user .message__avatar {
      background: linear-gradient(135deg, var(--wk-primary) 0%, var(--wk-primary-dark) 100%);
    }

    .message__content {
      flex: 1;
      min-width: 0;
    }

    .message__role {
      display: block;
      font-size: var(--wk-text-xs);
      font-weight: var(--wk-font-medium);
      color: var(--wk-text-muted);
      margin-bottom: var(--wk-space-1);
    }

    .message__text {
      padding: var(--wk-space-3) var(--wk-space-4);
      border-radius: var(--wk-radius-lg);
      font-size: var(--wk-text-sm);
      line-height: var(--wk-leading-relaxed);

      /* Use ::ng-deep to style dynamically inserted innerHTML content */
      ::ng-deep {
        ul, ol {
          margin: var(--wk-space-2) 0;
          padding-left: 1.5rem;
          list-style-position: outside;
        }

        ul { list-style-type: disc; }
        ol { list-style-type: decimal; }

        ul ul, ol ul {
          list-style-type: circle;
          padding-left: 1.5rem;
        }
        ul ol, ol ol {
          list-style-type: lower-alpha;
          padding-left: 1.5rem;
        }

        /* Handle sibling pattern: ul following ol (LLM often generates this instead of nested) */
        ol + ul {
          list-style-type: circle;
          padding-left: 3rem;
        }

        li {
          margin: var(--wk-space-1) 0;
          padding-left: 0.25rem;
        }

        li > ul, li > ol {
          margin-top: var(--wk-space-1);
          margin-bottom: var(--wk-space-1);
        }
      }
    }

    .message--assistant .message__text {
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid rgba(148, 163, 184, 0.25);
      color: var(--wk-text-primary);
      backdrop-filter: blur(8px);
    }

    .message--user .message__text {
      background: linear-gradient(135deg, var(--wk-primary) 0%, var(--wk-primary-dark) 100%);
      border: 1px solid rgba(129, 140, 248, 0.4);
      color: white;
      text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }

    .typing-indicator {
      display: inline-flex;
      gap: 4px;

      span {
        width: 8px;
        height: 8px;
        background: var(--wk-text-muted);
        border-radius: 50%;
        animation: typing 1.4s infinite ease-in-out;

        &:nth-child(2) { animation-delay: 0.2s; }
        &:nth-child(3) { animation-delay: 0.4s; }
      }
    }

    .streaming-text {
      display: block;
      white-space: pre-wrap;
      word-wrap: break-word;
      overflow-wrap: break-word;
    }

    .streaming-cursor {
      display: inline-block;
      width: 2px;
      height: 1em;
      background: var(--wk-primary);
      margin-left: 2px;
      animation: blink 1s step-end infinite;
      vertical-align: text-bottom;
    }

    @keyframes typing {
      0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
      40% { transform: scale(1.2); opacity: 1; }
    }

    @keyframes blink {
      0%, 50% { opacity: 1; }
      51%, 100% { opacity: 0; }
    }

    /* Chat input */
    .chat-input {
      display: flex;
      gap: var(--wk-space-3);
      padding: var(--wk-space-4) var(--wk-space-6);
      background: var(--wk-glass-bg);
      backdrop-filter: blur(var(--wk-blur-md));
      border-top: 1px solid var(--wk-glass-border);
    }

    .chat-input__field {
      flex: 1;
      padding: var(--wk-space-3) var(--wk-space-4);
      background: var(--wk-surface-elevated);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-lg);
      color: var(--wk-text-primary);
      font-size: var(--wk-text-sm);
      font-family: inherit;
      line-height: var(--wk-leading-normal);
      transition: all var(--wk-transition-fast);
      resize: none;
      overflow-y: auto;
      min-height: 48px;
      max-height: 200px;
      word-wrap: break-word;
      white-space: pre-wrap;

      &::placeholder { color: var(--wk-text-muted); }

      &:focus {
        outline: none;
        border-color: var(--wk-primary);
        box-shadow: 0 0 0 3px var(--wk-primary-glow);
      }

      &:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
    }

    .chat-input__btn {
      width: 48px;
      height: 48px;
      background: linear-gradient(135deg, var(--wk-primary) 0%, var(--wk-primary-dark) 100%);
      border: none;
      border-radius: var(--wk-radius-lg);
      color: white;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all var(--wk-transition-fast);

      lucide-icon { width: 20px; height: 20px; }

      &:hover:not(:disabled) {
        box-shadow: 0 0 20px var(--wk-primary-glow);
        transform: scale(1.05);
      }

      &:disabled {
        opacity: 0.5;
        cursor: not-allowed;
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
      transition: all var(--wk-transition-fast);
      white-space: nowrap;

      lucide-icon { width: 16px; height: 16px; }

      &:disabled { opacity: 0.5; cursor: not-allowed; }

      &--sm {
        padding: var(--wk-space-2) var(--wk-space-3);
        font-size: var(--wk-text-xs);
      }

      &--ghost {
        background: transparent;
        border: 1px solid var(--wk-glass-border);
        color: var(--wk-text-secondary);

        &:hover:not(:disabled) {
          background: var(--wk-surface-elevated);
          border-color: var(--wk-glass-border-hover);
          color: var(--wk-text-primary);
        }
      }

      &--primary {
        background: linear-gradient(135deg, var(--wk-primary) 0%, var(--wk-primary-dark) 100%);
        border: none;
        color: white;

        &:hover:not(:disabled) {
          box-shadow: 0 0 15px var(--wk-primary-glow);
        }
      }
    }

    .scroll-to-bottom {
      position: absolute;
      bottom: 80px;
      right: var(--wk-space-6);
      width: 48px;
      height: 48px;
      border-radius: 50%;
      background: linear-gradient(135deg, var(--wk-primary) 0%, var(--wk-primary-dark) 100%);
      border: none;
      color: white;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
      transition: all var(--wk-transition-fast);
      z-index: 10;

      lucide-icon { width: 24px; height: 24px; }

      &:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
      }

      &:active {
        transform: scale(0.95);
      }
    }

    .animate-spin { animation: spin 1s linear infinite; }
    @keyframes spin { to { transform: rotate(360deg); } }

    @media (max-width: 768px) {
      .sidebar { display: none; }
      .builder__actions { gap: var(--wk-space-2); }
    }
  `]
})
export class UniverseAiBuilderComponent implements OnInit, OnDestroy, AfterViewChecked {
  private readonly worldgenService = inject(WorldgenService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly sanitizer = inject(DomSanitizer);

  @ViewChild('chatContainer') chatContainer!: ElementRef<HTMLDivElement>;

  readonly ArrowLeftIcon = ArrowLeft;
  readonly SparklesIcon = Sparkles;
  readonly SendIcon = Send;
  readonly Loader2Icon = Loader2;
  readonly CheckIcon = Check;
  readonly CircleIcon = Circle;
  readonly BotIcon = Bot;
  readonly UserIcon = User;
  readonly PenToolIcon = PenTool;
  readonly ChevronDownIcon = ChevronDown;

  readonly steps = WORLDGEN_STEPS;

  inputText = '';
  private shouldScrollToBottom = false;
  private readonly isAtBottom = signal(true);
  readonly showScrollButton = computed(() => !this.isAtBottom());

  // Computed from service
  readonly session = this.worldgenService.currentSession;
  readonly isStreaming = this.worldgenService.isStreaming;
  readonly stepStatus = this.worldgenService.stepStatus;
  readonly canFinalize = this.worldgenService.canFinalize;
  readonly currentStep = this.worldgenService.currentStep;
  readonly pendingUserMessage = this.worldgenService.pendingUserMessage;

  readonly messages = computed(() => this.session()?.conversation_json ?? []);
  readonly mode = computed(() => this.session()?.mode ?? 'ai_collab');
  readonly universeName = computed(() => this.session()?.draft_data_json?.basics?.name ?? '');
  readonly errorMessage = signal('');

  get modeIcon() { return this.mode() === 'ai_collab' ? this.BotIcon : this.PenToolIcon; }

  ngOnInit(): void {
    const sessionId = this.route.snapshot.paramMap.get('sessionId');
    if (sessionId) {
      this.worldgenService.getSession(sessionId).subscribe({
        next: () => {
          this.shouldScrollToBottom = true;
        },
        error: () => this.router.navigate(['/universes/new'])
      });
    } else {
      this.router.navigate(['/universes/new']);
    }
  }

  ngOnDestroy(): void {
    this.worldgenService.clearSession();
  }

  ngAfterViewChecked(): void {
    if (this.shouldScrollToBottom) {
      this.scrollToBottomInstant();
      this.shouldScrollToBottom = false;
    }
  }

  isStepComplete(stepName: WorldgenStepName): boolean {
    return this.stepStatus()?.[stepName]?.complete ?? false;
  }

  sendMessage(): void {
    if (!this.inputText.trim() || this.isStreaming()) return;

    this.errorMessage.set('');
    const message = this.inputText.trim();
    this.inputText = '';

    // Reset textarea height
    const textarea = document.querySelector('.chat-input__field') as HTMLTextAreaElement;
    if (textarea) {
      textarea.style.height = 'auto';
    }

    this.shouldScrollToBottom = true;

    const sessionId = this.session()?.id;
    if (!sessionId) return;

    this.worldgenService.sendMessage(sessionId, message).subscribe({
      next: () => {
        this.shouldScrollToBottom = true;
      },
      error: err => {
        console.error('Chat error:', err);
        const friendly = err?.message && err.message.trim() !== '' ? err.message : 'Chat request failed. Please try again.';
        this.errorMessage.set(friendly);
      }
    });
  }

  adjustTextareaHeight(event: Event): void {
    const textarea = event.target as HTMLTextAreaElement;
    textarea.style.height = 'auto';
    const maxHeight = 200;
    const newHeight = Math.min(textarea.scrollHeight, maxHeight);
    textarea.style.height = newHeight + 'px';
  }

  onEnterKey(event: Event): void {
    const keyEvent = event as KeyboardEvent;
    if (!keyEvent.shiftKey) {
      keyEvent.preventDefault();
      this.sendMessage();
    }
  }

  onScroll(): void {
    if (!this.chatContainer?.nativeElement) return;

    const el = this.chatContainer.nativeElement;
    const threshold = 100;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < threshold;

    this.isAtBottom.set(atBottom);
  }

  scrollToBottom(): void {
    if (this.chatContainer?.nativeElement) {
      const el = this.chatContainer.nativeElement;
      el.scrollTo({
        top: el.scrollHeight,
        behavior: 'smooth'
      });
    }
  }

  switchMode(): void {
    const session = this.session();
    if (!session) return;

    const newMode = session.mode === 'ai_collab' ? 'manual' : 'ai_collab';
    this.worldgenService.switchMode(session.id, newMode).subscribe({
      error: err => console.error('Mode switch error:', err)
    });
  }

  finalize(): void {
    const session = this.session();
    if (!session) return;

    this.worldgenService.finalizeSession(session.id).subscribe({
      next: universe => {
        this.router.navigate(['/universes', universe.id]);
      },
      error: err => {
        console.error('Finalize error:', err);
      }
    });
  }

  private scrollToBottomInstant(): void {
    if (this.chatContainer?.nativeElement) {
      const el = this.chatContainer.nativeElement;
      el.scrollTop = el.scrollHeight;
    }
  }

  renderMarkdown(text: string): string {
    return this.worldgenService.renderMarkdown(text);
  }

  renderMarkdownSafe(text: string): SafeHtml {
    const html = this.worldgenService.renderMarkdown(text);
    return this.sanitizer.bypassSecurityTrustHtml(html);
  }
}
