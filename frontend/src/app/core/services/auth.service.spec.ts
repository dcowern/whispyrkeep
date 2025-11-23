import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { AuthService } from './auth.service';
import { StorageService } from './storage.service';
import { environment } from '@env/environment';

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;
  let storageService: StorageService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        AuthService,
        StorageService
      ]
    });
    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
    storageService = TestBed.inject(StorageService);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('login', () => {
    it('should authenticate and store tokens', () => {
      const credentials = { email: 'test@example.com', password: 'password' };
      const response = {
        access: 'access-token',
        refresh: 'refresh-token',
        user: { id: '1', email: 'test@example.com', username: 'testuser', created_at: '', updated_at: '' }
      };

      service.login(credentials).subscribe(data => {
        expect(data.user.email).toBe('test@example.com');
        expect(storageService.getAccessToken()).toBe('access-token');
        expect(storageService.getRefreshToken()).toBe('refresh-token');
        expect(service.isAuthenticated()).toBe(true);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/auth/login/`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(credentials);
      req.flush(response);
    });
  });

  describe('register', () => {
    it('should register and store tokens', () => {
      const registerData = {
        email: 'new@example.com',
        username: 'newuser',
        password: 'password',
        password_confirm: 'password'
      };
      const response = {
        access: 'access-token',
        refresh: 'refresh-token',
        user: { id: '1', email: 'new@example.com', username: 'newuser', created_at: '', updated_at: '' }
      };

      service.register(registerData).subscribe(data => {
        expect(data.user.email).toBe('new@example.com');
        expect(service.isAuthenticated()).toBe(true);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/auth/register/`);
      req.flush(response);
    });
  });

  describe('logout', () => {
    it('should clear tokens and user state', () => {
      // Setup: login first
      storageService.setTokens('access', 'refresh');

      service.logout();

      expect(storageService.getAccessToken()).toBeNull();
      expect(storageService.getRefreshToken()).toBeNull();
      expect(service.isAuthenticated()).toBe(false);
      expect(service.user()).toBeNull();
    });
  });

  describe('refreshToken', () => {
    it('should refresh access token', () => {
      storageService.setTokens('old-access', 'refresh-token');
      const response = { access: 'new-access-token' };

      service.refreshToken().subscribe(() => {
        expect(storageService.getAccessToken()).toBe('new-access-token');
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/auth/token/refresh/`);
      expect(req.request.body).toEqual({ refresh: 'refresh-token' });
      req.flush(response);
    });
  });

  describe('loadCurrentUser', () => {
    it('should load and store current user', () => {
      const user = { id: '1', email: 'test@example.com', username: 'testuser', created_at: '', updated_at: '' };

      service.loadCurrentUser().subscribe(() => {
        expect(service.user()).toEqual(user);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/auth/me/`);
      req.flush(user);
    });
  });
});
