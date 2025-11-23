import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { CharacterService } from './character.service';
import { environment } from '@env/environment';
import { CharacterSheet } from '../models/api.models';

describe('CharacterService', () => {
  let service: CharacterService;
  let httpMock: HttpTestingController;

  const mockCharacter: CharacterSheet = {
    id: '1',
    user: 'user-1',
    name: 'Test Character',
    race: 'Human',
    class_name: 'Fighter',
    level: 1,
    background: 'Soldier',
    alignment: 'Neutral Good',
    abilities: {
      strength: 16,
      dexterity: 14,
      constitution: 14,
      intelligence: 10,
      wisdom: 12,
      charisma: 8
    },
    skills: { athletics: true, intimidation: true },
    hit_points: { current: 12, maximum: 12, temporary: 0 },
    armor_class: 16,
    speed: 30,
    proficiency_bonus: 2,
    equipment: ['Longsword', 'Shield'],
    features: ['Fighting Style', 'Second Wind'],
    backstory: 'A veteran soldier',
    notes: '',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        CharacterService
      ]
    });
    service = TestBed.inject(CharacterService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('list', () => {
    it('should return paginated characters', () => {
      const response = {
        count: 1,
        next: null,
        previous: null,
        results: [mockCharacter]
      };

      service.list().subscribe(data => {
        expect(data.count).toBe(1);
        expect(data.results[0].name).toBe('Test Character');
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/characters/`);
      expect(req.request.method).toBe('GET');
      req.flush(response);
    });
  });

  describe('get', () => {
    it('should return a character by id', () => {
      service.get('1').subscribe(data => {
        expect(data.name).toBe('Test Character');
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/characters/1/`);
      expect(req.request.method).toBe('GET');
      req.flush(mockCharacter);
    });
  });

  describe('create', () => {
    it('should create a new character', () => {
      const newCharacter = { name: 'New Character', race: 'Elf', class_name: 'Wizard' };

      service.create(newCharacter).subscribe(data => {
        expect(data.id).toBe('1');
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/characters/`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(newCharacter);
      req.flush(mockCharacter);
    });
  });

  describe('update', () => {
    it('should update a character', () => {
      const updates = { name: 'Updated Name' };

      service.update('1', updates).subscribe(data => {
        expect(data).toBeTruthy();
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/characters/1/`);
      expect(req.request.method).toBe('PATCH');
      req.flush({ ...mockCharacter, name: 'Updated Name' });
    });
  });

  describe('delete', () => {
    it('should delete a character', () => {
      service.delete('1').subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/characters/1/`);
      expect(req.request.method).toBe('DELETE');
      req.flush(null);
    });
  });

  describe('levelUp', () => {
    it('should level up a character', () => {
      service.levelUp('1').subscribe(data => {
        expect(data.level).toBe(2);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/characters/1/level-up/`);
      expect(req.request.method).toBe('POST');
      req.flush({ ...mockCharacter, level: 2 });
    });
  });

  describe('validate', () => {
    it('should validate a character', () => {
      const characterData = { name: 'Test', race: 'Human' };
      const validationResult = { valid: true, errors: [] };

      service.validate(characterData).subscribe(data => {
        expect(data.valid).toBe(true);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/characters/validate/`);
      expect(req.request.method).toBe('POST');
      req.flush(validationResult);
    });
  });
});
