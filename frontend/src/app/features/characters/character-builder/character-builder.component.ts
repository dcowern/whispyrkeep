import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-character-builder',
  standalone: true,
  imports: [RouterLink],
  template: `
    <main id="main-content" class="feature-page">
      <header class="feature-page__header">
        <a routerLink="/characters" class="back-link">Back to characters</a>
        <h1>{{ id() ? 'Edit Character' : 'Create Character' }}</h1>
      </header>
      <div class="feature-page__content">
        <p class="placeholder">Character builder placeholder</p>
      </div>
    </main>
  `,
  styleUrl: '../../shared.styles.scss'
})
export class CharacterBuilderComponent {
  id = input<string>();
}
