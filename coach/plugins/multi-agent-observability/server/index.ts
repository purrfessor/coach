/**
 * Multi-Agent Observability Server
 *
 * HTTP/WebSocket server for collecting and broadcasting hook events
 * from Claude Code agents across all projects.
 */

import { join, extname } from 'path';
import type { ServerWebSocket } from 'bun';
import type { HookEvent, WebSocketMessage } from './types';
import { insertEvent, getRecentEvents, getFilterOptions, clearEvents, getEventCount } from './db';

const PORT = Number(process.env.OBSERVABILITY_PORT) || 4000;

// Dashboard static files directory (built React app)
const DASHBOARD_DIR = join(import.meta.dir, '..', 'dashboard', 'dist');

// MIME types for static files
const MIME_TYPES: Record<string, string> = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
};

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
 * Serve static files from the dashboard build directory.
 * Falls back to index.html for SPA client-side routing.
 */
async function serveStaticFile(pathname: string): Promise<Response> {
  // Normalize path - remove leading slash and default to index.html
  let filePath = pathname === '/' ? 'index.html' : pathname.slice(1);

  // Security: prevent directory traversal
  if (filePath.includes('..')) {
    return jsonResponse({ error: 'Forbidden' }, 403);
  }

  const fullPath = join(DASHBOARD_DIR, filePath);

  // Try to serve the requested file
  const file = Bun.file(fullPath);
  if (await file.exists()) {
    const ext = extname(filePath);
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';
    return new Response(file, {
      headers: {
        'Content-Type': contentType,
        ...corsHeaders()
      }
    });
  }

  // For SPA: if file not found and not an API route, serve index.html
  const indexPath = join(DASHBOARD_DIR, 'index.html');
  const indexFile = Bun.file(indexPath);
  if (await indexFile.exists()) {
    return new Response(indexFile, {
      headers: {
        'Content-Type': 'text/html',
        ...corsHeaders()
      }
    });
  }

  // No dashboard built yet
  return new Response(
    `<!DOCTYPE html>
<html>
<head><title>Observability Dashboard</title></head>
<body style="font-family: system-ui; background: #09090b; color: #e4e4e7; padding: 40px; text-align: center;">
  <h1>Dashboard Not Built</h1>
  <p>Run <code style="background: #27272a; padding: 4px 8px; border-radius: 4px;">cd dashboard && npm install && npm run build</code> to build the dashboard.</p>
  <p style="margin-top: 20px; color: #71717a;">API endpoints are available at /health, /events, etc.</p>
</body>
</html>`,
    {
      status: 200,
      headers: {
        'Content-Type': 'text/html',
        ...corsHeaders()
      }
    }
  );
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

    // Serve static files from dashboard (fallback to index.html for SPA routing)
    return serveStaticFile(url.pathname);
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
console.log(`   Dashboard: http://localhost:${PORT}`);
console.log(`   WebSocket: ws://localhost:${PORT}/stream`);
console.log(`   Database: ~/.claude-observability/events.db`);
