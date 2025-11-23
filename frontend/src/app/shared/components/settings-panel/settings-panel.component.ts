import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from '@core/services';
import { UserSettings } from '@core/models';

@Component({
  selector: 'app-settings-panel',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="settings-panel">
      <h3 class="settings-panel__title">Accessibility Settings</h3>

      <div class="setting">
        <label class="setting__label">
          <input
            type="checkbox"
            [ngModel]="lowStimMode()"
            (ngModelChange)="updateSetting('low_stim_mode', $event)"
            class="setting__checkbox"
          />
          <span>Low-stim mode</span>
        </label>
        <p class="setting__description">Reduce visual effects and use muted colors</p>
      </div>

      <div class="setting">
        <label class="setting__label">
          <input
            type="checkbox"
            [ngModel]="conciseRecap()"
            (ngModelChange)="updateSetting('concise_recap', $event)"
            class="setting__checkbox"
          />
          <span>Concise recap</span>
        </label>
        <p class="setting__description">Show shorter turn summaries</p>
      </div>

      <div class="setting">
        <label class="setting__label" for="font-size">Font size</label>
        <select
          id="font-size"
          [ngModel]="fontSize()"
          (ngModelChange)="updateSetting('font_size', $event)"
          class="setting__select"
        >
          <option value="small">Small</option>
          <option value="medium">Medium</option>
          <option value="large">Large</option>
        </select>
      </div>

      <div class="setting">
        <label class="setting__label" for="content-rating">Content rating</label>
        <select
          id="content-rating"
          [ngModel]="contentRating()"
          (ngModelChange)="updateSetting('content_rating', $event)"
          class="setting__select"
        >
          <option value="G">G - General</option>
          <option value="PG">PG - Parental Guidance</option>
          <option value="PG13">PG-13 - Teen</option>
          <option value="R">R - Mature</option>
        </select>
      </div>
    </div>
  `,
  styles: [`
    .settings-panel {
      padding: var(--wk-space-md);
    }

    .settings-panel__title {
      font-size: 1rem;
      font-weight: 600;
      margin: 0 0 var(--wk-space-md);
      color: var(--wk-text-primary);
    }

    .setting {
      margin-bottom: var(--wk-space-md);
      padding-bottom: var(--wk-space-md);
      border-bottom: 1px solid var(--wk-border);
    }

    .setting__label {
      display: flex;
      align-items: center;
      gap: var(--wk-space-sm);
      font-weight: 500;
      color: var(--wk-text-primary);
      cursor: pointer;
    }

    .setting__checkbox {
      width: 18px;
      height: 18px;
      accent-color: var(--wk-primary);
    }

    .setting__description {
      font-size: 0.75rem;
      color: var(--wk-text-secondary);
      margin: var(--wk-space-xs) 0 0;
    }

    .setting__select {
      width: 100%;
      padding: var(--wk-space-sm);
      margin-top: var(--wk-space-xs);
      background-color: var(--wk-background);
      border: 1px solid var(--wk-border);
      border-radius: var(--wk-radius-md);
      color: var(--wk-text-primary);
    }
  `]
})
export class SettingsPanelComponent implements OnInit {
  private readonly authService = inject(AuthService);

  readonly lowStimMode = signal(false);
  readonly conciseRecap = signal(false);
  readonly fontSize = signal<'small' | 'medium' | 'large'>('medium');
  readonly contentRating = signal<'G' | 'PG' | 'PG13' | 'R'>('PG13');

  ngOnInit(): void {
    const settings = this.authService.settings();
    if (settings) {
      this.lowStimMode.set(settings.low_stim_mode);
      this.conciseRecap.set(settings.concise_recap);
      this.fontSize.set(settings.font_size);
      this.contentRating.set(settings.content_rating);
    } else {
      this.authService.loadUserSettings().subscribe(s => {
        this.lowStimMode.set(s.low_stim_mode);
        this.conciseRecap.set(s.concise_recap);
        this.fontSize.set(s.font_size);
        this.contentRating.set(s.content_rating);
      });
    }
  }

  updateSetting(key: keyof UserSettings, value: unknown): void {
    this.authService.updateUserSettings({ [key]: value }).subscribe({
      next: () => {
        if (key === 'low_stim_mode') {
          document.documentElement.setAttribute('data-low-stim', String(value));
        }
        if (key === 'font_size') {
          document.documentElement.setAttribute('data-font-size', String(value));
        }
      }
    });
  }
}
