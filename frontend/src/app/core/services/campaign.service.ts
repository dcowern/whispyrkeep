import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService, QueryParams } from './api.service';
import { Campaign, CampaignCreate, TurnEvent, PaginatedResponse, LoreEntry } from '../models/api.models';

export interface TurnInput {
  player_input: string;
}

export interface TurnResponse {
  turn: TurnEvent;
  narrative: string;
}

export interface RewindResult {
  campaign: Campaign;
  turns_removed: number;
}

@Injectable({
  providedIn: 'root'
})
export class CampaignService {
  private readonly api = inject(ApiService);
  private readonly endpoint = '/campaigns/';

  list(params?: QueryParams): Observable<PaginatedResponse<Campaign>> {
    return this.api.getList<Campaign>(this.endpoint, params);
  }

  get(id: string): Observable<Campaign> {
    return this.api.get<Campaign>(`${this.endpoint}${id}/`);
  }

  create(campaign: CampaignCreate): Observable<Campaign> {
    return this.api.post<Campaign>(this.endpoint, campaign);
  }

  update(id: string, campaign: Partial<CampaignCreate>): Observable<Campaign> {
    return this.api.patch<Campaign>(`${this.endpoint}${id}/`, campaign);
  }

  delete(id: string): Observable<void> {
    return this.api.delete<void>(`${this.endpoint}${id}/`);
  }

  // Turn management
  listTurns(campaignId: string, params?: QueryParams): Observable<PaginatedResponse<TurnEvent>> {
    return this.api.getList<TurnEvent>(`${this.endpoint}${campaignId}/turns/`, params);
  }

  getTurn(campaignId: string, turnId: string): Observable<TurnEvent> {
    return this.api.get<TurnEvent>(`${this.endpoint}${campaignId}/turns/${turnId}/`);
  }

  submitTurn(campaignId: string, input: TurnInput): Observable<TurnResponse> {
    return this.api.post<TurnResponse>(`${this.endpoint}${campaignId}/turns/`, input);
  }

  // Rewind
  rewind(campaignId: string, toTurnSequence: number): Observable<RewindResult> {
    return this.api.post<RewindResult>(`${this.endpoint}${campaignId}/rewind/`, {
      to_turn_sequence: toTurnSequence
    });
  }

  // State
  getCurrentState(campaignId: string): Observable<Record<string, unknown>> {
    return this.api.get<Record<string, unknown>>(`${this.endpoint}${campaignId}/state/`);
  }

  // Lore
  getLore(campaignId: string): Observable<LoreEntry[]> {
    return this.api.get<LoreEntry[]>(`${this.endpoint}${campaignId}/lore/`);
  }
}
