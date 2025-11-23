import { Injectable, inject, signal, computed } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, tap, catchError, throwError } from 'rxjs';
import { ApiService } from './api.service';
import { StorageService } from './storage.service';
import {
  User,
  UserSettings,
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  TokenRefreshResponse
} from '../models/api.models';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly api = inject(ApiService);
  private readonly storage = inject(StorageService);
  private readonly router = inject(Router);

  private readonly currentUser = signal<User | null>(null);
  private readonly userSettings = signal<UserSettings | null>(null);

  readonly user = this.currentUser.asReadonly();
  readonly settings = this.userSettings.asReadonly();
  readonly isAuthenticated = this.storage.authenticated;

  login(credentials: LoginRequest): Observable<AuthResponse> {
    return this.api.post<AuthResponse>('/auth/login/', credentials).pipe(
      tap(response => {
        this.storage.setTokens(response.access, response.refresh);
        this.currentUser.set(response.user);
      })
    );
  }

  register(data: RegisterRequest): Observable<AuthResponse> {
    return this.api.post<AuthResponse>('/auth/register/', data).pipe(
      tap(response => {
        this.storage.setTokens(response.access, response.refresh);
        this.currentUser.set(response.user);
      })
    );
  }

  logout(): void {
    this.storage.clearTokens();
    this.currentUser.set(null);
    this.userSettings.set(null);
    this.router.navigate(['/auth/login']);
  }

  refreshToken(): Observable<TokenRefreshResponse> {
    const refreshToken = this.storage.getRefreshToken();
    if (!refreshToken) {
      return throwError(() => new Error('No refresh token available'));
    }

    return this.api.post<TokenRefreshResponse>('/auth/token/refresh/', { refresh: refreshToken }).pipe(
      tap(response => {
        this.storage.setAccessToken(response.access);
      }),
      catchError(error => {
        this.logout();
        return throwError(() => error);
      })
    );
  }

  loadCurrentUser(): Observable<User> {
    return this.api.get<User>('/auth/me/').pipe(
      tap(user => this.currentUser.set(user))
    );
  }

  loadUserSettings(): Observable<UserSettings> {
    return this.api.get<UserSettings>('/auth/settings/').pipe(
      tap(settings => this.userSettings.set(settings))
    );
  }

  updateUserSettings(settings: Partial<UserSettings>): Observable<UserSettings> {
    return this.api.patch<UserSettings>('/auth/settings/', settings).pipe(
      tap(updated => this.userSettings.set(updated))
    );
  }
}
