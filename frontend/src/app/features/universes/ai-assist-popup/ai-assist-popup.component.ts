import { Component, inject, input, output, signal, OnDestroy, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WorldgenService } from '@core/services/worldgen.service';
import { WorldgenStepName, WorldgenChatMessage } from '@core/models';
import {
  LucideAngularModule,
  X,
  Sparkles,
  Send,
  Loader2,
  User,
  Minimize2,
  Maximize2
} from 'lucide-angular';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-ai-assist-popup',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule],
  template: `
    <div class="popup" [class.popup--minimized]="isMinimized()" [class.popup--visible]="isVisible()">
      <!-- Header -->
      <div class="popup__header" (click)="isMinimized() && toggleMinimize()">
        <div class="popup__title">
          <lucide-icon [img]="SparklesIcon" />
          <span>Whispyr</span>
          @if (currentStep()) {
            <span class="popup__step">{{ currentStep() }}</span>
          }
        </div>
        <div class="popup__actions">
          <button class="popup__btn" (click)="toggleMinimize(); $event.stopPropagation()" title="{{ isMinimized() ? 'Expand' : 'Minimize' }}">
            <lucide-icon [img]="isMinimized() ? Maximize2Icon : Minimize2Icon" />
          </button>
          <button class="popup__btn" (click)="close()" title="Close">
            <lucide-icon [img]="XIcon" />
          </button>
        </div>
      </div>

      @if (!isMinimized()) {
        <!-- Messages -->
        <div class="popup__messages" #messagesContainer>
          @if (messages().length === 0 && !isStreaming()) {
            <div class="popup__empty">
              <lucide-icon [img]="SparklesIcon" />
              <p>Ask me anything about this step!</p>
            </div>
          }

          @for (msg of messages(); track $index) {
            <div class="popup__msg" [class.popup__msg--user]="msg.role === 'user'">
              <div class="popup__avatar">
                <lucide-icon [img]="msg.role === 'user' ? UserIcon : SparklesIcon" />
              </div>
              <div class="popup__text">{{ msg.content }}</div>
            </div>
          }

          @if (isStreaming()) {
            <div class="popup__msg">
              <div class="popup__avatar">
                <lucide-icon [img]="SparklesIcon" />
              </div>
              <div class="popup__text">
                {{ streamContent() }}
                <span class="typing">
                  <span></span><span></span><span></span>
                </span>
              </div>
            </div>
          }
        </div>

        <!-- Input -->
        <form class="popup__input" (ngSubmit)="sendMessage()">
          <input
            type="text"
            [(ngModel)]="inputText"
            name="message"
            placeholder="Ask for help..."
            [disabled]="isStreaming()"
          />
          <button type="submit" [disabled]="!inputText.trim() || isStreaming()">
            @if (isStreaming()) {
              <lucide-icon [img]="Loader2Icon" class="animate-spin" />
            } @else {
              <lucide-icon [img]="SendIcon" />
            }
          </button>
        </form>
      }
    </div>
  `,
  styles: [`
    .popup {
      position: fixed;
      bottom: var(--wk-space-4);
      right: var(--wk-space-4);
      width: 380px;
      max-height: 500px;
      background: var(--wk-glass-bg);
      backdrop-filter: blur(var(--wk-blur-lg));
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-2xl);
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
      display: flex;
      flex-direction: column;
      z-index: 1000;
      opacity: 0;
      transform: translateY(20px) scale(0.95);
      pointer-events: none;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

      &--visible {
        opacity: 1;
        transform: translateY(0) scale(1);
        pointer-events: all;
      }

      &--minimized {
        max-height: 48px;
        width: 200px;
        cursor: pointer;
      }
    }

    .popup__header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: var(--wk-space-3) var(--wk-space-4);
      border-bottom: 1px solid var(--wk-glass-border);
      background: linear-gradient(135deg, var(--wk-secondary-glow) 0%, transparent 100%);
      border-radius: var(--wk-radius-2xl) var(--wk-radius-2xl) 0 0;

      .popup--minimized & {
        border-radius: var(--wk-radius-2xl);
        border-bottom: none;
      }
    }

    .popup__title {
      display: flex;
      align-items: center;
      gap: var(--wk-space-2);
      font-weight: var(--wk-font-semibold);
      font-size: var(--wk-text-sm);
      color: var(--wk-text-primary);

      lucide-icon {
        width: 18px;
        height: 18px;
        color: var(--wk-secondary);
      }
    }

    .popup__step {
      padding: var(--wk-space-1) var(--wk-space-2);
      background: var(--wk-surface-elevated);
      border-radius: var(--wk-radius-sm);
      font-size: var(--wk-text-xs);
      color: var(--wk-text-secondary);
      text-transform: capitalize;
    }

    .popup__actions {
      display: flex;
      gap: var(--wk-space-1);
    }

    .popup__btn {
      width: 28px;
      height: 28px;
      background: transparent;
      border: none;
      border-radius: var(--wk-radius-md);
      color: var(--wk-text-secondary);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all var(--wk-transition-fast);

      lucide-icon { width: 16px; height: 16px; }

      &:hover {
        background: var(--wk-surface-elevated);
        color: var(--wk-text-primary);
      }
    }

    .popup__messages {
      flex: 1;
      overflow-y: auto;
      padding: var(--wk-space-4);
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-3);
      min-height: 200px;
      max-height: 350px;
    }

    .popup__empty {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      color: var(--wk-text-muted);

      lucide-icon {
        width: 40px;
        height: 40px;
        margin-bottom: var(--wk-space-3);
        opacity: 0.4;
      }

      p {
        margin: 0;
        font-size: var(--wk-text-sm);
      }
    }

    .popup__msg {
      display: flex;
      gap: var(--wk-space-2);
      max-width: 90%;

      &--user {
        flex-direction: row-reverse;
        margin-left: auto;
      }
    }

    .popup__avatar {
      width: 28px;
      height: 28px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      background: linear-gradient(135deg, var(--wk-secondary) 0%, var(--wk-accent) 100%);

      lucide-icon { width: 14px; height: 14px; color: white; }

      .popup__msg--user & {
        background: linear-gradient(135deg, var(--wk-primary) 0%, var(--wk-primary-dark) 100%);
      }
    }

    .popup__text {
      padding: var(--wk-space-2) var(--wk-space-3);
      background: var(--wk-surface-elevated);
      border-radius: var(--wk-radius-lg);
      font-size: var(--wk-text-xs);
      line-height: var(--wk-leading-relaxed);
      color: var(--wk-text-primary);

      .popup__msg--user & {
        background: linear-gradient(135deg, var(--wk-primary) 0%, var(--wk-primary-dark) 100%);
        color: white;
      }
    }

    .typing {
      display: inline-flex;
      gap: 3px;
      margin-left: var(--wk-space-1);

      span {
        width: 4px;
        height: 4px;
        background: var(--wk-text-muted);
        border-radius: 50%;
        animation: typing 1.4s infinite ease-in-out;

        &:nth-child(2) { animation-delay: 0.2s; }
        &:nth-child(3) { animation-delay: 0.4s; }
      }
    }

    @keyframes typing {
      0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
      40% { transform: scale(1); opacity: 1; }
    }

    .popup__input {
      display: flex;
      gap: var(--wk-space-2);
      padding: var(--wk-space-3);
      border-top: 1px solid var(--wk-glass-border);

      input {
        flex: 1;
        padding: var(--wk-space-2) var(--wk-space-3);
        background: var(--wk-surface-elevated);
        border: 1px solid var(--wk-glass-border);
        border-radius: var(--wk-radius-lg);
        color: var(--wk-text-primary);
        font-size: var(--wk-text-xs);
        transition: all var(--wk-transition-fast);

        &::placeholder { color: var(--wk-text-muted); }

        &:focus {
          outline: none;
          border-color: var(--wk-primary);
        }

        &:disabled { opacity: 0.6; }
      }

      button {
        width: 36px;
        height: 36px;
        background: linear-gradient(135deg, var(--wk-primary) 0%, var(--wk-primary-dark) 100%);
        border: none;
        border-radius: var(--wk-radius-lg);
        color: white;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all var(--wk-transition-fast);

        lucide-icon { width: 16px; height: 16px; }

        &:hover:not(:disabled) {
          box-shadow: 0 0 15px var(--wk-primary-glow);
        }

        &:disabled { opacity: 0.5; cursor: not-allowed; }
      }
    }

    .animate-spin { animation: spin 1s linear infinite; }
    @keyframes spin { to { transform: rotate(360deg); } }
  `]
})
export class AiAssistPopupComponent implements OnDestroy, AfterViewChecked {
  private readonly worldgenService = inject(WorldgenService);

