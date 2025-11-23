import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService, QueryParams } from './api.service';
import {
  SrdRace,
  SrdClass,
  SrdBackground,
  SrdSpell,
  PaginatedResponse
} from '../models/api.models';

@Injectable({
  providedIn: 'root'
})
export class CatalogService {
  private readonly api = inject(ApiService);
  private readonly endpoint = '/srd/';

  // Species (races in SRD 5.2 terminology)
  listRaces(params?: QueryParams): Observable<PaginatedResponse<SrdRace>> {
    return this.api.getList<SrdRace>(`${this.endpoint}species/`, params);
  }

  getRace(id: string): Observable<SrdRace> {
    return this.api.get<SrdRace>(`${this.endpoint}species/${id}/`);
  }

  // Classes
  listClasses(params?: QueryParams): Observable<PaginatedResponse<SrdClass>> {
    return this.api.getList<SrdClass>(`${this.endpoint}classes/`, params);
  }

  getClass(id: string): Observable<SrdClass> {
    return this.api.get<SrdClass>(`${this.endpoint}classes/${id}/`);
  }

  // Backgrounds
  listBackgrounds(params?: QueryParams): Observable<PaginatedResponse<SrdBackground>> {
    return this.api.getList<SrdBackground>(`${this.endpoint}backgrounds/`, params);
  }

  getBackground(id: string): Observable<SrdBackground> {
    return this.api.get<SrdBackground>(`${this.endpoint}backgrounds/${id}/`);
  }

  // Spells
  listSpells(params?: QueryParams): Observable<PaginatedResponse<SrdSpell>> {
    return this.api.getList<SrdSpell>(`${this.endpoint}spells/`, params);
  }

  getSpell(id: string): Observable<SrdSpell> {
    return this.api.get<SrdSpell>(`${this.endpoint}spells/${id}/`);
  }

  searchSpells(query: string, className?: string): Observable<PaginatedResponse<SrdSpell>> {
    const params: QueryParams = { search: query };
    if (className) {
      params['class'] = className;
    }
    return this.api.getList<SrdSpell>(`${this.endpoint}spells/`, params);
  }
}
