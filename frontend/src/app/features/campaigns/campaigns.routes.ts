import { Routes } from '@angular/router';

export const CAMPAIGNS_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./campaign-list/campaign-list.component').then(m => m.CampaignListComponent)
  },
  {
    path: 'new',
    loadComponent: () => import('./campaign-setup/campaign-setup.component').then(m => m.CampaignSetupComponent)
  },
  {
    path: ':id',
    loadComponent: () => import('./campaign-detail/campaign-detail.component').then(m => m.CampaignDetailComponent)
  }
];
