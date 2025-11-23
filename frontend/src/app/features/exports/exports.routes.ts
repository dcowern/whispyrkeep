import { Routes } from '@angular/router';

export const exportsRoutes: Routes = [
  {
    path: '',
    loadComponent: () => import('./export-panel.component').then(m => m.ExportPanelComponent)
  }
];
