import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-universe-builder',
  standalone: true,
  imports: [RouterLink],
  template: `
    <main id="main-content" class="feature-page">
      <header class="feature-page__header">
        <a routerLink="/universes" class="back-link">Back to universes</a>
        <h1>{{ id() ? 'Edit Universe' : 'Create Universe' }}</h1>
      </header>
      <div class="feature-page__content">
        <p class="placeholder">Universe builder placeholder</p>
      </div>
    </main>
  `,
  styleUrl: '../../shared.styles.scss'
})
export class UniverseBuilderComponent {
  id = input<string>();
}
