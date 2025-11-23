import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [RouterLink],
  template: `
    <main id="main-content" class="home">
      <header class="home__header">
        <h1 class="home__title">WhispyrKeep</h1>
        <p class="home__subtitle">LLM-powered single-player RPG</p>
      </header>

      <nav class="home__nav" aria-label="Main navigation">
        <a routerLink="/auth/login" class="home__link">Login</a>
        <a routerLink="/auth/register" class="home__link home__link--primary">Get Started</a>
      </nav>
    </main>
  `,
  styles: [`
    .home {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      padding: var(--wk-space-xl);
      text-align: center;
    }

    .home__header {
      margin-bottom: var(--wk-space-xl);
    }

    .home__title {
      font-size: 3rem;
      font-weight: 700;
      color: var(--wk-text-primary);
      margin: 0 0 var(--wk-space-sm);
    }

    .home__subtitle {
      font-size: 1.25rem;
      color: var(--wk-text-secondary);
      margin: 0;
    }

    .home__nav {
      display: flex;
      gap: var(--wk-space-md);
    }

    .home__link {
      padding: var(--wk-space-sm) var(--wk-space-lg);
      border-radius: var(--wk-radius-md);
      text-decoration: none;
      font-weight: 500;
      transition: background-color 0.2s, color 0.2s;
      color: var(--wk-text-secondary);
      border: 1px solid var(--wk-border);

      &:hover {
        background-color: var(--wk-surface);
        color: var(--wk-text-primary);
      }

      &--primary {
        background-color: var(--wk-primary);
        color: var(--wk-text-primary);
        border-color: var(--wk-primary);

        &:hover {
          background-color: var(--wk-primary-dark);
        }
      }
    }
  `]
})
export class HomeComponent {}
