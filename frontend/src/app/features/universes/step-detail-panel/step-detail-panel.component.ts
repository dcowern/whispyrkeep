import {
  Component,
  Input,
  Output,
  EventEmitter,
  computed,
  signal,
  inject,
  OnChanges,
  SimpleChanges
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  LucideAngularModule,
  X,
  Check,
  AlertCircle,
  Sparkles,
  Wand2,
  Maximize2,
  Loader2
} from 'lucide-angular';
import { WorldgenStepName, WorldgenDraftData, WorldgenStepStatus } from '@core/models';
import { WorldgenService, WORLDGEN_STEPS } from '@core/services/worldgen.service';

interface FieldConfig {
  name: string;
  label: string;
  type: 'text' | 'textarea' | 'number' | 'slider' | 'boolean' | 'radio-boolean' | 'tags' | 'section';
  required?: boolean;
  min?: number;
  max?: number;
  placeholder?: string;
  description?: string;
  trueLabel?: string;   // For radio-boolean: label when true
  falseLabel?: string;  // For radio-boolean: label when false
}

const STEP_FIELDS: Record<WorldgenStepName, FieldConfig[]> = {
  basics: [
    { name: 'name', label: 'Universe Name', type: 'text', required: true, placeholder: 'Enter a name for your universe' },
    { name: 'description', label: 'Description', type: 'textarea', placeholder: 'Describe your universe...' }
  ],
  tone: [
    { name: 'darkness', label: 'Darkness', type: 'slider', required: true, min: 0, max: 100, description: '0 = Grimdark, 100 = Cozy' },
    { name: 'humor', label: 'Humor', type: 'slider', required: true, min: 0, max: 100, description: '0 = Comedic, 100 = Serious' },
    { name: 'realism', label: 'Realism', type: 'slider', required: true, min: 0, max: 100, description: '0 = Realistic, 100 = Fantastical' },
    { name: 'magic_level', label: 'Magic Level', type: 'slider', required: true, min: 0, max: 100, description: '0 = Low magic, 100 = High magic' },
    { name: 'themes', label: 'Themes', type: 'tags', placeholder: 'Add themes like exploration, intrigue, war...' }
  ],
  rules: [
    { name: 'permadeath', label: 'Permadeath', type: 'radio-boolean', required: true, trueLabel: 'Characters can permanently die', falseLabel: 'Characters cannot permanently die' },
    { name: 'critical_fumbles', label: 'Critical Fumbles', type: 'radio-boolean', required: true, trueLabel: 'Natural 1s have additional penalties', falseLabel: 'Natural 1s have no additional penalties' },
    { name: 'encumbrance', label: 'Encumbrance', type: 'radio-boolean', required: true, trueLabel: 'Track carrying capacity', falseLabel: 'Ignore carrying capacity' },
    { name: 'rules_strictness', label: 'Rules Strictness', type: 'slider', min: 0, max: 100, description: '0 = Loose (rule of cool), 100 = Strict (RAW)' }
  ],
  calendar: [
    { name: 'use_custom_names', label: 'Calendar Names', type: 'radio-boolean', trueLabel: 'Use custom month & weekday names', falseLabel: 'Use standard real-world names' },
    { name: 'month_names', label: 'Month Names', type: 'text', placeholder: 'Frostmoon, Stormtide, Greenleaf... (12 names, comma-separated)' },
    { name: 'weekday_names', label: 'Weekday Names', type: 'text', placeholder: 'Moonday, Fireday, Starday... (7 names, comma-separated)' },
  ],
  lore: [
    // History section
    { name: '_history_section', label: 'History', type: 'section', description: 'World timeline and historical events' },
    { name: 'world_timeline', label: 'World Timeline', type: 'textarea', placeholder: 'Major eras and events in chronological order...' },
    { name: 'regional_histories', label: 'Regional Histories', type: 'textarea', placeholder: 'How specific regions developed over time...' },
    { name: 'legendary_figures', label: 'Legendary Figures & Myths', type: 'textarea', placeholder: 'Heroes, villains, legends, and myths...' },
    { name: 'political_history', label: 'Political History', type: 'textarea', placeholder: 'Wars, treaties, rise and fall of empires...' },
    // Geography & Cultures section
    { name: '_geography_section', label: 'Geography & Cultures', type: 'section', description: 'Physical world and its peoples' },
    { name: 'geography', label: 'Geography', type: 'textarea', placeholder: 'Continents, seas, trade routes, distances...' },
    { name: 'regions_settlements', label: 'Regions & Settlements', type: 'textarea', placeholder: 'Detailed regions with major settlements...' },
    { name: 'cultures_peoples', label: 'Cultures & Peoples', type: 'textarea', placeholder: 'Cultures, customs, and traditions...' },
    { name: 'factions_religions', label: 'Factions & Religions', type: 'textarea', placeholder: 'Major organizations, guilds, religions...' },
    { name: 'mysterious_lands', label: 'Mysterious Lands', type: 'textarea', placeholder: 'Unexplored regions and distant mysteries...' },
    // Politics section
    { name: '_politics_section', label: 'Politics', type: 'section', description: 'Current political landscape' },
    { name: 'political_leaders', label: 'Political Leaders', type: 'textarea', placeholder: 'Major leaders and their positions...' },
    { name: 'leader_agendas', label: 'Leader Agendas', type: 'textarea', placeholder: 'Goals, motivations, and agendas...' },
    { name: 'regional_tensions', label: 'Regional Tensions', type: 'textarea', placeholder: 'Brewing conflicts and disputes...' },
    { name: 'faction_conflicts', label: 'Faction Conflicts', type: 'textarea', placeholder: 'Faction conflicts, alliances, and goals...' },
  ],
  homebrew: [
    { name: 'species', label: 'Custom Species', type: 'textarea', placeholder: 'Describe custom playable species/races for your universe...' },
    { name: 'classes', label: 'Custom Classes', type: 'textarea', placeholder: 'Describe custom character classes...' },
    { name: 'spells', label: 'Custom Spells', type: 'textarea', placeholder: 'Describe custom spells for your universe...' },
    { name: 'items', label: 'Custom Items', type: 'textarea', placeholder: 'Describe custom magic items and equipment...' },
    { name: 'monsters', label: 'Custom Monsters', type: 'textarea', placeholder: 'Describe custom monsters and creatures...' },
    { name: 'feats', label: 'Custom Feats', type: 'textarea', placeholder: 'Describe custom feats for characters...' },
    { name: 'backgrounds', label: 'Custom Backgrounds', type: 'textarea', placeholder: 'Describe custom character backgrounds...' },
  ]
};

