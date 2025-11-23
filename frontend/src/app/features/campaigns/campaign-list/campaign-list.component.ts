import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-campaign-list',
  standalone: true,
  imports: [RouterLink],
  template: `
    <main id="main-content" class="feature-page">
      <header class="feature-page__header">
        <h1>Campaigns</h1>
        <a routerLink="new" class="btn btn--primary">New Campaign</a>
      </header>
      <div class="feature-page__content">
        <p class="placeholder">Campaign list placeholder</p>
      </div>
    </main>
  `,
  styleUrl: '../../shared.styles.scss'
})
export class CampaignListComponent {}
