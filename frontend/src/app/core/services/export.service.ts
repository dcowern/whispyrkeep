import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService, QueryParams } from './api.service';
import { ExportJob, ExportJobCreate, PaginatedResponse } from '../models/api.models';

@Injectable({
  providedIn: 'root'
})
export class ExportService {
  private readonly api = inject(ApiService);
  private readonly endpoint = '/exports/';

  list(params?: QueryParams): Observable<PaginatedResponse<ExportJob>> {
    return this.api.getList<ExportJob>(this.endpoint, params);
  }

  get(id: string): Observable<ExportJob> {
    return this.api.get<ExportJob>(`${this.endpoint}${id}/`);
  }

  create(job: ExportJobCreate): Observable<ExportJob> {
    return this.api.post<ExportJob>(this.endpoint, job);
  }

  delete(id: string): Observable<void> {
    return this.api.delete<void>(`${this.endpoint}${id}/`);
  }

  download(id: string): Observable<Blob> {
    return this.api.get<Blob>(`${this.endpoint}${id}/download/`);
  }
}
