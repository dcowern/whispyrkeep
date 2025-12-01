import { Component, inject, signal, computed, Input, Output, EventEmitter, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WorldgenService } from '@core/services/worldgen.service';
import { ConsistencyCheckProgress, ConsistencyCheckStatus, WorldgenDraftData } from '@core/models';
import {
  LucideAngularModule,
  X,
  AlertTriangle,
  Check,
  Loader2,
  RefreshCw,
  Edit3,
  ChevronRight
} from 'lucide-angular';
import { interval, Subject, takeUntil } from 'rxjs';

@Component({
  selector: 'app-consistency-check-panel',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule],
  template: `
    <div class="panel-overlay" [class.panel-overlay--open]="isOpen" (click)="onOverlayClick($event)">
      <div class="panel" [class.panel--open]="isOpen" (click)="$event.stopPropagation()">
        <!-- Header -->
        <header class="panel__header">
          <h2>Consistency Check</h2>
          <button class="panel__close" (click)="close.emit()" type="button">
            <lucide-icon [img]="XIcon" />
          </button>
        </header>

        <!-- Content -->
        <div class="panel__content">
          @if (!checkId()) {
            <!-- Start state -->
            <div class="start-state">
              <div class="start-state__icon">
                <lucide-icon [img]="AlertTriangleIcon" />
              </div>
              <h3>Check for Contradictions</h3>
              <p>
                This will compare your universe content across all fields to find any contradictions or inconsistencies.
              </p>
              <p class="start-state__estimate">
                Estimated time: ~{{ estimatedMinutes() }} minutes
              </p>
              <button class="btn btn--primary" (click)="startCheck()" [disabled]="isStarting()">
                @if (isStarting()) {
                  <lucide-icon [img]="Loader2Icon" class="animate-spin" />
                  Starting...
                } @else {
                  Start Check
                }
              </button>
            </div>
          } @else if (status() === 'in_progress' || status() === 'pending') {
            <!-- Progress state -->
            <div class="progress-state">
              <div class="progress-state__icon">
                <lucide-icon [img]="Loader2Icon" class="animate-spin" />
              </div>
              <h3>Checking Consistency...</h3>
              <div class="progress-bar">
                <div class="progress-bar__fill" [style.width.%]="progressPercent()"></div>
              </div>
              <p class="progress-state__status">
                {{ currentPair() || 'Preparing...' }}
              </p>
              <p class="progress-state__count">
                {{ checkedPairs() }} of {{ totalPairs() }} pairs checked
              </p>
            </div>
          } @else if (status() === 'conflict_found' && currentConflict()) {
            <!-- Conflict state -->
            <div class="conflict-state">
              <div class="conflict-state__header">
                <lucide-icon [img]="AlertTriangleIcon" />
                <h3>Conflict Found</h3>
              </div>

              <div class="conflict-state__description">
                {{ currentConflict()!.conflict_description }}
              </div>

              <div class="conflict-state__fields">
                <div class="field-box">
                  <h4>{{ currentConflict()!.field_a_label }}</h4>
                  <div class="field-box__content">
                    {{ getFieldValue(currentConflict()!.field_a) }}
                  </div>
                  @if (currentConflict()!.resolution_target === 'a' || currentConflict()!.resolution_target === 'both') {
                    <span class="field-box__badge">Needs Update</span>
                  }
                </div>
                <div class="field-divider">
                  <lucide-icon [img]="ChevronRightIcon" />
                </div>
                <div class="field-box">
                  <h4>{{ currentConflict()!.field_b_label }}</h4>
                  <div class="field-box__content">
                    {{ getFieldValue(currentConflict()!.field_b) }}
                  </div>
                  @if (currentConflict()!.resolution_target === 'b' || currentConflict()!.resolution_target === 'both') {
                    <span class="field-box__badge">Needs Update</span>
                  }
                </div>
              </div>

              @if (currentConflict()!.suggested_resolution) {
                <div class="conflict-state__suggestion">
                  <h4>AI Suggestion</h4>
                  <p>{{ currentConflict()!.suggested_resolution }}</p>
                </div>
              }

              <div class="conflict-state__actions">
                <button
                  class="btn btn--primary"
                  (click)="acceptResolution()"
                  [disabled]="isResolving()"
                >
                  @if (isResolving()) {
                    <lucide-icon [img]="Loader2Icon" class="animate-spin" />
                  } @else {
                    <lucide-icon [img]="CheckIcon" />
                  }
                  Accept & Continue
                </button>
                <button
                  class="btn btn--secondary"
                  (click)="editField('a')"
                  [disabled]="isResolving()"
                >
                  <lucide-icon [img]="Edit3Icon" />
                  Edit {{ currentConflict()!.field_a_label }}
                </button>
                <button
                  class="btn btn--secondary"
                  (click)="editField('b')"
                  [disabled]="isResolving()"
                >
                  <lucide-icon [img]="Edit3Icon" />
                  Edit {{ currentConflict()!.field_b_label }}
                </button>
              </div>

              <div class="conflict-state__progress">
                {{ conflictsFound() }} conflicts found, {{ conflictsResolved() }} resolved
              </div>
            </div>
          } @else if (status() === 'completed') {
            <!-- Complete state -->
            <div class="complete-state">
              <div class="complete-state__icon complete-state__icon--success">
                <lucide-icon [img]="CheckIcon" />
              </div>
              @if (conflictsFound() === 0) {
                <h3>No Conflicts Found!</h3>
                <p>Your universe content is internally consistent.</p>
              } @else {
                <h3>All Conflicts Resolved!</h3>
                <p>{{ conflictsResolved() }} conflicts were found and resolved.</p>
              }
              <button class="btn btn--primary" (click)="close.emit()">
                <lucide-icon [img]="CheckIcon" />
                Done
              </button>
            </div>
          } @else if (status() === 'failed') {
            <!-- Error state -->
            <div class="error-state">
              <div class="error-state__icon">
                <lucide-icon [img]="AlertTriangleIcon" />
              </div>
              <h3>Check Failed</h3>
              <p>{{ errorMessage() || 'An error occurred during the consistency check.' }}</p>
              <button class="btn btn--primary" (click)="resetAndStart()">
                <lucide-icon [img]="RefreshCwIcon" />
                Try Again
              </button>
            </div>
          }
        </div>
      </div>
    </div>
  `,
  styles: [`
    .panel-overlay {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.5);
      backdrop-filter: blur(4px);
      opacity: 0;
      visibility: hidden;
      transition: all var(--wk-transition-normal);
      z-index: 100;

      &--open {
        opacity: 1;
        visibility: visible;
      }
    }

    .panel {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%) scale(0.95);
      width: 90%;
      max-width: 600px;
      max-height: 90vh;
      background: var(--wk-surface);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-xl);
      display: flex;
      flex-direction: column;
      opacity: 0;
      transition: all var(--wk-transition-normal);
      overflow: hidden;

      .panel-overlay--open & {
        opacity: 1;
        transform: translate(-50%, -50%) scale(1);
      }
    }

    .panel__header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: var(--wk-space-4) var(--wk-space-5);
      border-bottom: 1px solid var(--wk-glass-border);

      h2 {
        margin: 0;
        font-size: var(--wk-text-lg);
        font-weight: var(--wk-font-semibold);
        color: var(--wk-text-primary);
      }
    }

    .panel__close {
      width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: transparent;
      border: none;
      border-radius: var(--wk-radius-md);
      color: var(--wk-text-muted);
      cursor: pointer;
      transition: all var(--wk-transition-fast);

      lucide-icon { width: 18px; height: 18px; }

      &:hover {
        background: var(--wk-surface-elevated);
        color: var(--wk-text-primary);
      }
    }

    .panel__content {
      flex: 1;
      overflow-y: auto;
      padding: var(--wk-space-6);
    }

    /* Start state */
    .start-state {
      text-align: center;
      padding: var(--wk-space-4);
    }

    .start-state__icon {
      width: 64px;
      height: 64px;
      margin: 0 auto var(--wk-space-4);
      border-radius: 50%;
      background: var(--wk-warning-glow);
      display: flex;
      align-items: center;
      justify-content: center;

      lucide-icon {
        width: 32px;
        height: 32px;
        color: var(--wk-warning);
      }
    }

    .start-state h3 {
      margin: 0 0 var(--wk-space-3);
      font-size: var(--wk-text-xl);
      color: var(--wk-text-primary);
    }

    .start-state p {
      margin: 0 0 var(--wk-space-4);
      color: var(--wk-text-secondary);
      line-height: var(--wk-leading-relaxed);
    }

    .start-state__estimate {
      font-size: var(--wk-text-sm);
      color: var(--wk-text-muted);
      margin-bottom: var(--wk-space-5) !important;
    }

    /* Progress state */
    .progress-state {
      text-align: center;
      padding: var(--wk-space-4);
    }

    .progress-state__icon {
      width: 64px;
      height: 64px;
      margin: 0 auto var(--wk-space-4);
      border-radius: 50%;
      background: var(--wk-primary-glow);
      display: flex;
      align-items: center;
      justify-content: center;

      lucide-icon {
        width: 32px;
        height: 32px;
        color: var(--wk-primary);
      }
    }

    .progress-state h3 {
      margin: 0 0 var(--wk-space-4);
      font-size: var(--wk-text-xl);
      color: var(--wk-text-primary);
    }

    .progress-bar {
      width: 100%;
      height: 8px;
      background: var(--wk-surface-elevated);
      border-radius: var(--wk-radius-full);
      overflow: hidden;
      margin-bottom: var(--wk-space-4);
    }

    .progress-bar__fill {
      height: 100%;
      background: linear-gradient(90deg, var(--wk-primary), var(--wk-secondary));
      border-radius: var(--wk-radius-full);
      transition: width 0.3s ease;
    }

    .progress-state__status {
      margin: 0 0 var(--wk-space-2);
      color: var(--wk-text-primary);
      font-size: var(--wk-text-sm);
    }

    .progress-state__count {
      margin: 0;
      color: var(--wk-text-muted);
      font-size: var(--wk-text-xs);
    }

    /* Conflict state */
    .conflict-state {
      padding: var(--wk-space-2);
    }

    .conflict-state__header {
      display: flex;
      align-items: center;
      gap: var(--wk-space-3);
      margin-bottom: var(--wk-space-4);

      lucide-icon {
        width: 24px;
        height: 24px;
        color: var(--wk-warning);
      }

      h3 {
        margin: 0;
        font-size: var(--wk-text-lg);
        color: var(--wk-text-primary);
      }
    }

    .conflict-state__description {
      background: var(--wk-warning-glow);
      border: 1px solid rgba(251, 191, 36, 0.3);
      border-radius: var(--wk-radius-lg);
      padding: var(--wk-space-4);
      margin-bottom: var(--wk-space-4);
      color: var(--wk-text-primary);
      font-size: var(--wk-text-sm);
      line-height: var(--wk-leading-relaxed);
    }

    .conflict-state__fields {
      display: flex;
      gap: var(--wk-space-3);
      margin-bottom: var(--wk-space-4);
    }

    .field-box {
      flex: 1;
      background: var(--wk-surface-elevated);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-lg);
      padding: var(--wk-space-3);
      position: relative;

      h4 {
        margin: 0 0 var(--wk-space-2);
        font-size: var(--wk-text-xs);
        font-weight: var(--wk-font-semibold);
        color: var(--wk-text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }
    }

    .field-box__content {
      font-size: var(--wk-text-sm);
      color: var(--wk-text-primary);
      max-height: 120px;
      overflow-y: auto;
      line-height: var(--wk-leading-relaxed);
      white-space: pre-wrap;
    }

    .field-box__badge {
      position: absolute;
      top: var(--wk-space-2);
      right: var(--wk-space-2);
      background: var(--wk-warning);
      color: black;
      font-size: var(--wk-text-xs);
      font-weight: var(--wk-font-medium);
      padding: var(--wk-space-1) var(--wk-space-2);
      border-radius: var(--wk-radius-sm);
    }

    .field-divider {
      display: flex;
      align-items: center;
      color: var(--wk-text-muted);

      lucide-icon {
        width: 20px;
        height: 20px;
      }
    }

    .conflict-state__suggestion {
      background: var(--wk-secondary-glow);
      border: 1px solid rgba(139, 92, 246, 0.3);
      border-radius: var(--wk-radius-lg);
      padding: var(--wk-space-4);
      margin-bottom: var(--wk-space-4);

      h4 {
        margin: 0 0 var(--wk-space-2);
        font-size: var(--wk-text-sm);
        font-weight: var(--wk-font-semibold);
        color: var(--wk-secondary);
      }

      p {
        margin: 0;
        font-size: var(--wk-text-sm);
        color: var(--wk-text-primary);
        line-height: var(--wk-leading-relaxed);
      }
    }

    .conflict-state__actions {
      display: flex;
      flex-wrap: wrap;
      gap: var(--wk-space-3);
      margin-bottom: var(--wk-space-4);
    }

    .conflict-state__progress {
      text-align: center;
      font-size: var(--wk-text-xs);
      color: var(--wk-text-muted);
    }

    /* Complete state */
    .complete-state {
      text-align: center;
      padding: var(--wk-space-4);
    }

    .complete-state__icon {
      width: 64px;
      height: 64px;
      margin: 0 auto var(--wk-space-4);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;

      lucide-icon {
        width: 32px;
        height: 32px;
      }

      &--success {
        background: var(--wk-success-glow);
        lucide-icon { color: var(--wk-success); }
      }
    }

    .complete-state h3 {
      margin: 0 0 var(--wk-space-3);
      font-size: var(--wk-text-xl);
      color: var(--wk-text-primary);
    }

    .complete-state p {
      margin: 0 0 var(--wk-space-5);
      color: var(--wk-text-secondary);
    }

    /* Error state */
    .error-state {
      text-align: center;
      padding: var(--wk-space-4);
    }

    .error-state__icon {
      width: 64px;
      height: 64px;
      margin: 0 auto var(--wk-space-4);
      border-radius: 50%;
      background: rgba(239, 68, 68, 0.15);
      display: flex;
      align-items: center;
      justify-content: center;

      lucide-icon {
        width: 32px;
        height: 32px;
        color: #ef4444;
      }
    }

    .error-state h3 {
      margin: 0 0 var(--wk-space-3);
      font-size: var(--wk-text-xl);
      color: var(--wk-text-primary);
    }

    .error-state p {
      margin: 0 0 var(--wk-space-5);
      color: var(--wk-text-secondary);
    }

    /* Buttons */
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: var(--wk-space-2);
      padding: var(--wk-space-3) var(--wk-space-5);
      border-radius: var(--wk-radius-lg);
      font-size: var(--wk-text-sm);
      font-weight: var(--wk-font-medium);
      cursor: pointer;
      transition: all var(--wk-transition-fast);
      border: none;

      lucide-icon { width: 16px; height: 16px; }

      &:disabled { opacity: 0.5; cursor: not-allowed; }

      &--primary {
        background: linear-gradient(135deg, var(--wk-primary) 0%, var(--wk-primary-dark) 100%);
        color: white;

        &:hover:not(:disabled) {
          box-shadow: 0 0 15px var(--wk-primary-glow);
        }
      }

      &--secondary {
        background: var(--wk-surface-elevated);
        border: 1px solid var(--wk-glass-border);
        color: var(--wk-text-secondary);

        &:hover:not(:disabled) {
          background: var(--wk-surface);
          color: var(--wk-text-primary);
        }
      }
    }

    .animate-spin {
      animation: spin 1s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  `]
})
export class ConsistencyCheckPanelComponent implements OnDestroy {
  private readonly worldgenService = inject(WorldgenService);
  private destroy$ = new Subject<void>();

