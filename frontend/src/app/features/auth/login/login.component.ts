import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router } from '@angular/router';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { AuthService } from '@core/services';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, RouterLink, ReactiveFormsModule],
  template: `
    <main id="main-content" class="auth-page">
      <div class="auth-card">
        <h1 class="auth-card__title">Login</h1>
        <p class="auth-card__subtitle">Welcome back to WhispyrKeep</p>

        @if (errorMessage()) {
          <div class="auth-card__error" role="alert">
            {{ errorMessage() }}
          </div>
        }

        <form [formGroup]="loginForm" (ngSubmit)="onSubmit()" class="auth-form">
          <div class="form-group">
            <label for="email" class="form-label">Email</label>
            <input
              type="email"
              id="email"
              formControlName="email"
              class="form-input"
              [class.form-input--error]="showError('email')"
              autocomplete="email"
            />
            @if (showError('email')) {
              <span class="form-error">Please enter a valid email address</span>
            }
          </div>

          <div class="form-group">
            <label for="password" class="form-label">Password</label>
            <input
              type="password"
              id="password"
              formControlName="password"
              class="form-input"
              [class.form-input--error]="showError('password')"
              autocomplete="current-password"
            />
            @if (showError('password')) {
              <span class="form-error">Password is required</span>
            }
          </div>

          <button
            type="submit"
            class="btn btn--primary btn--full"
            [disabled]="isLoading()"
          >
            {{ isLoading() ? 'Logging in...' : 'Login' }}
          </button>
        </form>

        <p class="auth-card__link">
          Don't have an account? <a routerLink="/auth/register">Register</a>
        </p>
      </div>
    </main>
  `,
  styleUrl: '../auth.styles.scss'
})
export class LoginComponent {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  readonly isLoading = signal(false);
  readonly errorMessage = signal<string | null>(null);

  readonly loginForm = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]]
  });

  showError(field: 'email' | 'password'): boolean {
    const control = this.loginForm.get(field);
    return !!control && control.invalid && (control.dirty || control.touched);
  }

  onSubmit(): void {
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      return;
    }

    this.isLoading.set(true);
    this.errorMessage.set(null);

    const { email, password } = this.loginForm.getRawValue();

    this.authService.login({ email, password }).subscribe({
      next: () => {
        this.router.navigate(['/home']);
      },
      error: (err) => {
        this.isLoading.set(false);
        this.errorMessage.set(err.error?.detail || 'Login failed. Please check your credentials.');
      }
    });
  }
}
