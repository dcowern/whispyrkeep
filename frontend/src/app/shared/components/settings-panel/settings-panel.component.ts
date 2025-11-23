import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule, Settings, HelpCircle, MoonStar, SunMedium, Accessibility, ShieldHalf, Network } from 'lucide-angular';
import { AuthService } from '@core/services';
import { UserSettings } from '@core/models';

type FontSize = 'small' | 'medium' | 'large';
type LineSpacing = 'standard' | 'roomy' | 'relaxed';
type ContentRating = 'G' | 'PG' | 'PG13' | 'R' | 'NC17';
type UiMode = 'dark' | 'light';

type HelpCopy = {
  accessibility: string;
  low_stim_mode: string;
  concise_recap: string;
  decision_menu_mode: string;
  dyslexia_font: string;
  display: string;
  ui_mode: string;
  font_size: string;
  line_spacing: string;
  safety: string;
  content_rating: string;
  endpoint: string;
  default_endpoint: string;
};

@Component({
  selector: 'app-settings-panel',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule],
  template: `
    <div class="settings-page">
      <header class="settings-hero">
        <div class="hero-icon">
          <lucide-icon [img]="SettingsIcon" />
        </div>
        <div>
          <h1>User Settings</h1>
          <p>Fine-tune accessibility, display, safety, and LLM preferences for every session.</p>
        </div>
      </header>

      @if (error()) {
        <div class="alert alert--error">
          {{ error() }}
        </div>
      }

      @if (isLoading()) {
        <div class="loading">
          <div class="spinner"></div>
          <p>Loading your preferences…</p>
        </div>
      } @else {
        <section class="settings-section">
          <div class="section-header">
            <div class="section-icon section-icon--accent">
              <lucide-icon [img]="AccessibilityIcon" />
            </div>
            <div>
              <h2 class="label-with-help">
                Accessibility
                  <span class="help-trigger">
                    <lucide-icon [img]="HelpCircleIcon" />
                    <span class="tooltip">{{ helpText.accessibility }}</span>
                  </span>
              </h2>
              <p class="section-desc">Neurodiversity-friendly defaults that shape UI pacing and recap detail.</p>
            </div>
          </div>

          <div class="setting-row">
            <div class="setting-copy">
              <span class="label-with-help">
                Low-stim mode
                <span class="help-trigger">
                  <lucide-icon [img]="HelpCircleIcon" />
                  <span class="tooltip">{{ helpText.low_stim_mode }}</span>
                </span>
              </span>
              <p class="setting-desc">Mute animations and strong highlights for calmer play.</p>
            </div>
            <label class="switch">
              <input type="checkbox" [checked]="lowStimMode()" (change)="onToggle('low_stim_mode', $any($event.target).checked)" />
              <span class="switch-slider"></span>
            </label>
          </div>

          <div class="setting-row">
            <div class="setting-copy">
              <span class="label-with-help">
                Concise recap
                <span class="help-trigger">
                  <lucide-icon [img]="HelpCircleIcon" />
                  <span class="tooltip">{{ helpText.concise_recap }}</span>
                </span>
              </span>
              <p class="setting-desc">Shorten turn summaries to reduce reading load.</p>
            </div>
            <label class="switch">
              <input type="checkbox" [checked]="conciseRecap()" (change)="onToggle('concise_recap', $any($event.target).checked)" />
              <span class="switch-slider"></span>
            </label>
          </div>

          <div class="setting-row">
            <div class="setting-copy">
              <span class="label-with-help">
                Decision menu mode
                <span class="help-trigger">
                  <lucide-icon [img]="HelpCircleIcon" />
                  <span class="tooltip">{{ helpText.decision_menu_mode }}</span>
                </span>
              </span>
              <p class="setting-desc">Prefer structured choice lists over open-ended prompts.</p>
            </div>
            <label class="switch">
              <input type="checkbox" [checked]="decisionMenuMode()" (change)="onToggle('decision_menu_mode', $any($event.target).checked)" />
              <span class="switch-slider"></span>
            </label>
          </div>

          <div class="setting-row">
            <div class="setting-copy">
              <span class="label-with-help">
                Dyslexia-friendly font
                <span class="help-trigger">
                  <lucide-icon [img]="HelpCircleIcon" />
                  <span class="tooltip">{{ helpText.dyslexia_font }}</span>
                </span>
              </span>
              <p class="setting-desc">Switch to the dyslexia-friendly typeface.</p>
            </div>
            <label class="switch">
              <input type="checkbox" [checked]="dyslexiaFont()" (change)="onToggle('dyslexia_font', $any($event.target).checked)" />
              <span class="switch-slider"></span>
            </label>
          </div>
        </section>

        <section class="settings-section">
          <div class="section-header">
            <div class="section-icon section-icon--info">
              <lucide-icon [img]="DisplayIcon" />
            </div>
            <div>
              <h2 class="label-with-help">
                Display
                <span class="help-trigger">
                  <lucide-icon [img]="HelpCircleIcon" />
                  <span class="tooltip">{{ helpText.display }}</span>
                </span>
              </h2>
              <p class="section-desc">Control theme, font size, and line spacing across the app.</p>
            </div>
          </div>

          <div class="setting-row">
            <div class="setting-copy">
              <span class="label-with-help">
                Theme
                <span class="help-trigger">
                  <lucide-icon [img]="HelpCircleIcon" />
                  <span class="tooltip">{{ helpText.ui_mode }}</span>
                </span>
              </span>
              <p class="setting-desc">Light boosts contrast in bright rooms; dark reduces eye strain in low light.</p>
            </div>
            <div class="segmented">
              <button class="segment" [class.segment--active]="uiMode() === 'light'" (click)="onSelect('ui_mode', 'light')">
                <lucide-icon [img]="SunIcon" />
                Light
              </button>
              <button class="segment" [class.segment--active]="uiMode() === 'dark'" (click)="onSelect('ui_mode', 'dark')">
                <lucide-icon [img]="MoonIcon" />
                Dark
              </button>
            </div>
          </div>

          <div class="setting-row">
            <div class="setting-copy">
              <span class="label-with-help">
                Font size
                <span class="help-trigger">
                  <lucide-icon [img]="HelpCircleIcon" />
                  <span class="tooltip">{{ helpText.font_size }}</span>
                </span>
              </span>
              <p class="setting-desc">Applies to play view, dashboards, and builders.</p>
            </div>
            <select class="select" [ngModel]="fontSize()" (ngModelChange)="onSelect('font_size', $event)">
              @for (opt of fontSizeOptions; track opt.value) {
                <option [value]="opt.value">{{ opt.label }}</option>
              }
            </select>
          </div>

          <div class="setting-row">
            <div class="setting-copy">
              <span class="label-with-help">
                Line spacing
                <span class="help-trigger">
                  <lucide-icon [img]="HelpCircleIcon" />
                  <span class="tooltip">{{ helpText.line_spacing }}</span>
                </span>
              </span>
              <p class="setting-desc">Looser spacing can reduce crowding and tracking effort.</p>
            </div>
            <select class="select" [ngModel]="lineSpacing()" (ngModelChange)="onSelect('line_spacing', $event)">
              @for (opt of lineSpacingOptions; track opt.value) {
                <option [value]="opt.value">{{ opt.label }}</option>
              }
            </select>
          </div>
        </section>

        <section class="settings-section">
          <div class="section-header">
            <div class="section-icon section-icon--warning">
              <lucide-icon [img]="SafetyIcon" />
            </div>
            <div>
              <h2 class="label-with-help">
                Safety & Content
                <span class="help-trigger">
                  <lucide-icon [img]="HelpCircleIcon" />
                  <span class="tooltip">{{ helpText.safety }}</span>
                </span>
              </h2>
              <p class="section-desc">Gate how intense stories can get; influences LLM prompt safety rails.</p>
            </div>
          </div>

          <div class="setting-row">
            <div class="setting-copy">
              <span class="label-with-help">
                Content rating
                <span class="help-trigger">
                  <lucide-icon [img]="HelpCircleIcon" />
                  <span class="tooltip">{{ helpText.content_rating }}</span>
                </span>
              </span>
              <p class="setting-desc">Sets your default ceiling for violence, horror, and mature themes.</p>
            </div>
            <select class="select" [ngModel]="contentRating()" (ngModelChange)="onSelect('content_rating', $event)">
              @for (opt of ratingOptions; track opt.value) {
                <option [value]="opt.value">{{ opt.label }}</option>
              }
            </select>
          </div>
        </section>

        <section class="settings-section">
          <div class="section-header">
            <div class="section-icon section-icon--info">
              <lucide-icon [img]="EndpointIcon" />
            </div>
            <div>
              <h2 class="label-with-help">
                LLM Endpoint Preference
                <span class="help-trigger">
                  <lucide-icon [img]="HelpCircleIcon" />
                  <span class="tooltip">{{ helpText.endpoint }}</span>
                </span>
              </h2>
              <p class="section-desc">Choose which configured endpoint WhispyrKeep should prefer when generating turns.</p>
            </div>
          </div>

          <div class="setting-row">
            <div class="setting-copy">
              <span class="label-with-help">
                Default endpoint
                <span class="help-trigger">
                  <lucide-icon [img]="HelpCircleIcon" />
                  <span class="tooltip">{{ helpText.default_endpoint }}</span>
                </span>
              </span>
              <p class="setting-desc">Useful if you maintain multiple providers or custom gateways.</p>
            </div>
            <input
              type="text"
              class="input"
              placeholder="e.g., anthropic-default, openai-dev, local-ollama"
              [ngModel]="endpointPref()"
              (ngModelChange)="onSelect('endpoint_pref', $event)"
            />
          </div>
        </section>
      }
    </div>
  `,
  styles: [`
    .settings-page {
      padding: var(--wk-space-6);
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-5);
    }

    .settings-hero {
      display: flex;
      align-items: center;
      gap: var(--wk-space-4);
      background: var(--wk-glass-bg);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-xl);
      padding: var(--wk-space-5);
      box-shadow: var(--wk-shadow-soft);
    }

    .hero-icon {
      width: 56px;
      height: 56px;
      border-radius: 16px;
      background: linear-gradient(135deg, var(--wk-primary), var(--wk-primary-dark));
      display: grid;
      place-items: center;
      color: #fff;
      box-shadow: 0 12px 30px rgba(79, 70, 229, 0.25);
    }

    h1 {
      margin: 0;
      font-size: 1.5rem;
      color: var(--wk-text-primary);
    }

    .settings-section {
      background: var(--wk-surface);
      border: 1px solid var(--wk-border);
      border-radius: var(--wk-radius-xl);
      padding: var(--wk-space-5);
      box-shadow: var(--wk-shadow-soft);
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-4);
    }

    .section-header {
      display: flex;
      gap: var(--wk-space-3);
      align-items: center;
    }

    .section-icon {
      width: 44px;
      height: 44px;
      border-radius: 12px;
      display: grid;
      place-items: center;
      color: #fff;
    }

    .section-icon--accent { background: linear-gradient(135deg, var(--wk-secondary), var(--wk-secondary-dark)); }
    .section-icon--info { background: linear-gradient(135deg, var(--wk-primary), var(--wk-primary-dark)); }
    .section-icon--warning { background: linear-gradient(135deg, var(--wk-accent), #f97316); }

    .section-desc {
      margin: var(--wk-space-1) 0 0;
      color: var(--wk-text-secondary);
      font-size: var(--wk-text-sm);
    }

    .setting-row {
      display: flex;
      justify-content: space-between;
      gap: var(--wk-space-4);
      align-items: center;
      padding: var(--wk-space-4);
      border: 1px solid var(--wk-border);
      border-radius: var(--wk-radius-lg);
      background: var(--wk-glass-bg);
    }

    .setting-copy {
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-1);
      color: var(--wk-text-primary);
    }

    .setting-desc {
      margin: 0;
      color: var(--wk-text-secondary);
      font-size: var(--wk-text-sm);
    }

    .switch {
      position: relative;
      display: inline-block;
      width: 52px;
      height: 28px;
    }

    .switch input {
      opacity: 0;
      width: 0;
      height: 0;
    }

    .switch-slider {
      position: absolute;
      cursor: pointer;
      inset: 0;
      background-color: var(--wk-border-strong);
      border-radius: 999px;
      transition: all var(--wk-transition-fast);
    }

    .switch-slider::before {
      position: absolute;
      content: '';
      height: 22px;
      width: 22px;
      left: 3px;
      bottom: 3px;
      background-color: white;
      border-radius: 50%;
      transition: all var(--wk-transition-fast);
      box-shadow: 0 4px 10px rgba(0, 0, 0, 0.12);
    }

    .switch input:checked + .switch-slider {
      background-color: var(--wk-primary);
    }

    .switch input:checked + .switch-slider::before {
      transform: translateX(24px);
    }

    .segmented {
      display: inline-flex;
      background: var(--wk-surface-2);
      border: 1px solid var(--wk-border);
      border-radius: var(--wk-radius-lg);
      overflow: hidden;
    }

    .segment {
      border: none;
      background: transparent;
      color: var(--wk-text-secondary);
      padding: var(--wk-space-2) var(--wk-space-3);
      display: inline-flex;
      align-items: center;
      gap: var(--wk-space-2);
      cursor: pointer;
      transition: background var(--wk-transition-fast), color var(--wk-transition-fast);
    }

    .segment--active {
      background: var(--wk-primary-soft);
      color: var(--wk-primary-dark);
    }

    .select, .input {
      min-width: 220px;
      padding: var(--wk-space-2) var(--wk-space-3);
      border: 1px solid var(--wk-border);
      border-radius: var(--wk-radius-md);
      background: var(--wk-surface-2);
      color: var(--wk-text-primary);
    }

    /* Match tooltip styling used across builders */
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

    .label-with-help {
      display: inline-flex;
      align-items: center;
      gap: var(--wk-space-1);
      font-weight: var(--wk-font-semibold);
      color: var(--wk-text-primary);
    }

    .alert {
      padding: var(--wk-space-3) var(--wk-space-4);
      border-radius: var(--wk-radius-lg);
      border: 1px solid var(--wk-border);
    }

    .alert--error {
      border-color: var(--wk-error-border, #fda4af);
      background: #fff1f2;
      color: #b91c1c;
    }

    .loading {
      display: grid;
      gap: var(--wk-space-2);
      justify-items: start;
      color: var(--wk-text-secondary);
    }

    .spinner {
      width: 28px;
      height: 28px;
      border: 3px solid var(--wk-border);
      border-top-color: var(--wk-primary);
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    @media (max-width: 900px) {
      .settings-section, .setting-row {
        padding: var(--wk-space-3);
      }

      .setting-row {
        flex-direction: column;
        align-items: flex-start;
      }

      .select, .input, .segmented {
        width: 100%;
      }
    }
  `]
})
export class SettingsPanelComponent implements OnInit {
  private readonly authService = inject(AuthService);

