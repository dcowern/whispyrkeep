/**
 * Common API response types
 */

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiError {
  detail?: string;
  message?: string;
  errors?: Record<string, string[]>;
}

/**
 * User & Auth models
 */
export interface User {
  id: string;
  email: string;
  username: string;
  created_at: string;
  updated_at: string;
}

export interface UserSettings {
  id: string;
  user: string;
  low_stim_mode: boolean;
  concise_recap: boolean;
  font_size: 'small' | 'medium' | 'large';
  content_rating: 'G' | 'PG' | 'PG13' | 'R';
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  password_confirm: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface TokenRefreshRequest {
  refresh: string;
}

export interface TokenRefreshResponse {
  access: string;
}

/**
 * LLM Config models
 */
export interface LlmEndpointConfig {
  id: string;
  name: string;
  provider: 'openai' | 'anthropic' | 'custom';
  base_url: string;
  model_name: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface LlmEndpointConfigCreate {
  name: string;
  provider: 'openai' | 'anthropic' | 'custom';
  base_url: string;
  model_name: string;
  api_key: string;
  is_default?: boolean;
}

/**
 * Character models
 */
export interface CharacterSheet {
  id: string;
  user: string;
  name: string;
  race: string;
  class_name: string;
  level: number;
  background: string;
  alignment: string;
  abilities: AbilityScores;
  skills: Record<string, boolean>;
  hit_points: HitPoints;
  armor_class: number;
  speed: number;
  proficiency_bonus: number;
  equipment: string[];
  features: string[];
  spells?: SpellSlots;
  backstory: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface AbilityScores {
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
}

export interface HitPoints {
  current: number;
  maximum: number;
  temporary: number;
}

export interface SpellSlots {
  level_1?: number;
  level_2?: number;
  level_3?: number;
  level_4?: number;
  level_5?: number;
  level_6?: number;
  level_7?: number;
  level_8?: number;
  level_9?: number;
}

/**
 * Universe models
 */
export interface Universe {
  id: string;
  user: string;
  name: string;
  description: string;
  tone: UniverseTone;
  rules: UniverseRules;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface UniverseTone {
  darkness: number; // 0-100
  humor: number; // 0-100
  realism: number; // 0-100
  magic_level: number; // 0-100
}

export interface UniverseRules {
  permadeath: boolean;
  critical_fumbles: boolean;
  encumbrance: boolean;
  optional_rules: string[];
}

export interface UniverseCreate {
  name: string;
  description: string;
  tone?: Partial<UniverseTone>;
  rules?: Partial<UniverseRules>;
  is_public?: boolean;
}

/**
 * Campaign models
 */
export interface Campaign {
  id: string;
  user: string;
  universe: string;
  character: string;
  name: string;
  description: string;
  status: 'active' | 'paused' | 'completed' | 'abandoned';
  turn_count: number;
  current_state_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface CampaignCreate {
  universe: string;
  character: string;
  name: string;
  description?: string;
  difficulty?: 'easy' | 'normal' | 'hard';
  content_rating?: 'G' | 'PG' | 'PG13' | 'R';
}

export interface TurnEvent {
  id: string;
  campaign: string;
  sequence_number: number;
  player_input: string;
  dm_narrative: string;
  dm_json: TurnDmJson;
  state_before: string;
  state_after: string;
  created_at: string;
}

export interface TurnDmJson {
  roll_requests?: RollRequest[];
  patches?: StatePatch[];
  lore_deltas?: LoreDelta[];
}

export interface RollRequest {
  type: 'ability_check' | 'saving_throw' | 'attack' | 'damage';
  ability?: string;
  skill?: string;
  dc?: number;
  advantage?: boolean;
  disadvantage?: boolean;
}

export interface StatePatch {
  op: 'add' | 'remove' | 'replace';
  path: string;
  value?: unknown;
}

export interface LoreDelta {
  category: 'hard_canon' | 'soft_lore';
  content: string;
  tags?: string[];
}

/**
 * Lore models
 */
export interface LoreDocument {
  id: string;
  universe: string;
  title: string;
  content: string;
  category: 'hard_canon' | 'soft_lore';
  source: 'user_upload' | 'dm_generated';
  embedding_status: 'pending' | 'processing' | 'complete' | 'failed';
  created_at: string;
  updated_at: string;
}

export interface LoreSearchResult {
  id: string;
  title: string;
  content: string;
  category: string;
  relevance_score: number;
}

export interface LoreEntry {
  id: string;
  title?: string;
  content: string;
  is_canon: boolean;
  source?: string;
  tags?: string[];
  created_at: string;
}

/**
 * Export models
 */
export interface ExportJob {
  id: string;
  user: string;
  export_type: 'universe' | 'campaign' | 'character';
  target_id: string;
  format: 'json' | 'markdown' | 'pdf';
  status: 'pending' | 'processing' | 'complete' | 'failed';
  file_url: string | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface ExportJobCreate {
  export_type: 'universe' | 'campaign' | 'character';
  target_id: string;
  format: 'json' | 'markdown' | 'pdf';
}

/**
 * SRD Catalog models
 */
export interface SrdRace {
  id: string;
  name: string;
  description: string;
  ability_bonuses: Record<string, number>;
  traits: string[];
  speed: number;
  size: string;
}

export interface SrdClass {
  id: string;
  name: string;
  description: string;
  hit_die: number;
  primary_ability: string;
  saving_throw_proficiencies: string[];
  features: SrdFeature[];
}

export interface SrdFeature {
  name: string;
  level: number;
  description: string;
}

export interface SrdBackground {
  id: string;
  name: string;
  description: string;
  skill_proficiencies: string[];
  tool_proficiencies: string[];
  feature: string;
}

export interface SrdSpell {
  id: string;
  name: string;
  level: number;
  school: string;
  casting_time: string;
  range: string;
  components: string;
  duration: string;
  description: string;
  classes: string[];
}
