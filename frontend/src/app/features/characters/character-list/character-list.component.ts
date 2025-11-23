import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-character-list',
  standalone: true,
  imports: [RouterLink],
  template: `
    <main id="main-content" class="feature-page">
      <header class="feature-page__header">
        <h1>Characters</h1>
        <a routerLink="new" class="btn btn--primary">Create Character</a>
      </header>
      <div class="feature-page__content">
        <p class="placeholder">Character list placeholder</p>
      </div>
    </main>
  `,
  styleUrl: '../../shared.styles.scss'
})
export class CharacterListComponent {}
