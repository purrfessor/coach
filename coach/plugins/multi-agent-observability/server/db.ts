/**
 * SQLite database for event persistence.
 */

import { Database } from 'bun:sqlite';
import type { HookEvent, FilterOptions } from './types';
import { homedir } from 'os';
import { mkdirSync, existsSync } from 'fs';
import { join } from 'path';

// Store data in a central location
const DATA_DIR = join(homedir(), '.claude-observability');
const DB_PATH = join(DATA_DIR, 'events.db');

// Ensure data directory exists
if (!existsSync(DATA_DIR)) {
  mkdirSync(DATA_DIR, { recursive: true });
}

// Initialize database with WAL mode for better concurrency
const db = new Database(DB_PATH);
db.exec('PRAGMA journal_mode = WAL');
db.exec('PRAGMA synchronous = NORMAL');

// Create events table
db.exec(`
  CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_app TEXT NOT NULL,
    session_id TEXT NOT NULL,
    hook_event_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    chat TEXT,
    summary TEXT,
    model_name TEXT,
    timestamp INTEGER NOT NULL
  )
`);

// Create indexes for common queries
db.exec('CREATE INDEX IF NOT EXISTS idx_source_app ON events(source_app)');
db.exec('CREATE INDEX IF NOT EXISTS idx_session_id ON events(session_id)');
db.exec('CREATE INDEX IF NOT EXISTS idx_hook_event_type ON events(hook_event_type)');
db.exec('CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)');

/**
 * Insert a new event into the database.
 */
export function insertEvent(event: Omit<HookEvent, 'id'>): HookEvent {
  const stmt = db.prepare(`
    INSERT INTO events (source_app, session_id, hook_event_type, payload, chat, summary, model_name, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `);

  const result = stmt.run(
    event.source_app,
    event.session_id,
    event.hook_event_type,
    JSON.stringify(event.payload),
    event.chat ? JSON.stringify(event.chat) : null,
    event.summary || null,
    event.model_name || null,
    event.timestamp
  );

  return {
    ...event,
    id: Number(result.lastInsertRowid)
  };
}

/**
 * Get recent events with pagination.
 */
export function getRecentEvents(limit: number = 300): HookEvent[] {
  const stmt = db.prepare(`
    SELECT * FROM events
    ORDER BY timestamp DESC
    LIMIT ?
  `);

  const rows = stmt.all(limit) as any[];

  return rows.map(row => ({
    id: row.id,
    source_app: row.source_app,
    session_id: row.session_id,
    hook_event_type: row.hook_event_type,
    payload: JSON.parse(row.payload),
    chat: row.chat ? JSON.parse(row.chat) : undefined,
    summary: row.summary || undefined,
    model_name: row.model_name || undefined,
    timestamp: row.timestamp
  })).reverse(); // Return in chronological order
}

/**
 * Get filter options for the UI.
 */
export function getFilterOptions(): FilterOptions {
  const sourceApps = db.prepare('SELECT DISTINCT source_app FROM events ORDER BY source_app').all() as { source_app: string }[];
  const sessionIds = db.prepare('SELECT DISTINCT session_id FROM events ORDER BY session_id').all() as { session_id: string }[];
  const eventTypes = db.prepare('SELECT DISTINCT hook_event_type FROM events ORDER BY hook_event_type').all() as { hook_event_type: string }[];

  return {
    source_apps: sourceApps.map(r => r.source_app),
    session_ids: sessionIds.map(r => r.session_id),
    hook_event_types: eventTypes.map(r => r.hook_event_type)
  };
}

/**
 * Clear all events from the database.
 */
export function clearEvents(): void {
  db.exec('DELETE FROM events');
}

/**
 * Get event count.
 */
export function getEventCount(): number {
  const result = db.prepare('SELECT COUNT(*) as count FROM events').get() as { count: number };
  return result.count;
}

export { db };
