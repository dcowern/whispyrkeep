import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService, QueryParams } from './api.service';
import { CharacterSheet, PaginatedResponse } from '../models/api.models';

@Injectable({
  providedIn: 'root'
})
export class CharacterService {
  private readonly api = inject(ApiService);
  private readonly endpoint = '/characters/';

  list(params?: QueryParams): Observable<PaginatedResponse<CharacterSheet>> {
    return this.api.getList<CharacterSheet>(this.endpoint, params);
  }

  get(id: string): Observable<CharacterSheet> {
    return this.api.get<CharacterSheet>(`${this.endpoint}${id}/`);
  }

  create(character: Partial<CharacterSheet>): Observable<CharacterSheet> {
    return this.api.post<CharacterSheet>(this.endpoint, character);
  }

  update(id: string, character: Partial<CharacterSheet>): Observable<CharacterSheet> {
    return this.api.patch<CharacterSheet>(`${this.endpoint}${id}/`, character);
  }

  delete(id: string): Observable<void> {
    return this.api.delete<void>(`${this.endpoint}${id}/`);
  }

  levelUp(id: string): Observable<CharacterSheet> {
    return this.api.post<CharacterSheet>(`${this.endpoint}${id}/level-up/`, {});
  }

  validate(character: Partial<CharacterSheet>): Observable<{ valid: boolean; errors: string[] }> {
    return this.api.post<{ valid: boolean; errors: string[] }>(
      `${this.endpoint}validate/`,
      character
    );
  }
}
