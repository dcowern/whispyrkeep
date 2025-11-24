import { Routes } from '@angular/router';

export const UNIVERSES_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./universe-list/universe-list.component').then(m => m.UniverseListComponent)
  },
  {
    path: 'new',
    loadComponent: () => import('./universe-mode-select/universe-mode-select.component').then(m => m.UniverseModeSelectComponent)
  },
  {
    path: 'build/:sessionId',
    loadComponent: () => import('./universe-ai-builder/universe-ai-builder.component').then(m => m.UniverseAiBuilderComponent)
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