  @ViewChild('messagesContainer') messagesContainer?: ElementRef<HTMLDivElement>;

  // Icons
  readonly XIcon = X;
  readonly SparklesIcon = Sparkles;
  readonly SendIcon = Send;
  readonly Loader2Icon = Loader2;
  readonly UserIcon = User;
  readonly Minimize2Icon = Minimize2;
  readonly Maximize2Icon = Maximize2;

  // Inputs
  readonly sessionId = input<string>();
  readonly currentStep = input<WorldgenStepName>();

  // Outputs
  readonly closed = output<void>();
  readonly dataUpdated = output<void>();

  // Local state
  readonly isVisible = signal(false);
  readonly isMinimized = signal(false);
  readonly messages = signal<WorldgenChatMessage[]>([]);

  inputText = '';
  private shouldScrollToBottom = false;
  private activeStreamSub: Subscription | null = null;

  // From service
  readonly isStreaming = this.worldgenService.isStreaming;
  readonly streamContent = this.worldgenService.streamContent;

  ngAfterViewChecked(): void {
    if (this.shouldScrollToBottom && this.messagesContainer) {
      this.scrollToBottom();
      this.shouldScrollToBottom = false;
    }
  }

  show(): void {
    this.isVisible.set(true);
    this.isMinimized.set(false);
  }

