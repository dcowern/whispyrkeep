import { Routes } from '@angular/router';

export const timelineRoutes: Routes = [
  {
    path: ':universeId',
    loadComponent: () => import('./timeline-viewer.component').then(m => m.TimelineViewerComponent)
  }
];
