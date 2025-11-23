import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-play',
  standalone: true,
  imports: [RouterLink],
  template: `
    <main id="main-content" class="play">
      <header class="play__header">
        <a routerLink="/campaigns" class="play__back">Back to campaigns</a>
        <h1 class="play__title">Campaign: {{ campaignId() }}</h1>
      </header>
      <div class="play__content">
        <p>Play screen placeholder - Campaign {{ campaignId() }}</p>
      </div>
    </main>
  `,
  styles: [`
    .play {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    .play__header {
      padding: var(--wk-space-md) var(--wk-space-lg);
      border-bottom: 1px solid var(--wk-border);
      background-color: var(--wk-surface);
    }

    .play__back {
      color: var(--wk-text-secondary);
      text-decoration: none;
      font-size: 0.875rem;

      &:hover {
        color: var(--wk-text-primary);
      }
    }

    .play__title {
      font-size: 1.25rem;
      margin: var(--wk-space-sm) 0 0;
    }

    .play__content {
      flex: 1;
      padding: var(--wk-space-lg);
    }
  `]
})
export class PlayComponent {
  campaignId = input.required<string>();
}