@Component({
  selector: 'app-step-detail-panel',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule],
  template: `
    <div class="panel" [class.panel--open]="isOpen">
      <div class="panel__header">
        <div class="panel__title-area">
          <h3 class="panel__title">{{ stepDisplayName }}</h3>
          <span class="panel__status" [class.panel__status--complete]="isStepComplete" [class.panel__status--touched]="isStepTouched && !isStepComplete">
            @if (isStepComplete) {
              <lucide-icon [img]="CheckIcon" /> Complete
            } @else if (isStepTouched) {
              <lucide-icon [img]="AlertCircleIcon" /> In Progress
            } @else {
              <lucide-icon [img]="AlertCircleIcon" /> Not Started
            }
          </span>
        </div>
        <button class="panel__close" (click)="close.emit()" type="button">
          <lucide-icon [img]="XIcon" />
        </button>
      </div>

      <div class="panel__content">
        @if (stepInfo) {
          <p class="panel__description">{{ stepInfo.description }}</p>
        }

        @if (errorMessage()) {
          <div class="panel__error" role="alert">
            <lucide-icon [img]="AlertCircleIcon" />
            <span>{{ errorMessage() }}</span>
          </div>
        }

        <form class="panel__form" (ngSubmit)="saveChanges()">
          @for (field of fields; track field.name) {
            @if (field.type === 'section') {
              <div class="form-section">
                <h4 class="form-section__title">{{ field.label }}</h4>
                @if (field.description) {
                  <p class="form-section__description">{{ field.description }}</p>
                }
              </div>
            } @else {
            <div class="form-field" [class.form-field--filled]="isFieldFilled(field.name)">
              <label class="form-field__label" [for]="'field-' + field.name">
                {{ field.label }}
                @if (field.required) {
                  <span class="form-field__required">*</span>
                }
              </label>

              @if (field.description) {
                <span class="form-field__description">{{ field.description }}</span>
              }

              @switch (field.type) {
                @case ('text') {
                  <input
                    [id]="'field-' + field.name"
                    type="text"
                    class="form-field__input"
                    [placeholder]="field.placeholder || ''"
                    [ngModel]="getFieldValue(field.name)"
                    (ngModelChange)="setFieldValue(field.name, $event)"
                    [name]="field.name"
                  />
                  <div class="field-actions">
                    <button
                      type="button"
                      class="field-action-btn"
                      [disabled]="processingField() === field.name"
                      (click)="extractField(field.name)"
                      title="Extract from conversation"
                    >
                      @if (processingField() === field.name && processingAction() === 'extract') {
                        <lucide-icon [img]="Loader2Icon" class="spinning" />
                      } @else {
                        <lucide-icon [img]="Wand2Icon" />
                      }
                      Extract
                    </button>
                    <button
                      type="button"
                      class="field-action-btn"
                      [disabled]="!hasFieldContent(field.name) || processingField() === field.name"
                      (click)="extendField(field.name)"
                      title="Extend with more detail"
                    >
                      @if (processingField() === field.name && processingAction() === 'extend') {
                        <lucide-icon [img]="Loader2Icon" class="spinning" />
                      } @else {
                        <lucide-icon [img]="Maximize2Icon" />
                      }
                      Extend
                    </button>
                  </div>
                }
                @case ('textarea') {
                  <textarea
                    [id]="'field-' + field.name"
                    class="form-field__textarea"
                    [placeholder]="field.placeholder || ''"
                    [ngModel]="getFieldValue(field.name)"
                    (ngModelChange)="setFieldValue(field.name, $event)"
                    [name]="field.name"
                    rows="4"
                  ></textarea>
                  <div class="field-actions">
                    <button
                      type="button"
                      class="field-action-btn"
                      [disabled]="processingField() === field.name"
                      (click)="extractField(field.name)"
                      title="Extract from conversation"
                    >
                      @if (processingField() === field.name && processingAction() === 'extract') {
                        <lucide-icon [img]="Loader2Icon" class="spinning" />
                      } @else {
                        <lucide-icon [img]="Wand2Icon" />
                      }
                      Extract
                    </button>
                    <button
                      type="button"
                      class="field-action-btn"
                      [disabled]="!hasFieldContent(field.name) || processingField() === field.name"
                      (click)="extendField(field.name)"
                      title="Extend with more detail"
                    >
                      @if (processingField() === field.name && processingAction() === 'extend') {
                        <lucide-icon [img]="Loader2Icon" class="spinning" />
                      } @else {
                        <lucide-icon [img]="Maximize2Icon" />
                      }
                      Extend
                    </button>
                  </div>
                }
                @case ('slider') {
                  <div class="form-field__slider-container">
                    <input
                      [id]="'field-' + field.name"
                      type="range"
                      class="form-field__slider"
                      [min]="field.min ?? 0"
                      [max]="field.max ?? 100"
                      [ngModel]="getFieldValue(field.name) ?? 50"
                      (ngModelChange)="setFieldValue(field.name, $event)"
                      [name]="field.name"
                    />
                    <span class="form-field__slider-value">{{ getFieldValue(field.name) ?? 50 }}</span>
                  </div>
                }
                @case ('boolean') {
                  <label class="form-field__checkbox">
                    <input
                      type="checkbox"
                      [ngModel]="getFieldValue(field.name) ?? false"
                      (ngModelChange)="setFieldValue(field.name, $event)"
                      [name]="field.name"
                    />
                    <span class="form-field__checkbox-mark"></span>
                    {{ field.description }}
                  </label>
                }
                @case ('radio-boolean') {
                  <div class="form-field__radio-group">
                    <label class="form-field__radio">
                      <input
                        type="radio"
                        [name]="field.name"
                        [value]="true"
                        [checked]="getFieldValue(field.name) === true"
                        (change)="setFieldValue(field.name, true)"
                      />
                      <span class="form-field__radio-mark"></span>
                      {{ field.trueLabel }}
                    </label>
                    <label class="form-field__radio">
                      <input
                        type="radio"
                        [name]="field.name"
                        [value]="false"
                        [checked]="getFieldValue(field.name) === false"
                        (change)="setFieldValue(field.name, false)"
                      />
                      <span class="form-field__radio-mark"></span>
                      {{ field.falseLabel }}
                    </label>
                  </div>
                }
                @case ('tags') {
                  <div class="form-field__tags">
                    @for (tag of getTagsValue(field.name); track tag) {
                      <span class="form-field__tag">
                        {{ tag }}
                        <button type="button" class="form-field__tag-remove" (click)="removeTag(field.name, tag)">
                          <lucide-icon [img]="XIcon" />
                        </button>
                      </span>
                    }
                    <input
                      type="text"
                      class="form-field__tag-input"
                      [placeholder]="field.placeholder || 'Add tag...'"
                      (keydown.enter)="addTag(field.name, $event)"
                      [name]="field.name + '_input'"
                    />
                  </div>
                }
              }
            </div>
            }
          }

          @if (fields.length === 0) {
            <div class="panel__empty">
              <lucide-icon [img]="SparklesIcon" />
              <p>This section is managed through the chat conversation.</p>
            </div>
          }

          @if (fields.length > 0) {
            <div class="panel__actions">
              <button type="button" class="btn btn--ghost" (click)="close.emit()">
                Cancel
              </button>
              <button type="submit" class="btn btn--primary" [disabled]="!hasChanges">
                <lucide-icon [img]="CheckIcon" />
                Save Changes
              </button>
            </div>
          }
        </form>
      </div>
    </div>
  `,
  styles: [`
    .panel {
      width: 0;
      height: 100%;
      background: var(--wk-glass-bg);
      backdrop-filter: blur(var(--wk-blur-md));
      border-left: 1px solid var(--wk-glass-border);
      overflow: hidden;
      transition: width 0.3s ease;
      display: flex;
      flex-direction: column;
    }

    .panel--open {
      width: 380px;
    }

    .panel__header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: var(--wk-space-4);
      border-bottom: 1px solid var(--wk-glass-border);
      flex-shrink: 0;
    }

    .panel__title-area {
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-1);
    }

    .panel__title {
      margin: 0;
      font-size: var(--wk-text-lg);
      font-weight: var(--wk-font-semibold);
      color: var(--wk-text-primary);
    }

    .panel__status {
      display: inline-flex;
      align-items: center;
      gap: var(--wk-space-1);
      font-size: var(--wk-text-xs);
      color: var(--wk-text-muted);

      lucide-icon { width: 12px; height: 12px; }

      &--complete {
        color: var(--wk-success);
      }

      &--touched {
        color: var(--wk-warning);
      }
    }

    .panel__close {
      width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: transparent;
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-md);
      color: var(--wk-text-secondary);
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
      padding: var(--wk-space-4);
    }

    .panel__description {
      margin: 0 0 var(--wk-space-4);
      font-size: var(--wk-text-sm);
      color: var(--wk-text-secondary);
    }

    .panel__error {
      display: flex;
      align-items: flex-start;
      gap: var(--wk-space-2);
      padding: var(--wk-space-3);
      margin-bottom: var(--wk-space-4);
      background: rgba(239, 68, 68, 0.1);
      border: 1px solid var(--wk-error);
      border-radius: var(--wk-radius-md);
      color: var(--wk-error);
      font-size: var(--wk-text-sm);

      lucide-icon {
        width: 16px;
        height: 16px;
        flex-shrink: 0;
        margin-top: 2px;
      }
    }

    .panel__form {
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-4);
    }

    .form-section {
      margin-top: var(--wk-space-6);
      margin-bottom: var(--wk-space-2);
      padding-bottom: var(--wk-space-2);
      border-bottom: 1px solid var(--wk-glass-border);

      &:first-child {
        margin-top: 0;
      }
    }

    .form-section__title {
      margin: 0;
      font-size: var(--wk-text-md);
      font-weight: var(--wk-font-semibold);
      color: var(--wk-primary);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .form-section__description {
      margin: var(--wk-space-1) 0 0;
      font-size: var(--wk-text-xs);
      color: var(--wk-text-muted);
    }

    .form-field {
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-2);
    }

    .form-field__label {
      font-size: var(--wk-text-sm);
      font-weight: var(--wk-font-medium);
      color: var(--wk-text-primary);
    }

    .form-field__required {
      color: var(--wk-error);
      margin-left: var(--wk-space-1);
    }

    .form-field__description {
      font-size: var(--wk-text-xs);
      color: var(--wk-text-muted);
    }

    .form-field__input,
    .form-field__textarea {
      padding: var(--wk-space-3);
      background: var(--wk-surface-elevated);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-md);
      color: var(--wk-text-primary);
      font-size: var(--wk-text-sm);
      font-family: inherit;
      transition: all var(--wk-transition-fast);

      &::placeholder { color: var(--wk-text-muted); }

      &:focus {
        outline: none;
        border-color: var(--wk-primary);
        box-shadow: 0 0 0 3px var(--wk-primary-glow);
      }
    }

    .form-field__textarea {
      resize: vertical;
      min-height: 100px;
    }

    .form-field__slider-container {
      display: flex;
      align-items: center;
      gap: var(--wk-space-3);
    }

    .form-field__slider {
      flex: 1;
      height: 6px;
      appearance: none;
      background: var(--wk-surface-elevated);
      border-radius: var(--wk-radius-full);
      outline: none;

      &::-webkit-slider-thumb {
        appearance: none;
        width: 18px;
        height: 18px;
        background: var(--wk-primary);
        border-radius: 50%;
        cursor: pointer;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
      }

      &::-moz-range-thumb {
        width: 18px;
        height: 18px;
        background: var(--wk-primary);
        border-radius: 50%;
        cursor: pointer;
        border: none;
      }
    }

    .form-field__slider-value {
      min-width: 40px;
      text-align: center;
      font-size: var(--wk-text-sm);
      font-weight: var(--wk-font-medium);
      color: var(--wk-primary);
    }

    .form-field__checkbox {
      display: flex;
      align-items: center;
      gap: var(--wk-space-3);
      cursor: pointer;
      font-size: var(--wk-text-sm);
      color: var(--wk-text-secondary);

      input {
        display: none;
      }
    }

    .form-field__checkbox-mark {
      width: 20px;
      height: 20px;
      border: 2px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-sm);
      background: var(--wk-surface-elevated);
      position: relative;
      flex-shrink: 0;
      transition: all var(--wk-transition-fast);

      input:checked + & {
        background: var(--wk-primary);
        border-color: var(--wk-primary);

        &::after {
          content: '';
          position: absolute;
          top: 3px;
          left: 6px;
          width: 5px;
          height: 9px;
          border: solid white;
          border-width: 0 2px 2px 0;
          transform: rotate(45deg);
        }
      }
    }

    .form-field__radio-group {
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-2);
    }

    .form-field__radio {
      display: flex;
      align-items: center;
      gap: var(--wk-space-3);
      cursor: pointer;
      font-size: var(--wk-text-sm);
      color: var(--wk-text-secondary);
      padding: var(--wk-space-2) var(--wk-space-3);
      border-radius: var(--wk-radius-md);
      transition: background-color var(--wk-transition-fast);

      &:hover {
        background: var(--wk-surface-elevated);
      }

      input {
        display: none;
      }
    }

    .form-field__radio-mark {
      width: 20px;
      height: 20px;
      border: 2px solid var(--wk-glass-border);
      border-radius: 50%;
      background: var(--wk-surface-elevated);
      position: relative;
      flex-shrink: 0;
      transition: all var(--wk-transition-fast);

      input:checked + & {
        border-color: var(--wk-primary);

        &::after {
          content: '';
          position: absolute;
          top: 4px;
          left: 4px;
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: var(--wk-primary);
        }
      }
    }

    .form-field__tags {
      display: flex;
      flex-wrap: wrap;
      gap: var(--wk-space-2);
      padding: var(--wk-space-2);
      background: var(--wk-surface-elevated);
      border: 1px solid var(--wk-glass-border);
      border-radius: var(--wk-radius-md);
      min-height: 44px;
    }

    .form-field__tag {
      display: inline-flex;
      align-items: center;
      gap: var(--wk-space-1);
      padding: var(--wk-space-1) var(--wk-space-2);
      background: var(--wk-primary-glow);
      border: 1px solid var(--wk-primary);
      border-radius: var(--wk-radius-sm);
      font-size: var(--wk-text-xs);
      color: var(--wk-primary);
    }

    .form-field__tag-remove {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 14px;
      height: 14px;
      padding: 0;
      background: none;
      border: none;
      cursor: pointer;
      color: var(--wk-primary);
      opacity: 0.7;

      lucide-icon { width: 10px; height: 10px; }

      &:hover { opacity: 1; }
    }

    .form-field__tag-input {
      flex: 1;
      min-width: 100px;
      padding: var(--wk-space-1);
      background: transparent;
      border: none;
      color: var(--wk-text-primary);
      font-size: var(--wk-text-sm);

      &::placeholder { color: var(--wk-text-muted); }
      &:focus { outline: none; }
    }

    .panel__empty {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: var(--wk-space-8);
      text-align: center;
      color: var(--wk-text-muted);

      lucide-icon {
        width: 48px;
        height: 48px;
        margin-bottom: var(--wk-space-4);
        opacity: 0.5;
      }

      p {
        margin: 0;
        font-size: var(--wk-text-sm);
      }
    }

    .panel__actions {
      display: flex;
      gap: var(--wk-space-3);
      justify-content: flex-end;
      padding-top: var(--wk-space-4);
      border-top: 1px solid var(--wk-glass-border);
      margin-top: var(--wk-space-4);
    }

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

      &--ghost {
        background: transparent;
        border: 1px solid var(--wk-glass-border);
        color: var(--wk-text-secondary);

        &:hover:not(:disabled) {
          background: var(--wk-surface-elevated);
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

    .field-actions {
      display: flex;
      gap: var(--wk-space-2);
      margin-top: var(--wk-space-2);
    }

    .field-action-btn {
      display: inline-flex;
      align-items: center;
      gap: var(--wk-space-1);
      padding: var(--wk-space-1) var(--wk-space-3);
      font-size: var(--wk-text-xs);
      font-weight: var(--wk-font-medium);
      border-radius: var(--wk-radius-sm);
      background: var(--wk-surface-elevated);
      border: 1px solid var(--wk-glass-border);
      color: var(--wk-text-secondary);
      cursor: pointer;
      transition: all var(--wk-transition-fast);

      lucide-icon {
        width: 14px;
        height: 14px;
      }

      &:hover:not(:disabled) {
        background: var(--wk-primary-glow);
        border-color: var(--wk-primary);
        color: var(--wk-primary);
      }

      &:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }
    }

    .spinning {
      animation: spin 1s linear infinite;
    }

    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }

    @media (max-width: 768px) {
      .panel--open {
        width: 100%;
        position: absolute;
        right: 0;
        top: 0;
        z-index: 100;
      }
    }
  `]
})
export class StepDetailPanelComponent implements OnChanges {
  private readonly worldgenService = inject(WorldgenService);