  readonly SettingsIcon = Settings;
  readonly HelpCircleIcon = HelpCircle;
  readonly AccessibilityIcon = Accessibility;
  readonly DisplayIcon = MoonStar;
  readonly SafetyIcon = ShieldHalf;
  readonly EndpointIcon = Network;
  readonly SunIcon = SunMedium;
  readonly MoonIcon = MoonStar;

  readonly lowStimMode = signal(false);
  readonly conciseRecap = signal(false);
  readonly decisionMenuMode = signal(false);
  readonly dyslexiaFont = signal(false);
  readonly fontSize = signal<FontSize>('medium');
  readonly lineSpacing = signal<LineSpacing>('standard');
  readonly contentRating = signal<ContentRating>('PG13');
  readonly uiMode = signal<UiMode>('dark');
  readonly endpointPref = signal<string>('');

  readonly isLoading = signal(true);
  readonly isSaving = signal(false);
  readonly error = signal<string | null>(null);

  readonly fontSizeOptions = [
    { value: 'small', label: 'Small' },
    { value: 'medium', label: 'Medium (default)' },
    { value: 'large', label: 'Large' }
  ];

  readonly lineSpacingOptions = [
    { value: 'standard', label: 'Standard' },
    { value: 'roomy', label: 'Roomy' },
    { value: 'relaxed', label: 'Relaxed' }
  ];

