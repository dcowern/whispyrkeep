import { Injectable, signal } from '@angular/core';

const TOKEN_KEY = 'wk_access_token';
const REFRESH_TOKEN_KEY = 'wk_refresh_token';

@Injectable({
  providedIn: 'root'
})
export class StorageService {
  private readonly isAuthenticated = signal(false);

  constructor() {
    // Check if tokens exist on init
    this.isAuthenticated.set(!!this.getAccessToken());
  }

  readonly authenticated = this.isAuthenticated.asReadonly();

  getAccessToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  }

  setTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem(TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    this.isAuthenticated.set(true);
  }

  setAccessToken(accessToken: string): void {
    localStorage.setItem(TOKEN_KEY, accessToken);
  }

  clearTokens(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    this.isAuthenticated.set(false);
  }
}