  @Input() step: WorldgenStepName | null = null;
  @Input() isOpen = false;
  @Input() draftData: WorldgenDraftData | null = null;
  @Input() stepStatus: Record<WorldgenStepName, WorldgenStepStatus> | null = null;
  @Input() sessionId: string | null = null;

  @Output() close = new EventEmitter<void>();
  @Output() saved = new EventEmitter<void>();

  readonly XIcon = X;
  readonly CheckIcon = Check;
  readonly AlertCircleIcon = AlertCircle;
  readonly SparklesIcon = Sparkles;
  readonly Wand2Icon = Wand2;
  readonly Maximize2Icon = Maximize2;
  readonly Loader2Icon = Loader2;

  // Local form state
  private localData = signal<Record<string, unknown>>({});
  private originalData = signal<Record<string, unknown>>({});

  // Processing state for extract/extend operations
  readonly processingField = signal<string | null>(null);
  readonly processingAction = signal<'extract' | 'extend' | null>(null);
  readonly errorMessage = signal<string | null>(null);

  get stepDisplayName(): string {
    if (!this.step) return '';
    const info = WORLDGEN_STEPS.find(s => s.name === this.step);
    return info?.displayName ?? this.step;
  }

  get stepInfo(): { description: string } | null {
    if (!this.step) return null;
    const info = WORLDGEN_STEPS.find(s => s.name === this.step);
    return info ? { description: info.description } : null;
  }

