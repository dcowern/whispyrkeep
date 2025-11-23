import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { StorageService } from '../services/storage.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const storageService = inject(StorageService);
  const router = inject(Router);

  const token = storageService.getAccessToken();

  // Clone request with auth header if token exists
  const authReq = token
    ? req.clone({
        setHeaders: {
          Authorization: `Bearer ${token}`
        }
      })
    : req;

  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      // Handle 401 errors by clearing tokens and redirecting to login
      if (error.status === 401 && !req.url.includes('/auth/')) {
        storageService.clearTokens();
        router.navigate(['/auth/login']);
      }
      return throwError(() => error);
    })
  );
};
