import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { ApiService } from './api.service';
import { environment } from '@env/environment';

describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        ApiService
      ]
    });
    service = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('get', () => {
    it('should make GET request to correct URL', () => {
      const testData = { id: '1', name: 'Test' };

      service.get('/test/').subscribe(data => {
        expect(data).toEqual(testData);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/test/`);
      expect(req.request.method).toBe('GET');
      req.flush(testData);
    });

    it('should include query params', () => {
      service.get('/test/', { page: 1, search: 'foo' }).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/test/?page=1&search=foo`);
      expect(req.request.method).toBe('GET');
      req.flush({});
    });
  });

  describe('getList', () => {
    it('should return paginated response', () => {
      const paginatedData = {
        count: 1,
        next: null,
        previous: null,
        results: [{ id: '1' }]
      };

      service.getList('/items/').subscribe(data => {
        expect(data.count).toBe(1);
        expect(data.results.length).toBe(1);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/items/`);
      req.flush(paginatedData);
    });
  });

  describe('post', () => {
    it('should make POST request with body', () => {
      const body = { name: 'New Item' };
      const response = { id: '1', name: 'New Item' };

      service.post('/items/', body).subscribe(data => {
        expect(data).toEqual(response);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/items/`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(body);
      req.flush(response);
    });
  });

  describe('patch', () => {
    it('should make PATCH request with body', () => {
      const body = { name: 'Updated' };
      const response = { id: '1', name: 'Updated' };

      service.patch('/items/1/', body).subscribe(data => {
        expect(data).toEqual(response);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/items/1/`);
      expect(req.request.method).toBe('PATCH');
      req.flush(response);
    });
  });

  describe('delete', () => {
    it('should make DELETE request', () => {
      service.delete('/items/1/').subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/items/1/`);
      expect(req.request.method).toBe('DELETE');
      req.flush(null);
    });
  });
});
