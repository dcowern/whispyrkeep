import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-campaign-detail',
  standalone: true,
  imports: [RouterLink],
  template: `
    <main id="main-content" class="feature-page">
      <header class="feature-page__header">
        <a routerLink="/campaigns" class="back-link">Back to campaigns</a>
        <h1>Campaign: {{ id() }}</h1>
        <a [routerLink]="['/play', id()]" class="btn btn--primary">Play</a>
      </header>
      <div class="feature-page__content">
        <p class="placeholder">Campaign detail placeholder</p>
      </div>
    </main>
  `,
  styleUrl: '../../shared.styles.scss'
})
export class CampaignDetailComponent {
  id = input.required<string>();
}
