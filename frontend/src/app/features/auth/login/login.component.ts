import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router } from '@angular/router';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { AuthService } from '@core/services';
import { LucideAngularModule, Shield, Mail, Lock, AlertCircle, LogIn, Loader2 } from 'lucide-angular';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, RouterLink, ReactiveFormsModule, LucideAngularModule],
  template: `
    <main id="main-content" class="auth-page">
      <div class="auth-card">
        <div class="auth-card__header">
          <div class="auth-card__logo">
            <lucide-icon [img]="ShieldIcon" />
          </div>
          <h1 class="auth-card__title">Welcome Back</h1>
          <p class="auth-card__subtitle">Sign in to continue your adventure</p>
        </div>

        @if (errorMessage()) {
          <div class="auth-card__error" role="alert">
            <lucide-icon [img]="AlertCircleIcon" />
            {{ errorMessage() }}
          </div>
        }

        <form [formGroup]="loginForm" (ngSubmit)="onSubmit()" class="auth-form">
          <div class="form-group">
            <label for="email" class="form-label">Email</label>
            <div class="form-input-wrapper">
              <span class="form-input-icon">
                <lucide-icon [img]="MailIcon" />
              </span>
              <input
                type="email"
                id="email"
                formControlName="email"
                class="form-input"
                [class.form-input--error]="showError('email')"
                placeholder="Enter your email"
                autocomplete="email"
              />
            </div>
            @if (showError('email')) {
              <span class="form-error">
                <lucide-icon [img]="AlertCircleIcon" />
                Please enter a valid email address
              </span>
            }
          </div>

          <div class="form-group">
            <label for="password" class="form-label">Password</label>
            <div class="form-input-wrapper">
              <span class="form-input-icon">
                <lucide-icon [img]="LockIcon" />
              </span>
              <input
                type="password"
                id="password"
                formControlName="password"
                class="form-input"
                [class.form-input--error]="showError('password')"
                placeholder="Enter your password"
                autocomplete="current-password"
              />
            </div>
            @if (showError('password')) {
              <span class="form-error">
                <lucide-icon [img]="AlertCircleIcon" />
                Password is required
              </span>
            }
          </div>

          <button
            type="submit"
            class="btn btn--primary btn--full"
            [class.btn--loading]="isLoading()"
            [disabled]="isLoading()"
          >
            @if (isLoading()) {
              <lucide-icon [img]="Loader2Icon" class="animate-spin" />
              Signing in...
            } @else {
              <lucide-icon [img]="LogInIcon" />
              Sign In
            }
          </button>
        </form>

        <p class="auth-card__link">
          Don't have an account? <a routerLink="/auth/register">Create one</a>
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

  // Lucide icons
  readonly ShieldIcon = Shield;
  readonly MailIcon = Mail;
  readonly LockIcon = Lock;
  readonly AlertCircleIcon = AlertCircle;
  readonly LogInIcon = LogIn;
  readonly Loader2Icon = Loader2;

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