  readonly ratingOptions = [
    { value: 'G', label: 'G — General' },
    { value: 'PG', label: 'PG — Parental Guidance' },
    { value: 'PG13', label: 'PG-13 — Teen' },
    { value: 'R', label: 'R — Mature' },
    { value: 'NC17', label: 'NC-17 — Adults only' }
  ];

  readonly helpText: HelpCopy = {
    accessibility: 'Global defaults that reduce overstimulation and streamline text. Applied across dashboards, play sessions, and setup flows.',
    low_stim_mode: 'Dials back visual effects and bright accents to keep the interface calmer. Great for long sessions or sensitive displays.',
    concise_recap: 'Shorter turn summaries to reduce reading load. Full detail remains available in the log if you need it.',
    decision_menu_mode: 'When possible, prefer structured option lists over open-ended prompts to ease decision fatigue.',
    dyslexia_font: 'Switches to a dyslexia-friendly typeface to improve character distinction and reduce visual noise.',
    display: 'Theme, sizing, and spacing changes cascade to play, builders, and logs.',
    ui_mode: 'Light mode favors bright spaces; dark mode softens glare at night. Applies to the entire app shell.',
    font_size: 'Adjust base font size across navigation, play view, and builders.',
    line_spacing: 'Extra spacing can improve readability for dense descriptions and logs.',
    safety: 'Sets the default ceiling for content intensity and feeds into prompt safety rails.',
    content_rating: 'G/PG keep things mild; PG-13 allows moderate peril; R permits graphic themes; NC-17 allows explicit mature content. Campaigns may still enforce stricter limits.',
    endpoint: 'If you have multiple configured providers, pick the one WhispyrKeep should prefer by default.',
    default_endpoint: 'Identifier or nickname of your preferred endpoint (e.g., "openai-prod", "anthropic-default").'
  };

