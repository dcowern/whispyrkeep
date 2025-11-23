import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService, QueryParams } from './api.service';
import { Universe, UniverseCreate, LoreDocument, PaginatedResponse, LoreSearchResult } from '../models/api.models';

@Injectable({
  providedIn: 'root'
})
export class UniverseService {
  private readonly api = inject(ApiService);
  private readonly endpoint = '/universes/';

  list(params?: QueryParams): Observable<PaginatedResponse<Universe>> {
    return this.api.getList<Universe>(this.endpoint, params);
  }

  get(id: string): Observable<Universe> {
    return this.api.get<Universe>(`${this.endpoint}${id}/`);
  }

  create(universe: UniverseCreate): Observable<Universe> {
    return this.api.post<Universe>(this.endpoint, universe);
  }

  update(id: string, universe: Partial<UniverseCreate>): Observable<Universe> {
    return this.api.patch<Universe>(`${this.endpoint}${id}/`, universe);
  }

  delete(id: string): Observable<void> {
    return this.api.delete<void>(`${this.endpoint}${id}/`);
  }

  // Worldgen endpoints
  generateWithLlm(id: string, prompt: string): Observable<{ content: string }> {
    return this.api.post<{ content: string }>(`${this.endpoint}${id}/generate/`, { prompt });
  }

  // Lore management
  listLore(universeId: string, params?: QueryParams): Observable<PaginatedResponse<LoreDocument>> {
    return this.api.getList<LoreDocument>(`${this.endpoint}${universeId}/lore/`, params);
  }

  uploadLore(universeId: string, file: File, category: 'hard_canon' | 'soft_lore'): Observable<LoreDocument> {
    return this.api.upload<LoreDocument>(`${this.endpoint}${universeId}/lore/upload/`, file, { category });
  }

  searchLore(universeId: string, query: string, limit = 10): Observable<LoreSearchResult[]> {
    return this.api.get<LoreSearchResult[]>(`${this.endpoint}${universeId}/lore/search/`, {
      query,
      limit
    });
  }

  deleteLore(universeId: string, loreId: string): Observable<void> {
    return this.api.delete<void>(`${this.endpoint}${universeId}/lore/${loreId}/`);
  }
}
