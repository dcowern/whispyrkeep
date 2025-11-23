import { Routes } from '@angular/router';

export const loreRoutes: Routes = [
  {
    path: ':campaignId',
    loadComponent: () => import('./lore-browser/lore-browser.component').then(m => m.LoreBrowserComponent)
  }
];