  @Input() isOpen = false;
  @Input() sessionId: string | null = null;
  @Input() draftData: WorldgenDraftData | null = null;
  @Output() close = new EventEmitter<void>();
  @Output() editFieldRequest = new EventEmitter<{ step: string; field: string }>();

  readonly XIcon = X;
  readonly AlertTriangleIcon = AlertTriangle;
  readonly CheckIcon = Check;
  readonly Loader2Icon = Loader2;
  readonly RefreshCwIcon = RefreshCw;
  readonly Edit3Icon = Edit3;
  readonly ChevronRightIcon = ChevronRight;

  // State
  readonly checkId = signal<string | null>(null);
  readonly status = signal<ConsistencyCheckStatus | null>(null);
  readonly totalPairs = signal(0);
  readonly checkedPairs = signal(0);
  readonly currentPair = signal<string | null>(null);
  readonly conflictsFound = signal(0);
  readonly conflictsResolved = signal(0);
  readonly errorMessage = signal<string | null>(null);
  readonly currentConflict = signal<ConsistencyCheckProgress['current_conflict']>(null);
  readonly isStarting = signal(false);
  readonly isResolving = signal(false);

  // Computed
  readonly progressPercent = computed(() => {
    const total = this.totalPairs();
    const checked = this.checkedPairs();
    if (total === 0) return 0;
    return Math.round((checked / total) * 100);
  });

