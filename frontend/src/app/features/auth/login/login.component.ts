import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [RouterLink],
  template: `
    <main id="main-content" class="auth-page">
      <div class="auth-card">
        <h1 class="auth-card__title">Login</h1>
        <p class="auth-card__subtitle">Welcome back to WhispyrKeep</p>
        <p class="auth-card__placeholder">Login form placeholder</p>
        <p class="auth-card__link">
          Don't have an account? <a routerLink="/auth/register">Register</a>
        </p>
      </div>
    </main>
  `,
  styleUrl: '../auth.styles.scss'
})
export class LoginComponent {}
