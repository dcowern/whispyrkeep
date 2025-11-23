import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService, QueryParams } from './api.service';
import { LlmEndpointConfig, LlmEndpointConfigCreate, PaginatedResponse } from '../models/api.models';

@Injectable({
  providedIn: 'root'
})
export class LlmConfigService {
  private readonly api = inject(ApiService);
  private readonly endpoint = '/llm-config/';

  list(params?: QueryParams): Observable<PaginatedResponse<LlmEndpointConfig>> {
    return this.api.getList<LlmEndpointConfig>(this.endpoint, params);
  }

  get(id: string): Observable<LlmEndpointConfig> {
    return this.api.get<LlmEndpointConfig>(`${this.endpoint}${id}/`);
  }

  create(config: LlmEndpointConfigCreate): Observable<LlmEndpointConfig> {
    return this.api.post<LlmEndpointConfig>(this.endpoint, config);
  }

  update(id: string, config: Partial<LlmEndpointConfigCreate>): Observable<LlmEndpointConfig> {
    return this.api.patch<LlmEndpointConfig>(`${this.endpoint}${id}/`, config);
  }

  delete(id: string): Observable<void> {
    return this.api.delete<void>(`${this.endpoint}${id}/`);
  }

  setDefault(id: string): Observable<LlmEndpointConfig> {
    return this.api.post<LlmEndpointConfig>(`${this.endpoint}${id}/set-default/`, {});
  }

  testConnection(id: string): Observable<{ success: boolean; message: string }> {
    return this.api.post<{ success: boolean; message: string }>(
      `${this.endpoint}${id}/test/`,
      {}
    );
  }
}
