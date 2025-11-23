import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-universe-detail',
  standalone: true,
  imports: [RouterLink],
  template: `
    <main id="main-content" class="feature-page">
      <header class="feature-page__header">
        <a routerLink="/universes" class="back-link">Back to universes</a>
        <h1>Universe: {{ id() }}</h1>
        <a [routerLink]="['/universes', id(), 'edit']" class="btn">Edit</a>
      </header>
      <div class="feature-page__content">
        <p class="placeholder">Universe detail placeholder</p>
      </div>
    </main>
  `,
  styleUrl: '../../shared.styles.scss'
})
export class UniverseDetailComponent {
  id = input.required<string>();
}
