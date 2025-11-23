import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-not-found',
  standalone: true,
  imports: [RouterLink],
  template: `
    <main id="main-content" class="not-found">
      <h1 class="not-found__title">404</h1>
      <p class="not-found__message">Page not found</p>
      <a routerLink="/" class="not-found__link">Return home</a>
    </main>
  `,
  styles: [`
    .not-found {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      text-align: center;
    }

    .not-found__title {
      font-size: 6rem;
      font-weight: 700;
      color: var(--wk-text-muted);
      margin: 0;
    }

    .not-found__message {
      font-size: 1.5rem;
      color: var(--wk-text-secondary);
      margin: var(--wk-space-md) 0 var(--wk-space-xl);
    }

    .not-found__link {
      color: var(--wk-primary);
      text-decoration: none;
      font-weight: 500;

      &:hover {
        text-decoration: underline;
      }
    }
  `]
})
export class NotFoundComponent {}
