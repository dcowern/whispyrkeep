import { TestBed } from '@angular/core/testing';
import { Router, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { authGuard, noAuthGuard } from './auth.guard';
import { StorageService } from '../services/storage.service';

describe('Auth Guards', () => {
  let storageService: StorageService;
  let router: Router;

  const mockRoute = {} as ActivatedRouteSnapshot;
  const mockState = { url: '/test' } as RouterStateSnapshot;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        StorageService,
        {
          provide: Router,
          useValue: { navigate: jasmine.createSpy('navigate') }
        }
      ]
    });

    storageService = TestBed.inject(StorageService);
    router = TestBed.inject(Router);
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('authGuard', () => {
    it('should allow access when authenticated', () => {
      storageService.setTokens('access', 'refresh');

      const result = TestBed.runInInjectionContext(() =>
        authGuard(mockRoute, mockState)
      );

      expect(result).toBe(true);
      expect(router.navigate).not.toHaveBeenCalled();
    });

    it('should redirect to login when not authenticated', () => {
      const result = TestBed.runInInjectionContext(() =>
        authGuard(mockRoute, mockState)
      );

      expect(result).toBe(false);
      expect(router.navigate).toHaveBeenCalledWith(['/auth/login']);
    });
  });

  describe('noAuthGuard', () => {
    it('should allow access when not authenticated', () => {
      const result = TestBed.runInInjectionContext(() =>
        noAuthGuard(mockRoute, mockState)
      );

      expect(result).toBe(true);
      expect(router.navigate).not.toHaveBeenCalled();
    });

    it('should redirect to home when authenticated', () => {
      storageService.setTokens('access', 'refresh');

      const result = TestBed.runInInjectionContext(() =>
        noAuthGuard(mockRoute, mockState)
      );

      expect(result).toBe(false);
      expect(router.navigate).toHaveBeenCalledWith(['/home']);
    });
  });
});