  ngOnInit(): void {
    const cached = this.authService.settings();
    if (cached) {
      this.applySettings(cached);
      this.applyDomFlags();
      this.isLoading.set(false);
    } else {
      this.fetchSettings();
    }
  }

  private fetchSettings(): void {
    this.isLoading.set(true);
    this.error.set(null);
    this.authService.loadUserSettings().subscribe({
      next: settings => {
        this.applySettings(settings);
        this.applyDomFlags();
        this.isLoading.set(false);
      },
      error: () => {
        this.error.set('Unable to load settings. Please try again.');
        this.isLoading.set(false);
      }
    });
  }

  private applySettings(settings: Partial<UserSettings>): void {
    const nd = (settings as any).nd_options || {};
    const safety = (settings as any).safety_defaults || {};

    this.lowStimMode.set(nd.low_stim_mode ?? (settings as any).low_stim_mode ?? false);
    this.conciseRecap.set(nd.concise_recap ?? (settings as any).concise_recap ?? false);
    this.decisionMenuMode.set(nd.decision_menu_mode ?? (settings as any).decision_menu_mode ?? false);
    this.dyslexiaFont.set(nd.dyslexia_font ?? (settings as any).dyslexia_font ?? false);
    this.fontSize.set(nd.font_size ?? (settings as any).font_size ?? 'medium');
    this.lineSpacing.set(nd.line_spacing ?? (settings as any).line_spacing ?? 'standard');
    this.contentRating.set(safety.content_rating ?? (settings as any).content_rating ?? 'PG13');
    this.uiMode.set((settings as any).ui_mode ?? 'dark');
    this.endpointPref.set((settings as any).endpoint_pref ?? '');
  }

  private applyDomFlags(): void {
    document.documentElement.setAttribute('data-low-stim', String(this.lowStimMode()));
    document.documentElement.setAttribute('data-font-size', String(this.fontSize()));
  }

  onToggle(key: keyof UserSettings, value: boolean): void {
    this.updateSetting(key, value);
  }

  onSelect<T extends keyof UserSettings>(key: T, value: UserSettings[T]): void {
    this.updateSetting(key, value);
  }

  private updateSetting(key: keyof UserSettings, value: unknown): void {
    this.isSaving.set(true);
    this.error.set(null);
    this.authService.updateUserSettings({ [key]: value }).subscribe({
      next: updated => {
        this.applySettings(updated);
        this.applyDomFlags();
      },
      error: () => {
        this.error.set('Failed to save setting. Please retry.');
      },
      complete: () => this.isSaving.set(false)
    });
  }
}
