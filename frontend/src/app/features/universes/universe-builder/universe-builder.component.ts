import { Component, inject, input, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { UniverseService } from '@core/services';
import { Universe, UniverseCreate, UniverseTone, UniverseRules } from '@core/models';

type Step = 'basics' | 'tone' | 'rules' | 'cowrite' | 'lore' | 'review';

@Component({
  selector: 'app-universe-builder',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  template: `
    <div class="builder">
      <header class="builder__header">
        <a routerLink="/universes" class="back-link">Back to universes</a>
        <h1>{{ id() ? 'Edit Universe' : 'Create Universe' }}</h1>
      </header>

      <nav class="steps">
        @for (s of steps; track s) {
          <button class="step" [class.step--active]="step() === s" (click)="step.set(s)">
            {{ stepLabels[s] }}
          </button>
        }
      </nav>

      <main class="builder__content">
        <!-- Basics -->
        @if (step() === 'basics') {
          <section class="step-content">
            <h2>Universe Basics</h2>
            <div class="form-grid">
              <div class="form-group">
                <label for="name">Universe Name</label>
                <input id="name" [(ngModel)]="universe.name" class="form-input" />
              </div>
              <div class="form-group form-group--full">
                <label for="description">Description</label>
                <textarea id="description" [(ngModel)]="universe.description" class="form-input" rows="4"></textarea>
              </div>
            </div>
          </section>
        }

        <!-- Tone sliders -->
        @if (step() === 'tone') {
          <section class="step-content">
            <h2>Universe Tone</h2>
            <p class="step-desc">Adjust sliders to set the tone of your universe.</p>
            @for (slider of toneSliders; track slider.key) {
              <div class="slider-group">
                <label class="slider-label">{{ slider.label }}</label>
                <input type="range" min="0" max="100" [(ngModel)]="universe.tone![slider.key]" class="slider" />
                <span class="slider-value">{{ universe.tone![slider.key] }}</span>
              </div>
            }
          </section>
        }

        <!-- Rules -->
        @if (step() === 'rules') {
          <section class="step-content">
            <h2>Optional Rules</h2>
            <div class="rules-list">
              <label class="rule-toggle">
                <input type="checkbox" [(ngModel)]="universe.rules!.permadeath" />
                <span>Permadeath</span>
              </label>
              <label class="rule-toggle">
                <input type="checkbox" [(ngModel)]="universe.rules!.critical_fumbles" />
                <span>Critical Fumbles</span>
              </label>
              <label class="rule-toggle">
                <input type="checkbox" [(ngModel)]="universe.rules!.encumbrance" />
                <span>Encumbrance Tracking</span>
              </label>
            </div>
          </section>
        }

        <!-- Co-write chat -->
        @if (step() === 'cowrite') {
          <section class="step-content">
            <h2>Co-write with AI</h2>
            <p class="step-desc">Chat with the AI to develop your universe's lore and details.</p>
            <div class="chat-box">
              @for (msg of chatMessages(); track $index) {
                <div class="chat-msg" [class.chat-msg--user]="msg.role === 'user'">
                  {{ msg.content }}
                </div>
              }
            </div>
            <form class="chat-form" (ngSubmit)="sendChatMessage()">
              <input [(ngModel)]="chatInput" name="chatInput" class="form-input" placeholder="Ask about your universe..." />
              <button type="submit" class="btn btn--primary" [disabled]="isGenerating()">
                {{ isGenerating() ? '...' : 'Send' }}
              </button>
            </form>
          </section>
        }

        <!-- Lore upload -->
        @if (step() === 'lore') {
          <section class="step-content">
            <h2>Upload Lore Documents</h2>
            <p class="step-desc">Upload existing documents to establish hard canon for your universe.</p>
            <div class="upload-area" (click)="fileInput.click()" (dragover)="$event.preventDefault()" (drop)="onFileDrop($event)">
              <p>Drag files here or click to upload</p>
              <p class="upload-hint">Supports .txt, .md, .pdf</p>
            </div>
            <input #fileInput type="file" (change)="onFileSelect($event)" accept=".txt,.md,.pdf" hidden multiple />
            @if (uploadedFiles().length > 0) {
              <ul class="file-list">
                @for (file of uploadedFiles(); track file.name) {
                  <li class="file-item">
                    <span>{{ file.name }}</span>
                    <button class="file-remove" (click)="removeFile(file)">Remove</button>
                  </li>
                }
              </ul>
            }
          </section>
        }

        <!-- Review -->
        @if (step() === 'review') {
          <section class="step-content">
            <h2>Review Universe</h2>
            <div class="review-card">
              <h3>{{ universe.name || 'Unnamed Universe' }}</h3>
              <p>{{ universe.description }}</p>
              <div class="review-tone">
                @for (slider of toneSliders; track slider.key) {
                  <div class="tone-bar">
                    <span>{{ slider.label }}</span>
                    <div class="tone-bar__track">
                      <div class="tone-bar__fill" [style.width.%]="universe.tone![slider.key]"></div>
                    </div>
                  </div>
                }
              </div>
            </div>
          </section>
        }
      </main>

      <footer class="builder__footer">
        <button class="btn" (click)="prevStep()" [disabled]="step() === 'basics'">Back</button>
        @if (step() !== 'review') {
          <button class="btn btn--primary" (click)="nextStep()">Continue</button>
        } @else {
          <button class="btn btn--primary" (click)="saveUniverse()" [disabled]="isSaving()">
            {{ isSaving() ? 'Saving...' : 'Create Universe' }}
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

    .steps { display: flex; gap: var(--wk-space-xs); padding: var(--wk-space-md); overflow-x: auto; border-bottom: 1px solid var(--wk-border); }
    .step { padding: var(--wk-space-sm) var(--wk-space-md); border: 1px solid var(--wk-border); border-radius: var(--wk-radius-md); background: none; color: var(--wk-text-secondary); cursor: pointer; }
    .step--active { border-color: var(--wk-primary); color: var(--wk-primary); }

    .builder__content { flex: 1; padding: var(--wk-space-lg); overflow-y: auto; }
    .step-content h2 { font-size: 1.25rem; margin: 0 0 var(--wk-space-md); }
    .step-desc { color: var(--wk-text-secondary); margin-bottom: var(--wk-space-md); }

    .form-grid { display: grid; grid-template-columns: 1fr; gap: var(--wk-space-md); max-width: 600px; }
    .form-group { display: flex; flex-direction: column; gap: var(--wk-space-xs); }
    .form-group--full { grid-column: 1 / -1; }
    .form-group label { font-weight: 500; font-size: 0.875rem; }
    .form-input { padding: var(--wk-space-sm); border: 1px solid var(--wk-border); border-radius: var(--wk-radius-md); background: var(--wk-background); color: var(--wk-text-primary); }

    .slider-group { display: flex; align-items: center; gap: var(--wk-space-md); margin-bottom: var(--wk-space-md); }
    .slider-label { width: 120px; font-weight: 500; }
    .slider { flex: 1; accent-color: var(--wk-primary); }
    .slider-value { width: 40px; text-align: right; color: var(--wk-text-secondary); }

    .rules-list { display: flex; flex-direction: column; gap: var(--wk-space-md); }
    .rule-toggle { display: flex; align-items: center; gap: var(--wk-space-sm); cursor: pointer; }
    .rule-toggle input { width: 18px; height: 18px; accent-color: var(--wk-primary); }

    .chat-box { background: var(--wk-surface); border-radius: var(--wk-radius-lg); padding: var(--wk-space-md); min-height: 200px; max-height: 300px; overflow-y: auto; margin-bottom: var(--wk-space-md); }
    .chat-msg { padding: var(--wk-space-sm) var(--wk-space-md); border-radius: var(--wk-radius-md); margin-bottom: var(--wk-space-sm); max-width: 80%; }
    .chat-msg--user { background: var(--wk-primary); margin-left: auto; }
    .chat-msg:not(.chat-msg--user) { background: var(--wk-background); }
    .chat-form { display: flex; gap: var(--wk-space-sm); }
    .chat-form .form-input { flex: 1; }

    .upload-area { border: 2px dashed var(--wk-border); border-radius: var(--wk-radius-lg); padding: var(--wk-space-xl); text-align: center; cursor: pointer; }
    .upload-area:hover { border-color: var(--wk-primary); }
    .upload-hint { font-size: 0.75rem; color: var(--wk-text-muted); }
    .file-list { list-style: none; padding: 0; margin-top: var(--wk-space-md); }
    .file-item { display: flex; justify-content: space-between; padding: var(--wk-space-sm); background: var(--wk-surface); border-radius: var(--wk-radius-md); margin-bottom: var(--wk-space-xs); }
    .file-remove { background: none; border: none; color: var(--wk-error); cursor: pointer; }

    .review-card { background: var(--wk-surface); padding: var(--wk-space-lg); border-radius: var(--wk-radius-lg); }
    .review-card h3 { margin: 0 0 var(--wk-space-sm); }
    .review-card p { color: var(--wk-text-secondary); }
    .review-tone { margin-top: var(--wk-space-lg); }
    .tone-bar { margin-bottom: var(--wk-space-sm); }
    .tone-bar span { font-size: 0.75rem; color: var(--wk-text-muted); }
    .tone-bar__track { height: 8px; background: var(--wk-background); border-radius: 4px; margin-top: 4px; }
    .tone-bar__fill { height: 100%; background: var(--wk-primary); border-radius: 4px; }

    .builder__footer { display: flex; justify-content: space-between; padding: var(--wk-space-md) var(--wk-space-lg); border-top: 1px solid var(--wk-border); background: var(--wk-surface); }
    .btn { padding: var(--wk-space-sm) var(--wk-space-lg); border: 1px solid var(--wk-border); border-radius: var(--wk-radius-md); background: none; color: var(--wk-text-primary); cursor: pointer; }
    .btn:disabled { opacity: 0.5; }
    .btn--primary { background: var(--wk-primary); border-color: var(--wk-primary); }
  `]
})
export class UniverseBuilderComponent implements OnInit {
  private readonly universeService = inject(UniverseService);
  private readonly router = inject(Router);

  id = input<string>();

  readonly steps: Step[] = ['basics', 'tone', 'rules', 'cowrite', 'lore', 'review'];
  readonly stepLabels: Record<Step, string> = {
    basics: 'Basics', tone: 'Tone', rules: 'Rules', cowrite: 'Co-write', lore: 'Lore', review: 'Review'
  };
  readonly toneSliders = [
    { key: 'darkness' as const, label: 'Darkness' },
    { key: 'humor' as const, label: 'Humor' },
    { key: 'realism' as const, label: 'Realism' },
    { key: 'magic_level' as const, label: 'Magic Level' }
  ];

  readonly step = signal<Step>('basics');
  readonly chatMessages = signal<{ role: 'user' | 'assistant'; content: string }[]>([]);
  readonly uploadedFiles = signal<File[]>([]);
  readonly isGenerating = signal(false);
  readonly isSaving = signal(false);

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
}
