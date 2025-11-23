import { Routes } from '@angular/router';

export const CHARACTERS_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./character-list/character-list.component').then(m => m.CharacterListComponent)
  },
  {
    path: 'new',
    loadComponent: () => import('./character-builder/character-builder.component').then(m => m.CharacterBuilderComponent)
  },
  {
    path: ':id',
    loadComponent: () => import('./character-detail/character-detail.component').then(m => m.CharacterDetailComponent)
  },
  {
    path: ':id/edit',
    loadComponent: () => import('./character-builder/character-builder.component').then(m => m.CharacterBuilderComponent)
  }
];
