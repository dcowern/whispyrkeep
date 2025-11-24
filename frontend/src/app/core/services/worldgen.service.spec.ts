import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { WorldgenService, WORLDGEN_STEPS } from './worldgen.service';
import { StorageService } from './storage.service';
import { environment } from '@env/environment';
import { WorldgenSession, WorldgenSessionMode } from '../models/api.models';

describe('WorldgenService', () => {
  let service: WorldgenService;
  let httpMock: HttpTestingController;

  const mockSession: WorldgenSession = {
    id: 'session-123',
    status: 'draft',
    mode: 'ai_collab',
    draft_data_json: {
      basics: { name: 'Test Universe', description: 'A test universe' },
      tone: { darkness: 50, humor: 50, realism: 50, magic_level: 50 },
      rules: { permadeath: false, critical_fumbles: false, encumbrance: false }
    },
    step_status_json: {
      basics: { complete: true, fields: { name: true, description: true } },
      tone: { complete: true, fields: {} },
      rules: { complete: true, fields: {} },
      calendar: { complete: false, fields: {} },
      lore: { complete: false, fields: {} },
      homebrew: { complete: false, fields: {} }
    },
    conversation_json: [],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        WorldgenService,
        StorageService
      ]
    });
    service = TestBed.inject(WorldgenService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('WORLDGEN_STEPS constant', () => {
    it('should have all required steps', () => {
      const stepNames = WORLDGEN_STEPS.map(s => s.name);
      expect(stepNames).toContain('basics');
      expect(stepNames).toContain('tone');
      expect(stepNames).toContain('rules');
      expect(stepNames).toContain('calendar');
      expect(stepNames).toContain('lore');
      expect(stepNames).toContain('homebrew');
    });

    it('should mark basics, tone, and rules as required', () => {
      const requiredSteps = WORLDGEN_STEPS.filter(s => s.required);
      expect(requiredSteps.map(s => s.name)).toEqual(['basics', 'tone', 'rules']);
    });
  });

  describe('checkLlmStatus', () => {
    it('should return LLM configuration status', () => {
      service.checkLlmStatus().subscribe(status => {
        expect(status.configured).toBe(true);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/universes/worldgen/llm-status/`);
      expect(req.request.method).toBe('GET');
      req.flush({ configured: true });
    });
  });

  describe('listSessions', () => {
    it('should return list of sessions', () => {
      const mockSessions = [
        { id: 'session-1', name: 'Session 1', status: 'draft', mode: 'ai_collab', updated_at: '2024-01-01' },
        { id: 'session-2', name: 'Session 2', status: 'draft', mode: 'manual', updated_at: '2024-01-02' }
      ];

      service.listSessions().subscribe(sessions => {
        expect(sessions.length).toBe(2);
        expect(sessions[0].id).toBe('session-1');
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/universes/worldgen/sessions/`);
      expect(req.request.method).toBe('GET');
      req.flush(mockSessions);
    });
  });

  describe('createSession', () => {
    it('should create a new session and update current session', () => {
      service.createSession('ai_collab').subscribe(session => {
        expect(session.id).toBe('session-123');
        expect(service.currentSession()).toEqual(mockSession);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/universes/worldgen/sessions/`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ mode: 'ai_collab' });
      req.flush(mockSession);
    });

    it('should create manual mode session', () => {
      service.createSession('manual').subscribe(session => {
        expect(session.mode).toBe('ai_collab'); // Mock returns ai_collab
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/universes/worldgen/sessions/`);
      expect(req.request.body).toEqual({ mode: 'manual' });
      req.flush(mockSession);
    });
  });

  describe('getSession', () => {
    it('should get session by ID and update current session', () => {
      service.getSession('session-123').subscribe(session => {
        expect(session.id).toBe('session-123');
        expect(service.currentSession()).toEqual(mockSession);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/universes/worldgen/sessions/session-123/`);
      expect(req.request.method).toBe('GET');
      req.flush(mockSession);
    });
  });

  describe('abandonSession', () => {
    it('should abandon session and clear current session if matching', () => {
      // First set current session
      service.getSession('session-123').subscribe();
      httpMock.expectOne(`${environment.apiUrl}/universes/worldgen/sessions/session-123/`).flush(mockSession);

      expect(service.currentSession()).toEqual(mockSession);

      // Now abandon
      service.abandonSession('session-123').subscribe();
      const req = httpMock.expectOne(`${environment.apiUrl}/universes/worldgen/sessions/session-123/`);
      expect(req.request.method).toBe('DELETE');
      req.flush(null);

      expect(service.currentSession()).toBeNull();
    });
  });

  describe('updateStepData', () => {
    it('should update step data and refresh current session', () => {
      const updatedSession = {
        ...mockSession,
        draft_data_json: {
          ...mockSession.draft_data_json,
          basics: { name: 'Updated Universe', description: 'Updated description' }
        }
      };

      service.updateStepData('session-123', 'basics', { name: 'Updated Universe' }).subscribe(session => {
        expect(session.draft_data_json.basics?.name).toBe('Updated Universe');
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/universes/worldgen/sessions/session-123/update/`);
      expect(req.request.method).toBe('PATCH');
      expect(req.request.body).toEqual({ step: 'basics', data: { name: 'Updated Universe' } });
      req.flush(updatedSession);
    });
  });

  describe('switchMode', () => {
    it('should switch session mode', () => {
      const manualSession = { ...mockSession, mode: 'manual' as WorldgenSessionMode };

      service.switchMode('session-123', 'manual').subscribe(session => {
        expect(session.mode).toBe('manual');
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/universes/worldgen/sessions/session-123/mode/`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ mode: 'manual' });
      req.flush(manualSession);
    });
  });

  describe('finalizeSession', () => {
    it('should finalize session and clear current session', () => {
      // First set current session
      service.getSession('session-123').subscribe();
      httpMock.expectOne(`${environment.apiUrl}/universes/worldgen/sessions/session-123/`).flush(mockSession);

      const mockUniverse = {
        id: 'universe-1',
        name: 'Test Universe',
        description: 'A test universe',
        created_at: '2024-01-01',
        updated_at: '2024-01-01'
      };

      service.finalizeSession('session-123').subscribe(universe => {
        expect(universe.name).toBe('Test Universe');
        expect(service.currentSession()).toBeNull();
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/universes/worldgen/sessions/session-123/finalize/`);
      expect(req.request.method).toBe('POST');
      req.flush(mockUniverse);
    });
  });

  describe('computed signals', () => {
    it('should compute stepStatus from current session', () => {
      expect(service.stepStatus()).toBeNull();

      service.getSession('session-123').subscribe();
      httpMock.expectOne(`${environment.apiUrl}/universes/worldgen/sessions/session-123/`).flush(mockSession);

      expect(service.stepStatus()).toEqual(mockSession.step_status_json);
    });

    it('should compute draftData from current session', () => {
      expect(service.draftData()).toBeNull();

      service.getSession('session-123').subscribe();
      httpMock.expectOne(`${environment.apiUrl}/universes/worldgen/sessions/session-123/`).flush(mockSession);

      expect(service.draftData()).toEqual(mockSession.draft_data_json);
    });

    it('should compute currentStep based on incomplete steps', () => {
      // Without session, default to basics
      expect(service.currentStep()).toBe('basics');

      // With session, find first incomplete step
      service.getSession('session-123').subscribe();
      httpMock.expectOne(`${environment.apiUrl}/universes/worldgen/sessions/session-123/`).flush(mockSession);

      // basics, tone, rules are complete, so next is calendar
      expect(service.currentStep()).toBe('calendar');
    });

    it('should compute canFinalize when required steps are complete', () => {
      expect(service.canFinalize()).toBe(false);

      service.getSession('session-123').subscribe();
      httpMock.expectOne(`${environment.apiUrl}/universes/worldgen/sessions/session-123/`).flush(mockSession);

      // basics, tone, rules are complete
      expect(service.canFinalize()).toBe(true);
    });

    it('should return false for canFinalize when required steps are incomplete', () => {
      const incompleteSession = {
        ...mockSession,
        step_status_json: {
          ...mockSession.step_status_json,
          basics: { complete: false, fields: {} }
        }
      };

      service.getSession('session-123').subscribe();
      httpMock.expectOne(`${environment.apiUrl}/universes/worldgen/sessions/session-123/`).flush(incompleteSession);

      expect(service.canFinalize()).toBe(false);
    });
  });

  describe('clearSession', () => {
    it('should clear all session state', () => {
      // First set current session
      service.getSession('session-123').subscribe();
      httpMock.expectOne(`${environment.apiUrl}/universes/worldgen/sessions/session-123/`).flush(mockSession);

      expect(service.currentSession()).toBeTruthy();

      service.clearSession();

      expect(service.currentSession()).toBeNull();
      expect(service.streamContent()).toBe('');
      expect(service.isStreaming()).toBe(false);
    });
  });
});
