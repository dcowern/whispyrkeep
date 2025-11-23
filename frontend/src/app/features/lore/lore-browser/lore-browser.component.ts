import { Component, inject, signal, input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { CampaignService } from '@core/services';
import { LoreEntry } from '@core/models';

type LoreTab = 'canon' | 'rumors';

@Component({
  selector: 'app-lore-browser',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="lore-browser">
      <header class="lore-browser__header">
        <a [routerLink]="backLink()" class="back-link">Back</a>
        <h1>Lore Browser</h1>
      </header>

      <!-- Search -->
      <div class="search-bar">
        <input
          type="search"
          [(ngModel)]="searchQuery"
          (ngModelChange)="onSearch($event)"
          class="search-input"
          placeholder="Search lore..."
        />
      </div>

      <!-- Tabs -->
      <nav class="tabs">
        <button
          class="tab"
          [class.tab--active]="activeTab() === 'canon'"
          (click)="activeTab.set('canon')"
        >
          Hard Canon
          <span class="tab__count">{{ canonEntries().length }}</span>
        </button>
        <button
          class="tab"
          [class.tab--active]="activeTab() === 'rumors'"
          (click)="activeTab.set('rumors')"
        >
          Rumors & Soft Lore
          <span class="tab__count">{{ rumorEntries().length }}</span>
        </button>
      </nav>

      <!-- Content -->
      <main class="lore-content">
        @if (isLoading()) {
          <p class="loading">Loading lore...</p>
        } @else if (filteredEntries().length === 0) {
          <div class="empty-state">
            @if (searchQuery) {
              <p>No lore entries match your search.</p>
            } @else {
              <p>No {{ activeTab() === 'canon' ? 'hard canon' : 'rumors' }} entries yet.</p>
            }
          </div>
        } @else {
          <div class="lore-list">
            @for (entry of filteredEntries(); track entry.id) {
              <article class="lore-entry" [class.lore-entry--rumor]="!entry.is_canon">
                <header class="lore-entry__header">
                  <h3 class="lore-entry__title">{{ entry.title || 'Untitled' }}</h3>
                  <span class="lore-entry__type" [class.lore-entry__type--canon]="entry.is_canon">
                    {{ entry.is_canon ? 'Canon' : 'Rumor' }}
                  </span>
                </header>
                <p class="lore-entry__content">{{ entry.content }}</p>
                @if (entry.source) {
                  <footer class="lore-entry__footer">
                    <span class="lore-entry__source">Source: {{ entry.source }}</span>
                  </footer>
                }
                @if (entry.tags && entry.tags.length > 0) {
                  <div class="lore-entry__tags">
                    @for (tag of entry.tags; track tag) {
                      <span class="tag">{{ tag }}</span>
                    }
                  </div>
                }
              </article>
            }
          </div>
        }
      </main>
    </div>
  `,
  styles: [`
    .lore-browser { display: flex; flex-direction: column; min-height: 100vh; }
    .lore-browser__header { padding: var(--wk-space-md) var(--wk-space-lg); border-bottom: 1px solid var(--wk-border); }
    .lore-browser__header h1 { margin: var(--wk-space-sm) 0 0; font-size: 1.5rem; }
    .back-link { color: var(--wk-text-secondary); text-decoration: none; font-size: 0.875rem; }

    .search-bar { padding: var(--wk-space-md) var(--wk-space-lg); border-bottom: 1px solid var(--wk-border); }
    .search-input { width: 100%; max-width: 400px; padding: var(--wk-space-sm) var(--wk-space-md); border: 1px solid var(--wk-border); border-radius: var(--wk-radius-md); background: var(--wk-background); color: var(--wk-text-primary); }

    .tabs { display: flex; gap: var(--wk-space-xs); padding: 0 var(--wk-space-lg); border-bottom: 1px solid var(--wk-border); }
    .tab { display: flex; align-items: center; gap: var(--wk-space-xs); padding: var(--wk-space-md); background: none; border: none; border-bottom: 2px solid transparent; color: var(--wk-text-secondary); cursor: pointer; }
    .tab--active { border-bottom-color: var(--wk-primary); color: var(--wk-primary); }
    .tab__count { padding: 2px 8px; font-size: 0.75rem; background: var(--wk-surface); border-radius: 999px; }

    .lore-content { flex: 1; padding: var(--wk-space-lg); overflow-y: auto; }
    .loading { color: var(--wk-text-muted); }
    .empty-state { text-align: center; padding: var(--wk-space-xl); color: var(--wk-text-secondary); }

    .lore-list { display: flex; flex-direction: column; gap: var(--wk-space-md); max-width: 800px; }
    .lore-entry { background: var(--wk-surface); border-radius: var(--wk-radius-lg); padding: var(--wk-space-md); border-left: 3px solid var(--wk-primary); }
    .lore-entry--rumor { border-left-color: var(--wk-warning); opacity: 0.9; }
    .lore-entry__header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--wk-space-sm); }
    .lore-entry__title { margin: 0; font-size: 1rem; }
    .lore-entry__type { font-size: 0.75rem; padding: 2px 8px; border-radius: var(--wk-radius-sm); background: var(--wk-surface-elevated); }
    .lore-entry__type--canon { background: var(--wk-primary); color: white; }
    .lore-entry__content { margin: 0 0 var(--wk-space-sm); color: var(--wk-text-secondary); font-size: 0.875rem; line-height: 1.5; }
    .lore-entry__footer { font-size: 0.75rem; color: var(--wk-text-muted); }
    .lore-entry__tags { display: flex; flex-wrap: wrap; gap: var(--wk-space-xs); margin-top: var(--wk-space-sm); }
    .tag { padding: 2px 8px; font-size: 0.75rem; background: var(--wk-background); border-radius: var(--wk-radius-sm); color: var(--wk-text-secondary); }
  `]
})
export class LoreBrowserComponent implements OnInit {
  private readonly campaignService = inject(CampaignService);

  campaignId = input<string>();

  readonly activeTab = signal<LoreTab>('canon');
  readonly loreEntries = signal<LoreEntry[]>([]);
  readonly isLoading = signal(true);
  searchQuery = '';

  ngOnInit(): void {
    if (this.campaignId()) {
      this.loadLore();
    } else {
      this.isLoading.set(false);
    }
  }

  private loadLore(): void {
    this.campaignService.getLore(this.campaignId()!).subscribe({
      next: (entries) => { this.loreEntries.set(entries); this.isLoading.set(false); },
      error: () => this.isLoading.set(false)
    });
  }

  backLink(): string {
    return this.campaignId() ? `/play/${this.campaignId()}` : '/campaigns';
  }

  canonEntries = () => this.loreEntries().filter(e => e.is_canon);
  rumorEntries = () => this.loreEntries().filter(e => !e.is_canon);

  filteredEntries = () => {
    const entries = this.activeTab() === 'canon' ? this.canonEntries() : this.rumorEntries();
    if (!this.searchQuery) return entries;
    const query = this.searchQuery.toLowerCase();
    return entries.filter(e =>
      (e.title?.toLowerCase().includes(query)) ||
      e.content.toLowerCase().includes(query) ||
      e.tags?.some(t => t.toLowerCase().includes(query))
    );
  };

  onSearch(query: string): void {
    this.searchQuery = query;
  }
}
