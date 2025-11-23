import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterOutlet } from '@angular/router';
import { AuthService } from '@core/services';

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterOutlet],
  template: `
    <div class="layout">
      <nav class="sidebar" aria-label="Main navigation">
        <div class="sidebar__brand">
          <a routerLink="/home" class="sidebar__logo">WhispyrKeep</a>
        </div>

        <ul class="sidebar__nav">
          <li><a routerLink="/home" class="sidebar__link">Dashboard</a></li>
          <li><a routerLink="/campaigns" class="sidebar__link">Campaigns</a></li>
          <li><a routerLink="/characters" class="sidebar__link">Characters</a></li>
          <li><a routerLink="/universes" class="sidebar__link">Universes</a></li>
        </ul>

        <div class="sidebar__footer">
          <button (click)="logout()" class="sidebar__link sidebar__link--logout">
            Logout
          </button>
        </div>
      </nav>

      <main class="main-content" id="main-content">
        <router-outlet />
      </main>
    </div>
  `,
  styles: [`
    .layout {
      display: flex;
      min-height: 100vh;
    }

    .sidebar {
      width: 240px;
      background-color: var(--wk-surface);
      border-right: 1px solid var(--wk-border);
      display: flex;
      flex-direction: column;
      padding: var(--wk-space-md);
    }

    .sidebar__brand {
      padding: var(--wk-space-md);
      margin-bottom: var(--wk-space-lg);
    }

    .sidebar__logo {
      font-size: 1.25rem;
      font-weight: 700;
      color: var(--wk-text-primary);
      text-decoration: none;
    }

    .sidebar__nav {
      list-style: none;
      padding: 0;
      margin: 0;
      flex: 1;
    }

    .sidebar__link {
      display: block;
      padding: var(--wk-space-sm) var(--wk-space-md);
      color: var(--wk-text-secondary);
      text-decoration: none;
      border-radius: var(--wk-radius-md);
      transition: background-color 0.2s, color 0.2s;
      margin-bottom: var(--wk-space-xs);

      &:hover {
        background-color: var(--wk-surface-elevated);
        color: var(--wk-text-primary);
      }

      &--logout {
        background: none;
        border: none;
        width: 100%;
        text-align: left;
        cursor: pointer;
        font-size: inherit;
      }
    }

    .sidebar__footer {
      border-top: 1px solid var(--wk-border);
      padding-top: var(--wk-space-md);
    }

    .main-content {
      flex: 1;
      overflow-y: auto;
    }
  `]
})
export class LayoutComponent {
  private readonly authService = inject(AuthService);

  logout(): void {
    this.authService.logout();
  }
}
