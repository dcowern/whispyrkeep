import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router } from '@angular/router';
import { FormBuilder, ReactiveFormsModule, Validators, AbstractControl, ValidationErrors } from '@angular/forms';
import { AuthService } from '@core/services';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, RouterLink, ReactiveFormsModule],
  template: `
    <main id="main-content" class="auth-page">
      <div class="auth-card">
        <h1 class="auth-card__title">Register</h1>
        <p class="auth-card__subtitle">Create your WhispyrKeep account</p>

        @if (errorMessage()) {
          <div class="auth-card__error" role="alert">
            {{ errorMessage() }}
          </div>
        }

        <form [formGroup]="registerForm" (ngSubmit)="onSubmit()" class="auth-form">
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
            <label for="username" class="form-label">Username</label>
            <input
              type="text"
              id="username"
              formControlName="username"
              class="form-input"
              [class.form-input--error]="showError('username')"
              autocomplete="username"
            />
            @if (showError('username')) {
              <span class="form-error">Username must be 3-30 characters</span>
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
              autocomplete="new-password"
            />
            @if (showError('password')) {
              <span class="form-error">Password must be at least 8 characters</span>
            }
          </div>

          <div class="form-group">
            <label for="password_confirm" class="form-label">Confirm Password</label>
            <input
              type="password"
              id="password_confirm"
              formControlName="password_confirm"
              class="form-input"
              [class.form-input--error]="showError('password_confirm')"
              autocomplete="new-password"
            />
            @if (showError('password_confirm')) {
              <span class="form-error">Passwords must match</span>
            }
          </div>

          <button
            type="submit"
            class="btn btn--primary btn--full"
            [disabled]="isLoading()"
          >
            {{ isLoading() ? 'Creating account...' : 'Create Account' }}
          </button>
        </form>

        <p class="auth-card__link">
          Already have an account? <a routerLink="/auth/login">Login</a>
        </p>
      </div>
    </main>
  `,
  styleUrl: '../auth.styles.scss'
})
export class RegisterComponent {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  readonly isLoading = signal(false);
  readonly errorMessage = signal<string | null>(null);

  readonly registerForm = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    username: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(30)]],
    password: ['', [Validators.required, Validators.minLength(8)]],
    password_confirm: ['', [Validators.required]]
  }, { validators: this.passwordMatchValidator });

  private passwordMatchValidator(control: AbstractControl): ValidationErrors | null {
    const password = control.get('password');
    const confirm = control.get('password_confirm');
    if (password && confirm && password.value !== confirm.value) {
      confirm.setErrors({ passwordMismatch: true });
      return { passwordMismatch: true };
    }
    return null;
  }

  showError(field: 'email' | 'username' | 'password' | 'password_confirm'): boolean {
    const control = this.registerForm.get(field);
    return !!control && control.invalid && (control.dirty || control.touched);
  }

  onSubmit(): void {
    if (this.registerForm.invalid) {
      this.registerForm.markAllAsTouched();
      return;
    }

    this.isLoading.set(true);
    this.errorMessage.set(null);

    const formData = this.registerForm.getRawValue();

    this.authService.register(formData).subscribe({
      next: () => {
        this.router.navigate(['/home']);
      },
      error: (err) => {
        this.isLoading.set(false);
        const message = err.error?.detail ||
          Object.values(err.error?.errors || {}).flat().join(', ') ||
          'Registration failed. Please try again.';
        this.errorMessage.set(message);
      }
    });
  }
}