  readonly estimatedMinutes = computed(() => {
    // Rough estimate: ~2 seconds per LLM call
    // Typical check might have 30-120 pairs
    return Math.ceil(60 * 2 / 60); // ~2-4 minutes
  });

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onOverlayClick(event: Event): void {
    if ((event.target as HTMLElement).classList.contains('panel-overlay')) {
      this.close.emit();
    }
  }

  startCheck(): void {
    if (!this.sessionId || this.isStarting()) return;

    this.isStarting.set(true);
    this.errorMessage.set(null);

    this.worldgenService.startConsistencyCheck(this.sessionId).subscribe({
      next: (response) => {
        this.isStarting.set(false);

        if (!response.check_id) {
          // No fields to compare
          this.status.set('completed');
          this.totalPairs.set(0);
          return;
        }

        this.checkId.set(response.check_id);
        this.status.set(response.status as ConsistencyCheckStatus);
        this.totalPairs.set(response.total_pairs);
        this.checkedPairs.set(response.checked_pairs ?? 0);
        this.currentPair.set(response.current_pair ?? null);

        // Start polling for progress
        this.pollForProgress();
      },
      error: (err) => {
        this.isStarting.set(false);
        this.errorMessage.set(err?.error?.error || 'Failed to start consistency check');
        this.status.set('failed');
      }
    });
  }

