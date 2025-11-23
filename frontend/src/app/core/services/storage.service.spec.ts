import { TestBed } from '@angular/core/testing';
import { StorageService } from './storage.service';

describe('StorageService', () => {
  let service: StorageService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [StorageService]
    });
    localStorage.clear();
    service = TestBed.inject(StorageService);
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('token management', () => {
    it('should store and retrieve access token', () => {
      service.setTokens('access', 'refresh');
      expect(service.getAccessToken()).toBe('access');
    });

    it('should store and retrieve refresh token', () => {
      service.setTokens('access', 'refresh');
      expect(service.getRefreshToken()).toBe('refresh');
    });

    it('should return null when no tokens exist', () => {
      expect(service.getAccessToken()).toBeNull();
      expect(service.getRefreshToken()).toBeNull();
    });

    it('should clear tokens', () => {
      service.setTokens('access', 'refresh');
      service.clearTokens();
      expect(service.getAccessToken()).toBeNull();
      expect(service.getRefreshToken()).toBeNull();
    });

    it('should update access token independently', () => {
      service.setTokens('old-access', 'refresh');
      service.setAccessToken('new-access');
      expect(service.getAccessToken()).toBe('new-access');
      expect(service.getRefreshToken()).toBe('refresh');
    });
  });

  describe('authenticated signal', () => {
    it('should return false initially when no tokens', () => {
      expect(service.authenticated()).toBe(false);
    });

    it('should return true after setting tokens', () => {
      service.setTokens('access', 'refresh');
      expect(service.authenticated()).toBe(true);
    });

    it('should return false after clearing tokens', () => {
      service.setTokens('access', 'refresh');
      service.clearTokens();
      expect(service.authenticated()).toBe(false);
    });
  });
});