  hide(): void {
    this.activeStreamSub?.unsubscribe();
    this.activeStreamSub = null;
    this.isVisible.set(false);
  }

  close(): void {
    this.hide();
    this.closed.emit();
  }

  toggleMinimize(): void {
    this.isMinimized.update(v => !v);
  }

  sendMessage(): void {
    const sessionId = this.sessionId();
    const step = this.currentStep();

    if (!this.inputText.trim() || this.isStreaming() || !sessionId) return;

    const message = this.inputText.trim();
    this.inputText = '';
    this.shouldScrollToBottom = true;

    // Add user message locally
    this.messages.update(msgs => [...msgs, {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    }]);

    // Use AI assist for the current step with user's message
    this.activeStreamSub?.unsubscribe();
    this.activeStreamSub = this.worldgenService.getAiAssist(sessionId, step || 'basics', undefined, message).subscribe({
      next: event => {
        if (event.type === 'chunk') {
          this.shouldScrollToBottom = true;
        }
        if (event.type === 'complete') {
          // Add assistant message
          this.messages.update(msgs => [...msgs, {
            role: 'assistant',
            content: this.streamContent(),
            timestamp: new Date().toISOString()
          }]);
          this.dataUpdated.emit();
        }
      },
      error: err => {
        console.error('AI assist error:', err);
        this.messages.update(msgs => [...msgs, {
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.',
          timestamp: new Date().toISOString()
        }]);
      }
    });
  }

  private scrollToBottom(): void {
    if (this.messagesContainer?.nativeElement) {
      const el = this.messagesContainer.nativeElement;
      el.scrollTop = el.scrollHeight;
    }
  }

  ngOnDestroy(): void {
    this.activeStreamSub?.unsubscribe();
    this.activeStreamSub = null;
  }
}
