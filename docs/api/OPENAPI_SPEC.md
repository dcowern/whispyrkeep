# WhispyrKeep API Specification

This document describes the REST API endpoints for WhispyrKeep.

## Base URL

```
/api/v1/
```

## Authentication

All endpoints (except auth) require JWT authentication.

```
Authorization: Bearer <access_token>
```

## Endpoints

### Authentication

#### POST /auth/register/
Create a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "username": "adventurer",
  "password": "securepassword123",
  "password_confirm": "securepassword123"
}
```

**Response (201):**
```json
{
  "access": "<jwt_access_token>",
  "refresh": "<jwt_refresh_token>",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "adventurer"
  }
}
```

#### POST /auth/login/
Authenticate and get tokens.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200):**
```json
{
  "access": "<jwt_access_token>",
  "refresh": "<jwt_refresh_token>",
  "user": { ... }
}
```

#### POST /auth/token/refresh/
Refresh access token.

**Request:**
```json
{
  "refresh": "<jwt_refresh_token>"
}
```

**Response (200):**
```json
{
  "access": "<new_jwt_access_token>"
}
```

#### GET /auth/me/
Get current user info.

**Response (200):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "adventurer",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### User Settings

#### GET /auth/settings/
Get user settings.

**Response (200):**
```json
{
  "low_stim_mode": false,
  "concise_recap": false,
  "font_size": "medium",
  "content_rating": "PG13"
}
```

#### PATCH /auth/settings/
Update user settings.

**Request:**
```json
{
  "low_stim_mode": true
}
```

### Characters

#### GET /characters/
List user's characters.

**Response (200):**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "name": "Aria Brightwood",
      "race": "Human",
      "class_name": "Fighter",
      "level": 5,
      ...
    }
  ]
}
```

#### POST /characters/
Create a new character.

**Request:**
```json
{
  "name": "Aria Brightwood",
  "race": "Human",
  "class_name": "Fighter",
  "background": "Soldier",
  "abilities": {
    "strength": 16,
    "dexterity": 14,
    "constitution": 15,
    "intelligence": 10,
    "wisdom": 12,
    "charisma": 8
  }
}
```

#### GET /characters/{id}/
Get character details.

#### PATCH /characters/{id}/
Update character.

#### DELETE /characters/{id}/
Delete character.

#### POST /characters/{id}/level-up/
Level up a character.

### Universes

#### GET /universes/
List universes.

#### POST /universes/
Create universe.

**Request:**
```json
{
  "name": "The Forgotten Realms",
  "description": "A high fantasy world",
  "is_public": false,
  "tone": {
    "darkness": 40,
    "humor": 30,
    "realism": 50,
    "magic_level": 80
  },
  "rules": {
    "permadeath": false,
    "critical_fumbles": true,
    "encumbrance": false
  }
}
```

#### GET /universes/{id}/
Get universe details.

#### PATCH /universes/{id}/
Update universe.

#### DELETE /universes/{id}/
Delete universe.

#### POST /universes/{id}/upload-lore/
Upload lore documents.

**Request (multipart/form-data):**
- `file`: The document file (.txt, .md, .pdf)
- `category`: "hard_canon" | "soft_lore"

### Campaigns

#### GET /campaigns/
List campaigns.

#### POST /campaigns/
Create campaign.

**Request:**
```json
{
  "universe": "uuid",
  "character": "uuid",
  "name": "The Lost Mine",
  "description": "A tale of adventure",
  "difficulty": "normal",
  "content_rating": "PG13"
}
```

#### GET /campaigns/{id}/
Get campaign details.

#### PATCH /campaigns/{id}/
Update campaign.

#### DELETE /campaigns/{id}/
Delete campaign.

### Turns

#### GET /campaigns/{id}/turns/
List turns for a campaign.

**Response (200):**
```json
{
  "count": 15,
  "results": [
    {
      "id": "uuid",
      "sequence_number": 1,
      "player_input": "I enter the tavern",
      "dm_narrative": "The tavern is dimly lit...",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### POST /campaigns/{id}/turns/
Submit a turn.

**Request:**
```json
{
  "player_input": "I speak with the bartender about the rumors."
}
```

**Response (201):**
```json
{
  "turn": {
    "id": "uuid",
    "sequence_number": 16,
    "player_input": "I speak with the bartender about the rumors.",
    "dm_narrative": "The bartender leans in...",
    "dm_json": { ... }
  },
  "narrative": "The bartender leans in..."
}
```

#### GET /campaigns/{id}/turns/{turnId}/
Get specific turn.

### Rewind

#### POST /campaigns/{id}/rewind/
Rewind campaign to a previous turn.

**Request:**
```json
{
  "to_turn_sequence": 10
}
```

**Response (200):**
```json
{
  "campaign": { ... },
  "turns_removed": 5
}
```

### Campaign State

#### GET /campaigns/{id}/state/
Get current campaign state.

**Response (200):**
```json
{
  "character": { ... },
  "location": { ... },
  "time": { ... },
  "inventory": [ ... ],
  "quests": [ ... ]
}
```

### Lore

#### GET /campaigns/{id}/lore/
Get lore entries for a campaign.

**Response (200):**
```json
[
  {
    "id": "uuid",
    "title": "History of Thornwood",
    "content": "The village was founded...",
    "is_canon": true,
    "source": "user_upload",
    "tags": ["history", "thornwood"]
  }
]
```

### SRD Catalog

#### GET /catalog/races/
List SRD races.

#### GET /catalog/classes/
List SRD classes.

#### GET /catalog/backgrounds/
List SRD backgrounds.

#### GET /catalog/spells/
List SRD spells.

#### GET /catalog/equipment/
List SRD equipment.

### Exports

#### GET /exports/
List export jobs.

#### POST /exports/
Create export job.

**Request:**
```json
{
  "export_type": "campaign",
  "target_id": "uuid",
  "format": "json"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "export_type": "campaign",
  "target_id": "uuid",
  "format": "json",
  "status": "pending",
  "file_url": null
}
```

#### GET /exports/{id}/
Get export job status.

**Response (200):**
```json
{
  "id": "uuid",
  "status": "complete",
  "file_url": "/media/exports/campaign_abc123.json"
}
```

### LLM Configuration

#### GET /llm-config/
List LLM endpoint configurations.

#### POST /llm-config/
Create LLM config.

**Request:**
```json
{
  "name": "OpenAI GPT-4",
  "provider": "openai",
  "api_key": "sk-...",
  "model": "gpt-4-turbo",
  "base_url": "https://api.openai.com/v1"
}
```

#### PATCH /llm-config/{id}/
Update LLM config.

#### DELETE /llm-config/{id}/
Delete LLM config.

## Error Responses

### 400 Bad Request
```json
{
  "error": "validation_error",
  "details": {
    "field_name": ["Error message"]
  }
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 500 Internal Server Error
```json
{
  "error": "internal_error",
  "message": "An unexpected error occurred."
}
```

## Pagination

List endpoints support pagination:

```
GET /characters/?page=2&page_size=20
```

**Response:**
```json
{
  "count": 45,
  "next": "/api/v1/characters/?page=3",
  "previous": "/api/v1/characters/?page=1",
  "results": [ ... ]
}
```

## Filtering

Some endpoints support filtering:

```
GET /campaigns/?status=active
GET /characters/?level__gte=5
```

## Rate Limiting

- 100 requests per minute for authenticated users
- Turn submission: 10 per minute (to prevent LLM abuse)
