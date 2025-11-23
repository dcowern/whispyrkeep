import { Component, inject, signal, input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { UniverseService } from '@core/services';

interface TimelineEra {
  id: string;
  name: string;
  startYear: number;
  endYear: number | null;
  description: string;
  events: TimelineEvent[];
}

interface TimelineEvent {
  id: string;
  name: string;
  year: number;
  description: string;
  category: 'political' | 'war' | 'discovery' | 'catastrophe' | 'cultural' | 'magical';
}

@Component({
  selector: 'app-timeline-viewer',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="timeline-viewer">
      <header class="timeline-viewer__header">
        <a [routerLink]="['/universes', universeId()]" class="back-link">Back to Universe</a>
        <h1>Timeline</h1>
        @if (universeName()) {
          <p class="universe-name">{{ universeName() }}</p>
        }
      </header>

      <main class="timeline-viewer__content">
        @if (isLoading()) {
          <p class="loading">Loading timeline...</p>
        } @else if (eras().length === 0) {
          <div class="empty-state">
            <p>No timeline events have been created for this universe yet.</p>
            <p class="hint">Timeline events are generated as your campaigns progress.</p>
          </div>
        } @else {
          <div class="timeline">
            @for (era of eras(); track era.id) {
              <section class="era">
                <div class="era__header">
                  <h2 class="era__title">{{ era.name }}</h2>
                  <span class="era__years">
                    {{ era.startYear }} - {{ era.endYear || 'Present' }}
                  </span>
                </div>
                <p class="era__description">{{ era.description }}</p>

                @if (era.events.length > 0) {
                  <div class="events">
                    @for (event of era.events; track event.id) {
                      <article class="event" [attr.data-category]="event.category">
                        <div class="event__marker"></div>
                        <div class="event__content">
                          <div class="event__header">
                            <span class="event__year">{{ event.year }}</span>
                            <span class="event__category">{{ categoryLabels[event.category] }}</span>
                          </div>
                          <h3 class="event__title">{{ event.name }}</h3>
                          <p class="event__description">{{ event.description }}</p>
                        </div>
                      </article>
                    }
                  </div>
                }
              </section>
            }
          </div>
        }
      </main>
    </div>
  `,
  styles: [`
    .timeline-viewer { display: flex; flex-direction: column; min-height: 100vh; }
    .timeline-viewer__header { padding: var(--wk-space-md) var(--wk-space-lg); border-bottom: 1px solid var(--wk-border); }
    .timeline-viewer__header h1 { margin: var(--wk-space-sm) 0 0; font-size: 1.5rem; }
    .back-link { color: var(--wk-text-secondary); text-decoration: none; font-size: 0.875rem; }
    .universe-name { color: var(--wk-text-secondary); margin: var(--wk-space-xs) 0 0; }

    .timeline-viewer__content { flex: 1; padding: var(--wk-space-lg); overflow-y: auto; }
    .loading { color: var(--wk-text-muted); }
    .empty-state { text-align: center; padding: var(--wk-space-xl); }
    .empty-state p { color: var(--wk-text-secondary); }
    .empty-state .hint { font-size: 0.875rem; color: var(--wk-text-muted); }

    .timeline { max-width: 800px; }

    .era { margin-bottom: var(--wk-space-xl); }
    .era__header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: var(--wk-space-sm); }
    .era__title { margin: 0; font-size: 1.25rem; color: var(--wk-primary); }
    .era__years { font-size: 0.875rem; color: var(--wk-text-muted); }
    .era__description { color: var(--wk-text-secondary); margin: 0 0 var(--wk-space-md); }

    .events { position: relative; padding-left: var(--wk-space-lg); border-left: 2px solid var(--wk-border); }

    .event { position: relative; margin-bottom: var(--wk-space-md); }
    .event__marker { position: absolute; left: calc(-1 * var(--wk-space-lg) - 6px); top: 4px; width: 10px; height: 10px; border-radius: 50%; background: var(--wk-surface); border: 2px solid var(--wk-primary); }
    .event[data-category="war"] .event__marker { border-color: var(--wk-error); }
    .event[data-category="catastrophe"] .event__marker { border-color: var(--wk-warning); }
    .event[data-category="discovery"] .event__marker { border-color: var(--wk-success); }
    .event[data-category="magical"] .event__marker { border-color: #9b59b6; }

    .event__content { background: var(--wk-surface); padding: var(--wk-space-md); border-radius: var(--wk-radius-md); }
    .event__header { display: flex; justify-content: space-between; margin-bottom: var(--wk-space-xs); }
    .event__year { font-weight: 600; font-size: 0.875rem; }
    .event__category { font-size: 0.75rem; color: var(--wk-text-muted); text-transform: uppercase; }
    .event__title { margin: 0 0 var(--wk-space-xs); font-size: 1rem; }
    .event__description { margin: 0; font-size: 0.875rem; color: var(--wk-text-secondary); }
  `]
})
export class TimelineViewerComponent implements OnInit {
  private readonly universeService = inject(UniverseService);

  universeId = input.required<string>();

  readonly eras = signal<TimelineEra[]>([]);
  readonly universeName = signal<string>('');
  readonly isLoading = signal(true);

  readonly categoryLabels: Record<string, string> = {
    political: 'Political',
    war: 'War',
    discovery: 'Discovery',
    catastrophe: 'Catastrophe',
    cultural: 'Cultural',
    magical: 'Magical'
  };

  ngOnInit(): void {
    // Load universe info
    this.universeService.get(this.universeId()).subscribe({
      next: (u) => this.universeName.set(u.name),
      error: () => {}
    });

    // Load timeline - mock data for now (would call universeService.getTimeline in production)
    this.loadTimeline();
  }

  private loadTimeline(): void {
    // Simulate API call - in production this would call a timeline endpoint
    setTimeout(() => {
      // Example data structure - empty by default
      this.eras.set([]);
      this.isLoading.set(false);
    }, 500);
  }
}
