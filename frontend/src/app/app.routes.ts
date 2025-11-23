import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'home'
  },
  {
    path: 'home',
    loadComponent: () => import('./features/home/home.component').then(m => m.HomeComponent)
  },
  {
    path: 'auth',
    loadChildren: () => import('./features/auth/auth.routes').then(m => m.AUTH_ROUTES)
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
    path: '**',
    loadComponent: () => import('./features/not-found/not-found.component').then(m => m.NotFoundComponent)
  }
];
