import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-character-detail',
  standalone: true,
  imports: [RouterLink],
  template: `
    <main id="main-content" class="feature-page">
      <header class="feature-page__header">
        <a routerLink="/characters" class="back-link">Back to characters</a>
        <h1>Character: {{ id() }}</h1>
        <a [routerLink]="['/characters', id(), 'edit']" class="btn">Edit</a>
      </header>
      <div class="feature-page__content">
        <p class="placeholder">Character detail placeholder</p>
      </div>
    </main>
  `,
  styleUrl: '../../shared.styles.scss'
})
export class CharacterDetailComponent {
  id = input.required<string>();
}
