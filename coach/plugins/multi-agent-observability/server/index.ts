/**
 * Multi-Agent Observability Server
 *
 * HTTP/WebSocket server for collecting and broadcasting hook events
 * from Claude Code agents across all projects.
 */

import type { ServerWebSocket } from 'bun';
import type { HookEvent, WebSocketMessage } from './types';
import { insertEvent, getRecentEvents, getFilterOptions, clearEvents, getEventCount } from './db';

const PORT = Number(process.env.OBSERVABILITY_PORT) || 4000;

// Track connected WebSocket clients
const clients = new Set<ServerWebSocket<unknown>>();

/**
 * Broadcast an event to all connected WebSocket clients.
 */
function broadcast(message: WebSocketMessage): void {
  const json = JSON.stringify(message);
  for (const client of clients) {
    try {
      client.send(json);
    } catch {
      clients.delete(client);
    }
  }
}

/**
 * Handle CORS for cross-origin requests.
 */
function corsHeaders(): Record<string, string> {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Accept',
  };
}

/**
 * Create a JSON response with CORS headers.
 */
function jsonResponse(data: unknown, status: number = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      ...corsHeaders()
    }
  });
}

/**
 * Main server
 */
const server = Bun.serve({
  port: PORT,

  fetch(req, server) {
    const url = new URL(req.url);
    const method = req.method;

    // Handle CORS preflight
    if (method === 'OPTIONS') {
      return new Response(null, {
        status: 204,
        headers: corsHeaders()
      });
    }

    // WebSocket upgrade for /stream
    if (url.pathname === '/stream') {
      const upgraded = server.upgrade(req);
      if (upgraded) {
        return undefined;
      }
      return new Response('WebSocket upgrade failed', { status: 400 });
    }

    // Health check endpoint
    if (url.pathname === '/health' && method === 'GET') {
      return jsonResponse({ status: 'ok', timestamp: Date.now() });
    }

    // POST /events - Receive hook events
    if (url.pathname === '/events' && method === 'POST') {
      return handlePostEvent(req);
    }

    // GET /events/recent - Get recent events
    if (url.pathname === '/events/recent' && method === 'GET') {
      const limit = Number(url.searchParams.get('limit')) || 300;
      const events = getRecentEvents(limit);
      return jsonResponse(events);
    }

    // GET /events/filter-options - Get filter options for UI
    if (url.pathname === '/events/filter-options' && method === 'GET') {
      const options = getFilterOptions();
      return jsonResponse(options);
    }

    // GET /events/count - Get event count
    if (url.pathname === '/events/count' && method === 'GET') {
      return jsonResponse({ count: getEventCount() });
    }

    // DELETE /events - Clear all events
    if (url.pathname === '/events' && method === 'DELETE') {
      clearEvents();
      return jsonResponse({ message: 'All events cleared' });
    }

    // 404 for unknown routes
    return jsonResponse({ error: 'Not found' }, 404);
  },

  websocket: {
    open(ws) {
      clients.add(ws);
      // Send recent events on connect
      const events = getRecentEvents(300);
      ws.send(JSON.stringify({
        type: 'initial',
        data: events
      } as WebSocketMessage));
    },

    close(ws) {
      clients.delete(ws);
    },

    message(ws, message) {
      // Currently no client-to-server messages expected
    }
  }
});

/**
 * Handle POST /events - receive and store a hook event.
 */
async function handlePostEvent(req: Request): Promise<Response> {
  try {
    const body = await req.json();

    // Validate required fields
    const { source_app, session_id, hook_event_type, payload } = body;

    if (!source_app || typeof source_app !== 'string') {
      return jsonResponse({ error: 'Missing or invalid source_app' }, 400);
    }
    if (!session_id || typeof session_id !== 'string') {
      return jsonResponse({ error: 'Missing or invalid session_id' }, 400);
    }
    if (!hook_event_type || typeof hook_event_type !== 'string') {
      return jsonResponse({ error: 'Missing or invalid hook_event_type' }, 400);
    }
    if (payload === undefined) {
      return jsonResponse({ error: 'Missing payload' }, 400);
    }

    // Build event object
    const event: Omit<HookEvent, 'id'> = {
      source_app,
      session_id,
      hook_event_type,
      payload: typeof payload === 'object' ? payload : { value: payload },
      timestamp: Date.now()
    };

    // Optional fields
    if (body.chat) {
      event.chat = body.chat;
    }
    if (body.summary) {
      event.summary = body.summary;
    }
    if (body.model_name) {
      event.model_name = body.model_name;
    }

    // Store event
    const savedEvent = insertEvent(event);

    // Broadcast to WebSocket clients
    broadcast({
      type: 'event',
      data: savedEvent
    });

    return jsonResponse(savedEvent, 201);

  } catch (error) {
    console.error('Error handling POST /events:', error);
    return jsonResponse({ error: 'Invalid request body' }, 400);
  }
}

console.log(`🔭 Observability server running on http://localhost:${PORT}`);
console.log(`   WebSocket endpoint: ws://localhost:${PORT}/stream`);
console.log(`   Data stored at: ~/.claude-observability/events.db`);