  get fields(): FieldConfig[] {
    if (!this.step) return [];
    return STEP_FIELDS[this.step] ?? [];
  }

  get isStepComplete(): boolean {
    if (!this.step || !this.stepStatus) return false;
    return this.stepStatus[this.step]?.complete ?? false;
  }

  get isStepTouched(): boolean {
    if (!this.step || !this.stepStatus) return false;
    return this.stepStatus[this.step]?.touched ?? false;
  }

  get hasChanges(): boolean {
    const local = this.localData();
    const original = this.originalData();
    return JSON.stringify(local) !== JSON.stringify(original);
  }

  ngOnChanges(changes: SimpleChanges): void {
    if ((changes['step'] || changes['draftData']) && this.step && this.draftData) {
      const stepData = this.draftData[this.step] ?? {};
      this.localData.set({ ...stepData });
      this.originalData.set({ ...stepData });
    }
  }

  getFieldValue(fieldName: string): unknown {
    return this.localData()[fieldName];
  }

  setFieldValue(fieldName: string, value: unknown): void {
    this.localData.update(data => ({ ...data, [fieldName]: value }));
  }

  isFieldFilled(fieldName: string): boolean {
    if (!this.step || !this.stepStatus) return false;
    return this.stepStatus[this.step]?.fields?.[fieldName] ?? false;
  }

