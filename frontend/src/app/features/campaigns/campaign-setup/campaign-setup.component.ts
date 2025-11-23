import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-campaign-setup',
  standalone: true,
  imports: [RouterLink],
  template: `
    <main id="main-content" class="feature-page">
      <header class="feature-page__header">
        <a routerLink="/campaigns" class="back-link">Back to campaigns</a>
        <h1>New Campaign</h1>
      </header>
      <div class="feature-page__content">
        <p class="placeholder">Campaign setup placeholder</p>
      </div>
    </main>
  `,
  styleUrl: '../../shared.styles.scss'
})
export class CampaignSetupComponent {}
