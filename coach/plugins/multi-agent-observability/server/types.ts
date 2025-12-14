/**
 * Type definitions for the observability server.
 */

export interface HookEvent {
  id?: number;
  source_app: string;
  session_id: string;
  hook_event_type: string;
  payload: Record<string, unknown>;
  chat?: ChatMessage[];
  summary?: string;
  model_name?: string;
  timestamp: number;
}

export interface ChatMessage {
  role: string;
  content: string;
  timestamp?: number;
}

export interface WebSocketMessage {
  type: 'initial' | 'event';
  data: HookEvent[] | HookEvent;
}

export interface FilterOptions {
  source_apps: string[];
  session_ids: string[];
  hook_event_types: string[];
}
