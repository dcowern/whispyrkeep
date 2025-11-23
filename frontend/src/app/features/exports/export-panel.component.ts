import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ExportService, UniverseService, CampaignService, CharacterService } from '@core/services';
import { ExportJob, Universe, Campaign, CharacterSheet } from '@core/models';

type ExportType = 'universe' | 'campaign' | 'character';
type ExportFormat = 'json' | 'markdown' | 'pdf';

@Component({
  selector: 'app-export-panel',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="export-panel">
      <header class="export-panel__header">
        <a routerLink="/home" class="back-link">Back to Dashboard</a>
        <h1>Export Data</h1>
      </header>

      <main class="export-panel__content">
        <!-- Export Type Selection -->
        <section class="export-section">
          <h2>What would you like to export?</h2>
          <div class="type-buttons">
            <button
              class="type-btn"
              [class.type-btn--active]="exportType() === 'universe'"
              (click)="selectType('universe')"
            >
              <span class="type-btn__icon">🌍</span>
              <span class="type-btn__label">Universe</span>
            </button>
            <button
              class="type-btn"
              [class.type-btn--active]="exportType() === 'campaign'"
              (click)="selectType('campaign')"
            >
              <span class="type-btn__icon">📜</span>
              <span class="type-btn__label">Campaign</span>
            </button>
            <button
              class="type-btn"
              [class.type-btn--active]="exportType() === 'character'"
              (click)="selectType('character')"
            >
              <span class="type-btn__icon">🧙</span>
              <span class="type-btn__label">Character</span>
            </button>
          </div>
        </section>

        <!-- Item Selection -->
        @if (exportType()) {
          <section class="export-section">
            <h2>Select {{ exportType() }}</h2>
            @if (isLoadingItems()) {
              <p class="loading">Loading...</p>
            } @else if (availableItems().length === 0) {
              <p class="empty">No {{ exportType() }}s found.</p>
            } @else {
              <div class="item-list">
                @for (item of availableItems(); track item.id) {
                  <button
                    class="item-btn"
                    [class.item-btn--selected]="selectedItemId() === item.id"
                    (click)="selectItem(item.id)"
                  >
                    {{ item.name }}
                  </button>
                }
              </div>
            }
          </section>
        }

        <!-- Format Selection -->
        @if (selectedItemId()) {
          <section class="export-section">
            <h2>Export Format</h2>
            <div class="format-buttons">
              <button
                class="format-btn"
                [class.format-btn--selected]="exportFormat() === 'json'"
                (click)="selectFormat('json')"
              >
                <strong>JSON</strong>
                <span>Full data export</span>
              </button>
              <button
                class="format-btn"
                [class.format-btn--selected]="exportFormat() === 'markdown'"
                (click)="selectFormat('markdown')"
              >
                <strong>Markdown</strong>
                <span>Human-readable</span>
              </button>
              <button
                class="format-btn"
                [class.format-btn--selected]="exportFormat() === 'pdf'"
                (click)="selectFormat('pdf')"
              >
                <strong>PDF</strong>
                <span>Print-ready</span>
              </button>
            </div>
          </section>
        }

        <!-- Export Button -->
        @if (exportFormat()) {
          <section class="export-section">
            <button
              class="export-btn"
              [disabled]="isExporting()"
              (click)="startExport()"
            >
              {{ isExporting() ? 'Exporting...' : 'Start Export' }}
            </button>
          </section>
        }

        <!-- Recent Exports -->
        @if (recentExports().length > 0) {
          <section class="export-section">
            <h2>Recent Exports</h2>
            <div class="export-list">
              @for (job of recentExports(); track job.id) {
                <div class="export-item" [class.export-item--complete]="job.status === 'complete'">
                  <div class="export-item__info">
                    <span class="export-item__type">{{ job.export_type | titlecase }}</span>
                    <span class="export-item__format">{{ job.format | uppercase }}</span>
                  </div>
                  <div class="export-item__status">
                    @if (job.status === 'complete' && job.file_url) {
                      <a [href]="job.file_url" class="download-link" download>Download</a>
                    } @else if (job.status === 'processing') {
                      <span class="status status--processing">Processing...</span>
                    } @else if (job.status === 'failed') {
                      <span class="status status--failed">Failed</span>
                    } @else {
                      <span class="status">{{ job.status }}</span>
                    }
                  </div>
                </div>
              }
            </div>
          </section>
        }
      </main>
    </div>
  `,
  styles: [`
    .export-panel { display: flex; flex-direction: column; min-height: 100vh; }
    .export-panel__header { padding: var(--wk-space-md) var(--wk-space-lg); border-bottom: 1px solid var(--wk-border); }
    .export-panel__header h1 { margin: var(--wk-space-sm) 0 0; font-size: 1.5rem; }
    .back-link { color: var(--wk-text-secondary); text-decoration: none; font-size: 0.875rem; }

    .export-panel__content { flex: 1; padding: var(--wk-space-lg); max-width: 800px; }
    .export-section { margin-bottom: var(--wk-space-xl); }
    .export-section h2 { font-size: 1rem; margin: 0 0 var(--wk-space-md); }
    .loading, .empty { color: var(--wk-text-muted); }

    .type-buttons { display: flex; gap: var(--wk-space-md); }
    .type-btn { display: flex; flex-direction: column; align-items: center; padding: var(--wk-space-lg); background: var(--wk-surface); border: 2px solid var(--wk-border); border-radius: var(--wk-radius-lg); cursor: pointer; min-width: 120px; transition: border-color 0.2s; }
    .type-btn:hover { border-color: var(--wk-primary); }
    .type-btn--active { border-color: var(--wk-primary); background: var(--wk-surface-elevated); }
    .type-btn__icon { font-size: 2rem; margin-bottom: var(--wk-space-sm); }
    .type-btn__label { font-weight: 500; }

    .item-list { display: flex; flex-wrap: wrap; gap: var(--wk-space-sm); }
    .item-btn { padding: var(--wk-space-sm) var(--wk-space-md); background: var(--wk-surface); border: 1px solid var(--wk-border); border-radius: var(--wk-radius-md); cursor: pointer; }
    .item-btn:hover { border-color: var(--wk-primary); }
    .item-btn--selected { background: var(--wk-primary); border-color: var(--wk-primary); color: white; }

    .format-buttons { display: flex; gap: var(--wk-space-md); }
    .format-btn { display: flex; flex-direction: column; padding: var(--wk-space-md); background: var(--wk-surface); border: 2px solid var(--wk-border); border-radius: var(--wk-radius-md); cursor: pointer; min-width: 140px; }
    .format-btn:hover { border-color: var(--wk-primary); }
    .format-btn--selected { border-color: var(--wk-primary); background: var(--wk-surface-elevated); }
    .format-btn strong { margin-bottom: 4px; }
    .format-btn span { font-size: 0.75rem; color: var(--wk-text-secondary); }

    .export-btn { padding: var(--wk-space-md) var(--wk-space-xl); background: var(--wk-primary); border: none; border-radius: var(--wk-radius-md); color: white; font-size: 1rem; cursor: pointer; }
    .export-btn:disabled { opacity: 0.5; cursor: not-allowed; }

    .export-list { display: flex; flex-direction: column; gap: var(--wk-space-sm); }
    .export-item { display: flex; justify-content: space-between; align-items: center; padding: var(--wk-space-md); background: var(--wk-surface); border-radius: var(--wk-radius-md); }
    .export-item__info { display: flex; gap: var(--wk-space-sm); }
    .export-item__type { font-weight: 500; }
    .export-item__format { padding: 2px 8px; background: var(--wk-background); border-radius: var(--wk-radius-sm); font-size: 0.75rem; }
    .download-link { color: var(--wk-primary); text-decoration: none; font-weight: 500; }
    .status { font-size: 0.875rem; color: var(--wk-text-muted); }
    .status--processing { color: var(--wk-warning); }
    .status--failed { color: var(--wk-error); }
  `]
})
export class ExportPanelComponent implements OnInit {
  private readonly exportService = inject(ExportService);
  private readonly universeService = inject(UniverseService);
  private readonly campaignService = inject(CampaignService);
  private readonly characterService = inject(CharacterService);

  readonly exportType = signal<ExportType | null>(null);
  readonly selectedItemId = signal<string | null>(null);
  readonly exportFormat = signal<ExportFormat | null>(null);
  readonly isLoadingItems = signal(false);
  readonly isExporting = signal(false);
  readonly availableItems = signal<{ id: string; name: string }[]>([]);
  readonly recentExports = signal<ExportJob[]>([]);

  ngOnInit(): void {
    this.loadRecentExports();
  }

  private loadRecentExports(): void {
    this.exportService.list().subscribe({
      next: (res) => this.recentExports.set(res.results.slice(0, 5)),
      error: () => {}
    });
  }

  selectType(type: ExportType): void {
    this.exportType.set(type);
    this.selectedItemId.set(null);
    this.exportFormat.set(null);
    this.loadItems(type);
  }

  private loadItems(type: ExportType): void {
    this.isLoadingItems.set(true);
    this.availableItems.set([]);

    switch (type) {
      case 'universe':
        this.universeService.list().subscribe({
          next: (res) => {
            this.availableItems.set(res.results.map(u => ({ id: u.id, name: u.name })));
            this.isLoadingItems.set(false);
          },
          error: () => this.isLoadingItems.set(false)
        });
        break;
      case 'campaign':
        this.campaignService.list().subscribe({
          next: (res) => {
            this.availableItems.set(res.results.map(c => ({ id: c.id, name: c.name })));
            this.isLoadingItems.set(false);
          },
          error: () => this.isLoadingItems.set(false)
        });
        break;
      case 'character':
        this.characterService.list().subscribe({
          next: (res) => {
            this.availableItems.set(res.results.map(c => ({ id: c.id, name: c.name })));
            this.isLoadingItems.set(false);
          },
          error: () => this.isLoadingItems.set(false)
        });
        break;
    }
  }

  selectItem(id: string): void {
    this.selectedItemId.set(id);
    this.exportFormat.set(null);
  }

  selectFormat(format: ExportFormat): void {
    this.exportFormat.set(format);
  }

  startExport(): void {
    const type = this.exportType();
    const targetId = this.selectedItemId();
    const format = this.exportFormat();

    if (!type || !targetId || !format) return;

    this.isExporting.set(true);
    this.exportService.create({
      export_type: type,
      target_id: targetId,
      format: format
    }).subscribe({
      next: (job) => {
        this.recentExports.update(exports => [job, ...exports.slice(0, 4)]);
        this.isExporting.set(false);
        // Reset selection
        this.exportType.set(null);
        this.selectedItemId.set(null);
        this.exportFormat.set(null);
      },
      error: () => this.isExporting.set(false)
    });
  }
}
