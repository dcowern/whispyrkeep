import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router } from '@angular/router';
import { FormBuilder, ReactiveFormsModule, Validators, AbstractControl, ValidationErrors } from '@angular/forms';
import { AuthService } from '@core/services';
import { LucideAngularModule, UserPlus, Mail, User, Lock, KeyRound, AlertCircle, Loader2 } from 'lucide-angular';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, RouterLink, ReactiveFormsModule, LucideAngularModule],
  template: `
    <main id="main-content" class="auth-page">
      <div class="auth-card">
        <div class="auth-card__header">
          <div class="auth-card__logo">
            <lucide-icon [img]="UserPlusIcon" />
          </div>
          <h1 class="auth-card__title">Create Account</h1>
          <p class="auth-card__subtitle">Begin your adventure in WhispyrKeep</p>
        </div>

        @if (errorMessage()) {
          <div class="auth-card__error" role="alert">
            <lucide-icon [img]="AlertCircleIcon" />
            {{ errorMessage() }}
          </div>
        }

        <form [formGroup]="registerForm" (ngSubmit)="onSubmit()" class="auth-form">
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
            <label for="username" class="form-label">Username</label>
            <div class="form-input-wrapper">
              <span class="form-input-icon">
                <lucide-icon [img]="UserIcon" />
              </span>
              <input
                type="text"
                id="username"
                formControlName="username"
                class="form-input"
                [class.form-input--error]="showError('username')"
                placeholder="Choose a username"
                autocomplete="username"
              />
            </div>
            @if (showError('username')) {
              <span class="form-error">
                <lucide-icon [img]="AlertCircleIcon" />
                Username must be 3-30 characters
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
                placeholder="Create a password"
                autocomplete="new-password"
              />
            </div>
            @if (showError('password')) {
              <span class="form-error">
                <lucide-icon [img]="AlertCircleIcon" />
                Password must be at least 8 characters
              </span>
            }
          </div>

          <div class="form-group">
            <label for="password_confirm" class="form-label">Confirm Password</label>
            <div class="form-input-wrapper">
              <span class="form-input-icon">
                <lucide-icon [img]="KeyRoundIcon" />
              </span>
              <input
                type="password"
                id="password_confirm"
                formControlName="password_confirm"
                class="form-input"
                [class.form-input--error]="showError('password_confirm')"
                placeholder="Confirm your password"
                autocomplete="new-password"
              />
            </div>
            @if (showError('password_confirm')) {
              <span class="form-error">
                <lucide-icon [img]="AlertCircleIcon" />
                Passwords must match
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
              Creating account...
            } @else {
              <lucide-icon [img]="UserPlusIcon" />
              Create Account
            }
          </button>
        </form>

        <p class="auth-card__link">
          Already have an account? <a routerLink="/auth/login">Sign in</a>
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

  // Lucide icons
  readonly UserPlusIcon = UserPlus;
  readonly MailIcon = Mail;
  readonly UserIcon = User;
  readonly LockIcon = Lock;
  readonly KeyRoundIcon = KeyRound;
  readonly AlertCircleIcon = AlertCircle;
  readonly Loader2Icon = Loader2;

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
