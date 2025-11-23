import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [RouterLink],
  template: `
    <main id="main-content" class="auth-page">
      <div class="auth-card">
        <h1 class="auth-card__title">Register</h1>
        <p class="auth-card__subtitle">Create your WhispyrKeep account</p>
        <p class="auth-card__placeholder">Registration form placeholder</p>
        <p class="auth-card__link">
          Already have an account? <a routerLink="/auth/login">Login</a>
        </p>
      </div>
    </main>
  `,
  styleUrl: '../auth.styles.scss'
})
export class RegisterComponent {}