  private pollForProgress(): void {
    const checkId = this.checkId();
    if (!checkId || !this.sessionId) return;

    // Continue the check to advance to next pair
    this.worldgenService.continueConsistencyCheck(this.sessionId, checkId).subscribe({
      next: (progress) => {
        this.updateFromProgress(progress);

        // If still in progress, poll again after a short delay
        if (progress.status === 'in_progress' || progress.status === 'pending') {
          setTimeout(() => this.pollForProgress(), 500);
        }
      },
      error: (err) => {
        this.errorMessage.set(err?.error?.error || 'Check failed');
        this.status.set('failed');
      }
    });
  }

  private updateFromProgress(progress: ConsistencyCheckProgress): void {
    this.status.set(progress.status);
    this.checkedPairs.set(progress.checked_pairs);
    this.currentPair.set(progress.current_pair);
    this.conflictsFound.set(progress.conflicts_found);
    this.conflictsResolved.set(progress.conflicts_resolved);
    this.errorMessage.set(progress.error_message);
    this.currentConflict.set(progress.current_conflict ?? null);
  }

  acceptResolution(): void {
    const checkId = this.checkId();
    if (!checkId || !this.sessionId || this.isResolving()) return;

    this.isResolving.set(true);

    this.worldgenService.resolveConflict(this.sessionId, checkId, 'accept').subscribe({
      next: (progress) => {
        this.isResolving.set(false);
        this.updateFromProgress(progress);

        // If back to in_progress, continue polling
        if (progress.status === 'in_progress') {
          this.pollForProgress();
        }
      },
      error: (err) => {
        this.isResolving.set(false);
        this.errorMessage.set(err?.error?.error || 'Failed to resolve conflict');
      }
    });
  }

  editField(target: 'a' | 'b'): void {
    const conflict = this.currentConflict();
    if (!conflict) return;

    const fieldPath = target === 'a' ? conflict.field_a : conflict.field_b;
    const [step, field] = fieldPath.split('.');

    // Emit event to parent to open the step panel for editing
    this.editFieldRequest.emit({ step, field });
  }

  getFieldValue(fieldPath: string): string {
    if (!this.draftData || !fieldPath) return '';

    const [step, field] = fieldPath.split('.');
    const stepData = (this.draftData as Record<string, Record<string, unknown>>)[step];
    if (!stepData) return '';

    const value = stepData[field];
    if (value === null || value === undefined) return '';
    if (typeof value === 'string') return value.substring(0, 300) + (value.length > 300 ? '...' : '');
    return JSON.stringify(value).substring(0, 300);
  }

  resetAndStart(): void {
    this.checkId.set(null);
    this.status.set(null);
    this.totalPairs.set(0);
    this.checkedPairs.set(0);
    this.currentPair.set(null);
    this.conflictsFound.set(0);
    this.conflictsResolved.set(0);
    this.errorMessage.set(null);
    this.currentConflict.set(null);

    this.startCheck();
  }
}
