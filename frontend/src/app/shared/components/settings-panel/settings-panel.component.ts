import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule, Settings, HelpCircle, MoonStar, SunMedium, Accessibility, ShieldHalf, Network } from 'lucide-angular';
import { AuthService, LlmEndpointService } from '@core/services';
import { EndpointPreference, LlmCompatibility, LlmModelListRequest, LlmProvider, LlmValidationRequest, UserSettings } from '@core/models';

type FontSize = 'small' | 'medium' | 'large';
type LineSpacing = 'standard' | 'roomy' | 'relaxed';
type ContentRating = 'G' | 'PG' | 'PG13' | 'R' | 'NC17';
type UiMode = 'dark' | 'light';
type ModelMode = 'api' | 'custom';

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
  api_key: string;
  provider: string;
  compatibility: string;
  base_url: string;
  api_models: string;
  custom_model: string;
  max_tokens: string;
  temperature: string;
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

          <div class="setting-row setting-row--stacked">
            <div class="setting-copy">
              <span class="label-with-help">
                Default endpoint
                <span class="help-trigger">
                  <lucide-icon [img]="HelpCircleIcon" />
                  <span class="tooltip">{{ helpText.default_endpoint }}</span>
                </span>
              </span>
              <p class="setting-desc">Provide a key, pick a provider, load models, then verify before saving.</p>
            </div>

            <div class="endpoint-grid">
              <div class="field field--wide">
                <label class="form-label label-with-help" for="endpoint-api-key">
                  API key
                  <span class="help-trigger">
                    <lucide-icon [img]="HelpCircleIcon" />
                    <span class="tooltip">{{ helpText.api_key }}</span>
                  </span>
                </label>
                <input
                  id="endpoint-api-key"
                  type="password"
                  class="input"
                  placeholder="sk-..."
                  [ngModel]="endpointApiKey()"
                  (ngModelChange)="onApiKeyChange($event)"
                />
                <p class="hint">Required for OpenAI, Anthropic, Meta, Mistral, and Google. Optional for custom gateways.</p>
              </div>

              <div class="field">
                <label class="form-label label-with-help" for="endpoint-provider">
                  Provider
                  <span class="help-trigger">
                    <lucide-icon [img]="HelpCircleIcon" />
                    <span class="tooltip">{{ helpText.provider }}</span>
                  </span>
                </label>
                <select id="endpoint-provider" class="select" [ngModel]="endpointProvider()" (ngModelChange)="onEndpointProviderChange($any($event))">
                  @for (provider of providerOptions; track provider.value) {
                    <option [value]="provider.value">{{ provider.label }}</option>
                  }
                </select>
              </div>

              <div class="field">
                <label class="form-label label-with-help">
                  Compatibility
                  <span class="help-trigger">
                    <lucide-icon [img]="HelpCircleIcon" />
                    <span class="tooltip">{{ helpText.compatibility }}</span>
                  </span>
                </label>
                @if (endpointProvider() === 'custom') {
                  <select class="select" [ngModel]="endpointCompatibility()" (ngModelChange)="onEndpointCompatibilityChange($any($event))">
                    <option value="openai">OpenAI-compatible</option>
                    <option value="anthropic">Anthropic-compatible</option>
                  </select>
                } @else {
                  <span class="badge">{{ compatibilityLabels[endpointCompatibility()] }}</span>
                }
              </div>

              <div class="field field--wide">
                <label class="form-label label-with-help" for="endpoint-base">
                  Base URL
                  <span class="help-trigger">
                    <lucide-icon [img]="HelpCircleIcon" />
                    <span class="tooltip">{{ helpText.base_url }}</span>
                  </span>
                </label>
                <input
                  id="endpoint-base"
                  type="text"
                  class="input"
                  [disabled]="endpointProvider() !== 'custom'"
                  [ngModel]="endpointBaseUrl()"
                  (ngModelChange)="onEndpointBaseChange($event)"
                  placeholder="https://api.your-gateway.com/v1"
                />
                <p class="hint">We auto-fill well-known providers. Custom gateways stay editable.</p>
              </div>

              <div class="model-card">
                <div class="model-modes">
                  <label class="radio label-with-help">
                    <input
                      type="radio"
                      name="model-mode"
                      value="api"
                      [checked]="endpointModelMode() === 'api'"
                      (change)="onModelModeChange('api')"
                    />
                    API-provided models
                    <span class="help-trigger">
                      <lucide-icon [img]="HelpCircleIcon" />
                      <span class="tooltip">{{ helpText.api_models }}</span>
                    </span>
                  </label>
                  <label class="radio label-with-help">
                    <input
                      type="radio"
                      name="model-mode"
                      value="custom"
                      [checked]="endpointModelMode() === 'custom'"
                      (change)="onModelModeChange('custom')"
                    />
                    Custom model name
                    <span class="help-trigger">
                      <lucide-icon [img]="HelpCircleIcon" />
                      <span class="tooltip">{{ helpText.custom_model }}</span>
                    </span>
                  </label>
                </div>

                @if (endpointModelMode() === 'api') {
                  <div class="field">
                    <label class="form-label" for="api-model-select">Available models</label>
                    <div class="model-row">
                      @if (endpointModels().length) {
                        <select id="api-model-select" class="select" [disabled]="isFetchingModels()" [ngModel]="endpointModel()" (ngModelChange)="onEndpointModelSelect($event)">
                          @for (model of endpointModels(); track model) {
                            <option [value]="model">{{ model }}</option>
                          }
                        </select>
                      } @else {
                      <p class="hint">Add an API key to pull available models for this provider.</p>
                      }
                      <button type="button" class="btn btn-ghost" (click)="refreshModels()" [disabled]="isFetchingModels() || requiresApiKey() && !endpointApiKey().trim()">
                        @if (isFetchingModels()) { Refreshing… } @else { Fetch models }
                      </button>
                    </div>
                  </div>
                } @else {
                  <div class="field">
                    <label class="form-label label-with-help" for="manual-model">
                      Model name
                      <span class="help-trigger">
                        <lucide-icon [img]="HelpCircleIcon" />
                        <span class="tooltip">{{ helpText.custom_model }}</span>
                      </span>
                    </label>
                    <input
                      id="manual-model"
                      type="text"
                      class="input"
                      placeholder="e.g., gpt-4o, claude-3-opus, llama3-70b"
                      [ngModel]="endpointManualModel()"
                      (ngModelChange)="onManualModelInput($event)"
                    />
                    <p class="hint">Use this if the endpoint does not support listing models or you prefer a specific one.</p>
                  </div>
                }

                <div class="field field--toggle-row">
                  <label class="toggle label-with-help">
                    <input type="checkbox" [checked]="endpointMaxTokensEnabled()" (change)="onMaxTokensToggle($any($event.target).checked)" />
                    <span>Send max_tokens</span>
                    <span class="help-trigger">
                      <lucide-icon [img]="HelpCircleIcon" />
                      <span class="tooltip">{{ helpText.max_tokens }}</span>
                    </span>
                  </label>
                  @if (endpointMaxTokensEnabled()) {
                    <input
                      type="number"
                      min="1"
                      class="input input--compact"
                      [ngModel]="endpointMaxTokens() ?? 256"
                      (ngModelChange)="endpointMaxTokens.set($any($event))"
                    />
                  }
                </div>

                <div class="field field--toggle-row">
                  <label class="toggle label-with-help">
                    <input type="checkbox" [checked]="endpointTemperatureEnabled()" (change)="onTemperatureToggle($any($event.target).checked)" />
                    <span>Send temperature</span>
                    <span class="help-trigger">
                      <lucide-icon [img]="HelpCircleIcon" />
                      <span class="tooltip">{{ helpText.temperature }}</span>
                    </span>
                  </label>
                  @if (endpointTemperatureEnabled()) {
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      class="input input--compact"
                      [ngModel]="endpointTemperature() ?? 0.7"
                      (ngModelChange)="endpointTemperature.set($any($event))"
                    />
                  }
                </div>
              </div>

              <div class="endpoint-actions">
                <button
                  class="btn btn-primary"
                  type="button"
                  (click)="saveEndpointPreference()"
                  [disabled]="isTestingEndpoint() || isSaving()"
                >
                  @if (isTestingEndpoint()) { Testing… } @else { Test & Save preference }
                </button>
              </div>

              <div class="endpoint-messages">
                @if (isFetchingModels()) {
                  <div class="endpoint-status endpoint-status--info">Loading models…</div>
                }
                @if (endpointStatus()) {
                  <div class="endpoint-status endpoint-status--ok">{{ endpointStatus() }}</div>
                }
                @if (endpointError()) {
                  <div class="endpoint-status endpoint-status--error">{{ endpointError() }}</div>
                }
              </div>
            </div>
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

    .setting-row--stacked {
      align-items: stretch;
      flex-direction: column;
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
      background: var(--wk-surface);
      color: var(--wk-text-primary);
    }

    .select option {
      color: var(--wk-text-primary);
      background: var(--wk-surface);
    }

    .endpoint-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: var(--wk-space-4);
      width: 100%;
    }

    .field--wide { grid-column: 1 / -1; }

    .field {
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-2);
    }

    .form-label {
      font-weight: var(--wk-font-semibold);
      color: var(--wk-text-primary);
    }

    .hint {
      margin: 0;
      color: var(--wk-text-muted);
      font-size: var(--wk-text-xs);
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: var(--wk-space-2);
      padding: 6px 10px;
      border-radius: var(--wk-radius-md);
      background: var(--wk-surface-2);
      border: 1px solid var(--wk-border);
      color: var(--wk-text-secondary);
      font-size: var(--wk-text-sm);
    }

    .model-card {
      grid-column: 1 / -1;
      border: 1px solid var(--wk-border);
      border-radius: var(--wk-radius-lg);
      background: var(--wk-surface-2);
      padding: var(--wk-space-3);
      display: grid;
      gap: var(--wk-space-3);
    }

    .model-modes {
      display: flex;
      gap: var(--wk-space-4);
      flex-wrap: wrap;
    }

    .radio {
      display: inline-flex;
      align-items: center;
      gap: var(--wk-space-2);
      font-weight: var(--wk-font-medium);
      color: var(--wk-text-primary);
    }

    .field--toggle-row {
      display: grid;
      grid-template-columns: auto 1fr;
      gap: var(--wk-space-3);
      align-items: center;
    }

    .model-row {
      display: flex;
      gap: var(--wk-space-2);
      align-items: center;
      flex-wrap: wrap;
    }

    .toggle {
      display: inline-flex;
      align-items: center;
      gap: var(--wk-space-2);
      font-weight: var(--wk-font-medium);
    }

    .input--compact {
      max-width: 140px;
      min-width: 120px;
    }

    .input:disabled {
      opacity: 0.7;
      cursor: not-allowed;
    }

    .endpoint-actions {
      display: flex;
      gap: var(--wk-space-2);
      align-items: center;
      flex-wrap: wrap;
      justify-content: flex-end;
      grid-column: 1 / -1;
    }

    .btn {
      border: 1px solid var(--wk-border);
      background: var(--wk-surface-2);
      color: var(--wk-text-primary);
      padding: var(--wk-space-2) var(--wk-space-3);
      border-radius: var(--wk-radius-md);
      cursor: pointer;
      transition: all var(--wk-transition-fast);
    }

    .btn:hover:not(:disabled) {
      border-color: var(--wk-primary);
      color: var(--wk-primary);
      box-shadow: 0 0 0 1px var(--wk-primary-soft);
    }

    .btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .btn-primary {
      background: var(--wk-primary);
      color: #fff;
      border-color: var(--wk-primary);
      box-shadow: 0 10px 30px rgba(79, 70, 229, 0.2);
    }

    .btn-primary:hover:not(:disabled) {
      background: var(--wk-primary-dark);
      border-color: var(--wk-primary-dark);
    }

    .endpoint-messages {
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-2);
      grid-column: 1 / -1;
    }

    .endpoint-status {
      padding: var(--wk-space-2) var(--wk-space-3);
      border-radius: var(--wk-radius-md);
      border: 1px solid var(--wk-border);
      font-size: var(--wk-text-sm);
    }

    .endpoint-status--ok {
      border-color: #22c55e33;
      background: #ecfdf3;
      color: #15803d;
    }

    .endpoint-status--info {
      border-color: var(--wk-border);
      background: var(--wk-surface-2);
      color: var(--wk-text-secondary);
    }

    .endpoint-status--error {
      border-color: #fda4af;
      background: #fff1f2;
      color: #b91c1c;
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
  private readonly llmEndpointService = inject(LlmEndpointService);

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
  readonly endpointProvider = signal<LlmProvider>('openai');
  readonly endpointBaseUrl = signal<string>('https://api.openai.com/v1');
  readonly endpointCompatibility = signal<LlmCompatibility>('openai');
  readonly endpointApiKey = signal<string>('');
  readonly endpointModelMode = signal<ModelMode>('api');
  readonly endpointMaxTokensEnabled = signal(false);
  readonly endpointMaxTokens = signal<number | null>(null);
  readonly endpointTemperatureEnabled = signal(false);
  readonly endpointTemperature = signal<number | null>(null);
  readonly endpointModels = signal<string[]>([]);
  readonly endpointModel = signal<string>('');
  readonly endpointManualModel = signal<string>('');
  readonly endpointStatus = signal<string | null>(null);
  readonly endpointError = signal<string | null>(null);
  readonly isFetchingModels = signal(false);
  readonly isTestingEndpoint = signal(false);

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

  readonly providerOptions: { value: LlmProvider; label: string }[] = [
    { value: 'openai', label: 'OpenAI' },
    { value: 'anthropic', label: 'Anthropic' },
    { value: 'meta', label: 'Meta (Llama)' },
    { value: 'mistral', label: 'Mistral' },
    { value: 'google', label: 'Google' },
    { value: 'custom', label: 'Custom URL' }
  ];

  readonly providerBaseMap: Record<LlmProvider, string> = {
    openai: 'https://api.openai.com/v1',
    anthropic: 'https://api.anthropic.com',
    meta: 'https://api.meta.com/v1',
    mistral: 'https://api.mistral.ai/v1',
    google: 'https://generativelanguage.googleapis.com/v1beta',
    custom: ''
  };

  readonly providerCompatibilityMap: Record<LlmProvider, LlmCompatibility> = {
    openai: 'openai',
    anthropic: 'anthropic',
    meta: 'openai',
    mistral: 'openai',
    google: 'google',
    custom: 'openai'
  };

  readonly compatibilityLabels: Record<LlmCompatibility, string> = {
    openai: 'OpenAI-compatible',
    anthropic: 'Anthropic-compatible',
    google: 'Google Generative API'
  };

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
    endpoint: 'Pick a provider or custom gateway, fetch available models, and verify the connection before saving.',
    default_endpoint: 'We map well-known brands to their URLs automatically. Custom gateways let you choose OpenAI- or Anthropic-compatible APIs.',
    api_key: 'Stored securely on the server and used for backend calls. Required for hosted providers; optional for custom gateways.',
    provider: 'Choose a branded provider or a custom gateway. We auto-fill URLs and compatibility for known brands.',
    compatibility: 'Protocol shape the endpoint speaks. Custom gateways often mimic OpenAI or Anthropic schemas.',
    base_url: 'Root URL for the API. Locked for known providers; editable for custom gateways.',
    api_models: 'Uses the provider’s model listing to populate choices. Requires an API key for hosted providers.',
    custom_model: 'Type an exact model name if listing fails or you prefer a specific deployment.',
    max_tokens: 'Optional completion cap sent during validation. Leave off if the provider expects a different parameter.',
    temperature: 'Optional randomness control. Leave off to use the provider default.'
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
    this.applyEndpointPreference((settings as any).endpoint_pref as EndpointPreference | string | undefined);
  }

  private applyEndpointPreference(pref: EndpointPreference | string | undefined): void {
    const provider: LlmProvider = (pref as EndpointPreference)?.provider ||
      (typeof pref === 'string' ? 'custom' : 'openai');

    this.endpointProvider.set(provider);
    const baseUrl = (pref as EndpointPreference)?.base_url || this.providerBaseMap[provider] || '';
    this.endpointBaseUrl.set(baseUrl);

    const compatibility = (pref as EndpointPreference)?.compatibility || this.providerCompatibilityMap[provider];
    this.endpointCompatibility.set(compatibility);

    const modelValue = typeof pref === 'object' && pref ? pref.model || '' : typeof pref === 'string' ? pref : '';
    const manualPreferred = typeof pref === 'object' && !!(pref as EndpointPreference)?.manual;
    this.endpointModel.set(manualPreferred ? '' : modelValue);
    this.endpointManualModel.set(manualPreferred ? modelValue : '');
    this.endpointModelMode.set(manualPreferred || provider === 'custom' ? 'custom' : 'api');
    this.endpointMaxTokensEnabled.set(!!(pref as EndpointPreference)?.max_tokens);
    this.endpointMaxTokens.set((pref as EndpointPreference)?.max_tokens ?? null);
    this.endpointTemperatureEnabled.set(!!(pref as EndpointPreference)?.temperature);
    this.endpointTemperature.set((pref as EndpointPreference)?.temperature ?? null);

    this.endpointModels.set([]);
    this.endpointStatus.set(null);
    this.endpointError.set(null);
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

  onEndpointProviderChange(provider: LlmProvider): void {
    this.endpointProvider.set(provider);
    this.endpointBaseUrl.set(this.providerBaseMap[provider] || '');
    this.endpointCompatibility.set(this.providerCompatibilityMap[provider]);
    this.endpointModels.set([]);
    this.endpointModel.set('');
    this.endpointManualModel.set('');
    this.endpointModelMode.set(provider === 'custom' ? 'custom' : 'api');
    this.endpointMaxTokensEnabled.set(false);
    this.endpointMaxTokens.set(null);
    this.endpointTemperatureEnabled.set(false);
    this.endpointTemperature.set(null);
    this.endpointStatus.set(null);
    this.endpointError.set(null);

    if (this.endpointModelMode() === 'api' && (this.endpointApiKey().trim() || !this.requiresApiKey())) {
      this.loadModels();
    } else if (this.requiresApiKey()) {
      this.endpointStatus.set('Enter an API key to load provider models.');
    }
  }

  onEndpointCompatibilityChange(value: LlmCompatibility): void {
    this.endpointCompatibility.set(value);
    this.endpointStatus.set(null);
    this.endpointError.set(null);
  }

  onEndpointBaseChange(value: string): void {
    this.endpointBaseUrl.set(value);
    this.endpointStatus.set(null);
    this.endpointError.set(null);
  }

  onEndpointModelSelect(value: string): void {
    this.endpointModel.set(value);
    this.endpointManualModel.set('');
    this.endpointModelMode.set('api');
    this.endpointStatus.set(null);
  }

  onManualModelInput(value: string): void {
    this.endpointManualModel.set(value);
    this.endpointModelMode.set('custom');
    this.endpointStatus.set(null);
  }

  onMaxTokensToggle(enabled: boolean): void {
    this.endpointMaxTokensEnabled.set(enabled);
    if (!enabled) {
      this.endpointMaxTokens.set(null);
    } else if (!this.endpointMaxTokens()) {
      this.endpointMaxTokens.set(4096);
    }
  }

  onTemperatureToggle(enabled: boolean): void {
    this.endpointTemperatureEnabled.set(enabled);
    if (!enabled) {
      this.endpointTemperature.set(null);
    } else if (this.endpointTemperature() === null) {
      this.endpointTemperature.set(0.7);
    }
  }

  onApiKeyChange(value: string): void {
    this.endpointApiKey.set(value);
    this.endpointStatus.set(null);
    this.endpointError.set(null);

    if (this.endpointModelMode() === 'api' && (value.trim() || !this.requiresApiKey())) {
      this.endpointModelMode.set('api');
      this.loadModels();
    }
  }

  onModelModeChange(mode: ModelMode): void {
    this.endpointModelMode.set(mode);
    this.endpointStatus.set(null);
    this.endpointError.set(null);

    if (mode === 'api' && this.endpointModels().length === 0) {
      if (this.endpointApiKey().trim() || !this.requiresApiKey()) {
        this.loadModels();
      } else if (this.requiresApiKey()) {
        this.endpointStatus.set('Enter an API key to load provider models.');
      }
    }
  }

  private loadModels(): void {
    const baseUrl = this.endpointBaseUrl().trim();
    if (!baseUrl) {
      this.endpointError.set('Base URL is required to load models.');
      return;
    }

    const apiKey = this.endpointApiKey().trim();
    if (this.requiresApiKey() && !apiKey) {
      this.endpointStatus.set('Enter an API key to load provider models.');
      return;
    }

    this.endpointError.set(null);
    this.endpointStatus.set('Loading models…');
    this.isFetchingModels.set(true);

    const payload = this.buildEndpointPayload();
    payload.api_key = apiKey || undefined;
    payload.base_url = baseUrl;

    this.llmEndpointService.listModels(payload).subscribe({
      next: response => {
        const models = response.models || [];
        this.endpointModels.set(models);
        const current = this.endpointModel();
        const firstModel = current && models.includes(current) ? current : models[0] ?? '';
        this.endpointModel.set(firstModel);
        this.endpointCompatibility.set(response.compatibility);
        this.endpointBaseUrl.set(response.resolved_base_url || this.endpointBaseUrl());
        this.endpointModelMode.set('api');
        this.endpointStatus.set(`Fetched ${models.length} model(s) from the provider.`);
      },
      error: err => {
        const detail = err?.error?.detail || err?.error?.message || 'Unable to fetch models from the endpoint.';
        this.endpointError.set(detail);
        this.endpointModels.set([]);
      },
      complete: () => this.isFetchingModels.set(false)
    });
  }

  saveEndpointPreference(): void {
    const payload = this.buildEndpointPayload(true);

    if (this.requiresApiKey() && !this.endpointApiKey().trim()) {
      this.endpointError.set('API key is required for this provider.');
      return;
    }

    const chosenModel = this.endpointModelMode() === 'api'
      ? this.endpointModel().trim()
      : this.endpointManualModel().trim();

    this.endpointStatus.set(null);
    this.endpointError.set(null);

    if (!chosenModel) {
      this.endpointError.set('Select a model from the list or enter one manually.');
      return;
    }

    this.isTestingEndpoint.set(true);
    payload.api_key = this.endpointApiKey().trim();
    payload.model = chosenModel;
    if (this.endpointMaxTokensEnabled() && this.endpointMaxTokens()) {
      payload.max_tokens = this.endpointMaxTokens() ?? undefined;
    }
    if (this.endpointTemperatureEnabled() && this.endpointTemperature() !== null) {
      payload.temperature = this.endpointTemperature() ?? undefined;
    }

    this.llmEndpointService.validate(payload).subscribe({
      next: response => {
        const models = response.models && response.models.length ? response.models : (this.endpointModels().length ? this.endpointModels() : [chosenModel]);
        this.endpointModels.set(models);
        if (models.length && !models.includes(chosenModel)) {
          this.endpointModel.set(models[0]);
        }
        const preference: EndpointPreference = {
          provider: this.endpointProvider(),
          base_url: response.resolved_base_url || this.endpointBaseUrl(),
          compatibility: response.compatibility,
          model: chosenModel,
          manual: this.endpointModelMode() === 'custom',
          max_tokens: this.endpointMaxTokensEnabled() ? this.endpointMaxTokens() ?? undefined : undefined,
          temperature: this.endpointTemperatureEnabled() ? this.endpointTemperature() ?? undefined : undefined,
        };

        this.endpointStatus.set(response.message || 'Endpoint verified and saved.');
        this.updateSetting('endpoint_pref', preference, () => {
          this.endpointModels.set(models);
          this.endpointModel.set(chosenModel);
          this.endpointStatus.set(response.message || 'Endpoint verified and saved.');
        });
      },
      error: err => {
        const detail = err?.error?.message || err?.error?.detail || 'Unable to verify this endpoint. Check URL, compatibility, and credentials.';
        this.endpointError.set(detail);
      },
      complete: () => this.isTestingEndpoint.set(false)
    });
  }

  private buildEndpointPayload(): LlmModelListRequest;
  private buildEndpointPayload(includeModel: true): LlmValidationRequest;
  private buildEndpointPayload(includeModel = false): LlmModelListRequest | LlmValidationRequest {
    const payload: LlmModelListRequest | LlmValidationRequest = {
      provider: this.endpointProvider(),
      base_url: this.endpointBaseUrl().trim(),
      compatibility: this.endpointCompatibility(),
      api_key: this.endpointApiKey().trim() || undefined
    };

    if (includeModel) {
      (payload as LlmValidationRequest).model = this.endpointModelMode() === 'api'
        ? this.endpointModel()
        : this.endpointManualModel().trim();
      if (this.endpointMaxTokensEnabled() && this.endpointMaxTokens()) {
        (payload as LlmValidationRequest).max_tokens = this.endpointMaxTokens() ?? undefined;
      }
      if (this.endpointTemperatureEnabled() && this.endpointTemperature() !== null) {
        (payload as LlmValidationRequest).temperature = this.endpointTemperature() ?? undefined;
      }
    }

    return payload;
  }

  private isCustomProvider(): boolean {
    return this.endpointProvider() === 'custom';
  }

  requiresApiKey(): boolean {
    return !this.isCustomProvider();
  }

  refreshModels(): void {
    this.endpointStatus.set(null);
    this.endpointError.set(null);
    this.endpointModelMode.set('api');
    this.loadModels();
  }

  private updateSetting(key: keyof UserSettings, value: unknown, onSuccess?: (settings: UserSettings) => void): void {
    this.isSaving.set(true);
    this.error.set(null);
    this.authService.updateUserSettings({ [key]: value }).subscribe({
      next: updated => {
        this.applySettings(updated);
        this.applyDomFlags();
        if (onSuccess) {
          onSuccess(updated);
        }
      },
      error: () => {
        this.error.set('Failed to save setting. Please retry.');
      },
      complete: () => this.isSaving.set(false)
    });
  }
}