  getTagsValue(fieldName: string): string[] {
    const value = this.localData()[fieldName];
    if (Array.isArray(value)) return value as string[];
    return [];
  }

  addTag(fieldName: string, event: Event): void {
    event.preventDefault();
    const input = event.target as HTMLInputElement;
    const value = input.value.trim();
    if (!value) return;

    const current = this.getTagsValue(fieldName);
    if (!current.includes(value)) {
      this.setFieldValue(fieldName, [...current, value]);
    }
    input.value = '';
  }

  removeTag(fieldName: string, tag: string): void {
    const current = this.getTagsValue(fieldName);
    this.setFieldValue(fieldName, current.filter(t => t !== tag));
  }

  saveChanges(): void {
    if (!this.sessionId || !this.step || !this.hasChanges) return;

    this.worldgenService.updateStepData(this.sessionId, this.step, this.localData()).subscribe({
      next: () => {
        this.originalData.set({ ...this.localData() });
        this.saved.emit();
      },
      error: err => {
        console.error('Failed to save step data:', err);
      }
    });
  }

  hasFieldContent(fieldName: string): boolean {
    const value = this.localData()[fieldName];
    if (typeof value === 'string') {
      return value.trim().length > 0;
    }
    return !!value;
  }

  extractField(fieldName: string): void {
    if (!this.sessionId || !this.step) return;

    this.processingField.set(fieldName);
    this.processingAction.set('extract');

    this.worldgenService.extractField(this.sessionId, this.step, fieldName).subscribe({
      next: (result) => {
        // Update local data with the extracted value
        const stepData = result.draft_data[this.step!] as Record<string, unknown> | undefined;
        const newValue = stepData?.[fieldName];
        if (newValue !== undefined) {
          this.setFieldValue(fieldName, newValue);
          this.originalData.update(data => ({ ...data, [fieldName]: newValue }));
        }
        this.processingField.set(null);
        this.processingAction.set(null);
      },
      error: (err) => {
        console.error('Failed to extract field:', err);
        const message = err?.error?.detail || err?.message || 'Failed to extract field. Please try again.';
        this.errorMessage.set(message);
        this.processingField.set(null);
        this.processingAction.set(null);
        // Auto-dismiss after 5 seconds
        setTimeout(() => this.errorMessage.set(null), 5000);
      }
    });
  }

  extendField(fieldName: string): void {
    if (!this.sessionId || !this.step) return;

    this.processingField.set(fieldName);
    this.processingAction.set('extend');

    this.worldgenService.extendField(this.sessionId, this.step, fieldName).subscribe({
      next: (result) => {
        // Update local data with the extended value
        const stepData = result.draft_data[this.step!] as Record<string, unknown> | undefined;
        const newValue = stepData?.[fieldName];
        if (newValue !== undefined) {
          this.setFieldValue(fieldName, newValue);
          this.originalData.update(data => ({ ...data, [fieldName]: newValue }));
        }
        this.processingField.set(null);
        this.processingAction.set(null);
      },
      error: (err) => {
        console.error('Failed to extend field:', err);
        const message = err?.error?.detail || err?.message || 'Failed to extend field. Please try again.';
        this.errorMessage.set(message);
        this.processingField.set(null);
        this.processingAction.set(null);
        // Auto-dismiss after 5 seconds
        setTimeout(() => this.errorMessage.set(null), 5000);
      }
    });
  }
}
