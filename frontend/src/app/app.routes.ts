import { Routes } from '@angular/router';
import { authGuard, noAuthGuard } from './core/guards';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'home'
  },
  {
    path: 'auth',
    canActivate: [noAuthGuard],
    loadChildren: () => import('./features/auth/auth.routes').then(m => m.AUTH_ROUTES)
  },
  {
    path: '',
    canActivate: [authGuard],
    loadComponent: () => import('./shared/components/layout/layout.component').then(m => m.LayoutComponent),
    children: [
      {
        path: 'home',
        loadComponent: () => import('./features/dashboard/dashboard.component').then(m => m.DashboardComponent)
      },
      {
        path: 'characters',
        loadChildren: () => import('./features/characters/characters.routes').then(m => m.CHARACTERS_ROUTES)
      },
      {
        path: 'universes',
        loadChildren: () => import('./features/universes/universes.routes').then(m => m.UNIVERSES_ROUTES)
      },
      {
        path: 'campaigns',
        loadChildren: () => import('./features/campaigns/campaigns.routes').then(m => m.CAMPAIGNS_ROUTES)
      },
      {
        path: 'play/:campaignId',
        loadComponent: () => import('./features/play/play.component').then(m => m.PlayComponent)
      },
      {
        path: 'lore',
        loadChildren: () => import('./features/lore/lore.routes').then(m => m.loreRoutes)
      },
      {
        path: 'timeline',
        loadChildren: () => import('./features/timeline/timeline.routes').then(m => m.timelineRoutes)
      },
      {
        path: 'exports',
        loadChildren: () => import('./features/exports/exports.routes').then(m => m.exportsRoutes)
      }
    ]
  },
  {
    path: '**',
    loadComponent: () => import('./features/not-found/not-found.component').then(m => m.NotFoundComponent)
  }
];
