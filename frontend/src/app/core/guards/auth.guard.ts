import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { StorageService } from '../services/storage.service';

export const authGuard: CanActivateFn = () => {
  const storageService = inject(StorageService);
  const router = inject(Router);

  if (storageService.authenticated()) {
    return true;
  }

  router.navigate(['/auth/login']);
  return false;
};

export const noAuthGuard: CanActivateFn = () => {
  const storageService = inject(StorageService);
  const router = inject(Router);

  if (!storageService.authenticated()) {
    return true;
  }

  router.navigate(['/home']);
  return false;
};
