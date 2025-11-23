import { Routes } from '@angular/router';

export const UNIVERSES_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./universe-list/universe-list.component').then(m => m.UniverseListComponent)
  },
  {
    path: 'new',
    loadComponent: () => import('./universe-builder/universe-builder.component').then(m => m.UniverseBuilderComponent)
  },
  {
    path: ':id',
    loadComponent: () => import('./universe-detail/universe-detail.component').then(m => m.UniverseDetailComponent)
  },
  {
    path: ':id/edit',
    loadComponent: () => import('./universe-builder/universe-builder.component').then(m => m.UniverseBuilderComponent)
  }
];
