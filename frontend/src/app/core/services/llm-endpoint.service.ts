import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import {
  LlmModelListRequest,
  LlmModelListResponse,
  LlmValidationRequest,
  LlmValidationResponse
} from '../models/api.models';

@Injectable({
  providedIn: 'root'
})
export class LlmEndpointService {
  private readonly api = inject(ApiService);

  listModels(payload: LlmModelListRequest): Observable<LlmModelListResponse> {
    return this.api.post<LlmModelListResponse>('/llm/models/', payload);
  }

  validate(payload: LlmValidationRequest): Observable<LlmValidationResponse> {
    return this.api.post<LlmValidationResponse>('/llm/validate/', payload);
  }
}
