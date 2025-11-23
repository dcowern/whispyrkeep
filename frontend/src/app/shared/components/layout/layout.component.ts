import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from '@core/services';
import {
  LucideAngularModule,
  Shield,
  LayoutDashboard,
  Swords,
  Users,
  Globe,
  Settings,
  LogOut,
  ChevronRight
} from 'lucide-angular';

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, RouterOutlet, LucideAngularModule],
  template: `
    <div class="layout">
      <nav class="sidebar" aria-label="Main navigation">
        <div class="sidebar__brand">
          <a routerLink="/home" class="sidebar__logo">
            <div class="sidebar__logo-icon">
              <lucide-icon [img]="ShieldIcon" />
            </div>
            <span class="sidebar__logo-text">WhispyrKeep</span>
          </a>
        </div>

        <ul class="sidebar__nav">
          <li>
            <a routerLink="/home" routerLinkActive="sidebar__link--active" [routerLinkActiveOptions]="{exact: true}" class="sidebar__link">
              <lucide-icon [img]="DashboardIcon" />
              <span>Dashboard</span>
              <lucide-icon [img]="ChevronIcon" class="sidebar__link-arrow" />
            </a>
          </li>
          <li>
            <a routerLink="/campaigns" routerLinkActive="sidebar__link--active" class="sidebar__link">
              <lucide-icon [img]="SwordsIcon" />
              <span>Campaigns</span>
              <lucide-icon [img]="ChevronIcon" class="sidebar__link-arrow" />
            </a>
          </li>
          <li>
            <a routerLink="/characters" routerLinkActive="sidebar__link--active" class="sidebar__link">
              <lucide-icon [img]="UsersIcon" />
              <span>Characters</span>
              <lucide-icon [img]="ChevronIcon" class="sidebar__link-arrow" />
            </a>
          </li>
          <li>
            <a routerLink="/universes" routerLinkActive="sidebar__link--active" class="sidebar__link">
              <lucide-icon [img]="GlobeIcon" />
              <span>Universes</span>
              <lucide-icon [img]="ChevronIcon" class="sidebar__link-arrow" />
            </a>
          </li>
        </ul>

        <div class="sidebar__footer">
          <a routerLink="/settings" class="sidebar__link">
            <lucide-icon [img]="SettingsIcon" />
            <span>Settings</span>
          </a>
          <button (click)="logout()" class="sidebar__link sidebar__link--logout">
            <lucide-icon [img]="LogOutIcon" />
            <span>Logout</span>
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
      width: 260px;
      background: var(--wk-glass-bg);
      backdrop-filter: blur(var(--wk-blur-lg));
      -webkit-backdrop-filter: blur(var(--wk-blur-lg));
      border-right: 1px solid var(--wk-glass-border);
      display: flex;
      flex-direction: column;
      padding: var(--wk-space-4);
      position: relative;

      /* Subtle gradient overlay */
      &::before {
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(180deg, rgba(129, 140, 248, 0.03) 0%, transparent 50%);
        pointer-events: none;
      }
    }

    .sidebar__brand {
      padding: var(--wk-space-4);
      margin-bottom: var(--wk-space-6);
    }

    .sidebar__logo {
      display: flex;
      align-items: center;
      gap: var(--wk-space-3);
      text-decoration: none;
      transition: transform var(--wk-transition-fast);

      &:hover {
        transform: translateX(2px);
      }
    }

    .sidebar__logo-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 40px;
      height: 40px;
      background: linear-gradient(135deg, var(--wk-primary) 0%, var(--wk-primary-dark) 100%);
      border-radius: var(--wk-radius-lg);
      box-shadow: 0 0 15px var(--wk-primary-glow);

      lucide-icon {
        width: 22px;
        height: 22px;
        color: white;
      }
    }

    .sidebar__logo-text {
      font-size: var(--wk-text-lg);
      font-weight: var(--wk-font-bold);
      background: linear-gradient(135deg, var(--wk-text-primary) 0%, var(--wk-primary-light) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .sidebar__nav {
      list-style: none;
      padding: 0;
      margin: 0;
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-1);
    }

    .sidebar__link {
      display: flex;
      align-items: center;
      gap: var(--wk-space-3);
      padding: var(--wk-space-3) var(--wk-space-4);
      color: var(--wk-text-secondary);
      text-decoration: none;
      border-radius: var(--wk-radius-lg);
      font-size: var(--wk-text-sm);
      font-weight: var(--wk-font-medium);
      transition:
        background var(--wk-transition-fast),
        color var(--wk-transition-fast),
        box-shadow var(--wk-transition-fast),
        transform var(--wk-transition-fast);
      position: relative;
      overflow: hidden;

      lucide-icon {
        width: 20px;
        height: 20px;
        flex-shrink: 0;
      }

      span {
        flex: 1;
      }

      .sidebar__link-arrow {
        width: 16px;
        height: 16px;
        opacity: 0;
        transform: translateX(-4px);
        transition: opacity var(--wk-transition-fast), transform var(--wk-transition-fast);
      }

      &:hover {
        background: var(--wk-surface-elevated);
        color: var(--wk-text-primary);
        transform: translateX(2px);

        .sidebar__link-arrow {
          opacity: 0.5;
          transform: translateX(0);
        }
      }

      &--active {
        background: var(--wk-primary-glow);
        color: var(--wk-primary-light);
        box-shadow: 0 0 20px var(--wk-primary-glow);

        &::before {
          content: '';
          position: absolute;
          left: 0;
          top: 50%;
          transform: translateY(-50%);
          width: 3px;
          height: 60%;
          background: var(--wk-primary);
          border-radius: 0 var(--wk-radius-sm) var(--wk-radius-sm) 0;
        }

        lucide-icon:first-child {
          color: var(--wk-primary);
        }

        .sidebar__link-arrow {
          opacity: 0.7;
          transform: translateX(0);
          color: var(--wk-primary);
        }
      }

      &--logout {
        background: none;
        border: none;
        width: 100%;
        text-align: left;
        cursor: pointer;
        font-size: inherit;
        font-family: inherit;

        &:hover {
          color: var(--wk-error);
          background: var(--wk-error-glow);

          lucide-icon {
            color: var(--wk-error);
          }
        }
      }
    }

    .sidebar__footer {
      border-top: 1px solid var(--wk-glass-border);
      padding-top: var(--wk-space-4);
      margin-top: var(--wk-space-4);
      display: flex;
      flex-direction: column;
      gap: var(--wk-space-1);
    }

    .main-content {
      flex: 1;
      overflow-y: auto;
      position: relative;
    }
  `]
})
export class LayoutComponent {
  private readonly authService = inject(AuthService);

  // Lucide icons
  readonly ShieldIcon = Shield;
  readonly DashboardIcon = LayoutDashboard;
  readonly SwordsIcon = Swords;
  readonly UsersIcon = Users;
  readonly GlobeIcon = Globe;
  readonly SettingsIcon = Settings;
  readonly LogOutIcon = LogOut;
  readonly ChevronIcon = ChevronRight;

  logout(): void {
    this.authService.logout();
  }
}
