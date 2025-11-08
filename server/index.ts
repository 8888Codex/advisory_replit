import express, { type Request, Response, NextFunction } from "express";
import { createProxyMiddleware } from 'http-proxy-middleware';
import { spawn } from 'child_process';
import path from 'path';
import session from 'express-session';
import connectPgSimple from 'connect-pg-simple';
import { RateLimiterPostgres } from 'rate-limiter-flexible';
import pg from 'pg';
import { registerRoutes } from "./routes";
import { registerAdminRoutes } from "./routes/admin";
import { setupVite, serveStatic, log } from "./vite";
import { seedExperts } from "./seed";

const { Pool } = pg;

const app = express();

// Trust proxy for correct IP detection behind Replit/production proxies
app.set('trust proxy', 1);

// Session configuration with PostgreSQL store
const PgSession = connectPgSimple(session);

// Validate SESSION_SECRET in production
const sessionSecret = process.env.SESSION_SECRET;
if (process.env.NODE_ENV === 'production' && !sessionSecret) {
  throw new Error('SESSION_SECRET environment variable is required in production');
}

app.use(session({
  store: new PgSession({
    conString: process.env.DATABASE_URL,
    tableName: 'session',
    createTableIfMissing: true
  }),
  secret: sessionSecret || 'o-conselho-dev-secret-key',
  resave: false,
  saveUninitialized: false,
  cookie: {
    maxAge: 30 * 24 * 60 * 60 * 1000, // 30 days
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax'
  }
}));

// Extend session type
declare module 'express-session' {
  interface SessionData {
    userId?: string;
    user?: {
      id: string;
      username: string;
      email: string;
      role: string; // "user" | "admin" | "superadmin"
      availableInvites: number;
    };
  }
}

// Start Python backend automatically
function startPythonBackend() {
  log("Starting Python backend on port 5001...");
  const isDevelopment = process.env.NODE_ENV === 'development';
  const uvicornArgs = ['-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '5001'];
  if (isDevelopment) {
    uvicornArgs.push('--reload');
  }
  const pythonProcess = spawn('python3', uvicornArgs, {
    cwd: 'python_backend',
    stdio: ['ignore', 'pipe', 'pipe']
  });
  
  pythonProcess.stdout.on('data', (data) => {
    log(`[Python Backend] ${data.toString().trim()}`);
  });
  
  pythonProcess.stderr.on('data', (data) => {
    log(`[Python Backend Error] ${data.toString().trim()}`);
  });
  
  pythonProcess.on('error', (error) => {
    log(`[Python Backend] Failed to start: ${error.message}`);
  });
  
  pythonProcess.on('exit', (code) => {
    if (code !== null && code !== 0) {
      log(`[Python Backend] Exited with code ${code}`);
    }
  });
  
  return pythonProcess;
}

const pythonBackend = startPythonBackend();

// ============================================
// RATE LIMITING CONFIGURATION
// ============================================
// PostgreSQL pool for rate limiters
const rateLimitPool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

// PostgreSQL-backed rate limiters for authentication endpoints
// Note: Tables will be auto-created by the library
const loginRateLimiter = new RateLimiterPostgres({
  storeClient: rateLimitPool,
  tableName: 'rate_limit_login',
  points: 5, // 5 attempts
  duration: 15 * 60, // Per 15 minutes
  blockDuration: 15 * 60 // Block for 15 minutes after limit
});

const registerRateLimiter = new RateLimiterPostgres({
  storeClient: rateLimitPool,
  tableName: 'rate_limit_register',
  points: 3, // 3 registrations
  duration: 60 * 60, // Per 1 hour
  blockDuration: 60 * 60 // Block for 1 hour after limit
});

// Rate limiting middleware factory
const createRateLimiter = (limiter: any, action: string) => {
  return async (req: Request, res: Response, next: NextFunction) => {
    const key = req.ip || 'unknown';
    try {
      await limiter.consume(key);
      next();
    } catch (rateLimiterRes: any) {
      const remainingTime = Math.ceil(rateLimiterRes.msBeforeNext / 1000 / 60); // minutes
      res.status(429).json({
        detail: `Muitas tentativas. Aguarde ${remainingTime} minuto${remainingTime > 1 ? 's' : ''}.`,
        retryAfter: remainingTime
      });
    }
  };
};

const loginRateLimit = createRateLimiter(loginRateLimiter, 'login');
const registerRateLimit = createRateLimiter(registerRateLimiter, 'register');

// Parse JSON and URL-encoded bodies BEFORE auth routes
app.use(express.json());
app.use(express.urlencoded({ extended: false }));

// ============================================
// AUDIT LOGGING HELPER
// ============================================

async function logAuthEvent(
  action: string,
  success: boolean,
  req: Request,
  userId?: string,
  metadata?: Record<string, any>
) {
  try {
    await fetch('http://localhost:5001/api/audit/log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action,
        success,
        userId,
        ipAddress: req.ip,
        userAgent: req.headers['user-agent'],
        metadata
      })
    });
  } catch (error) {
    console.error('[Audit] Failed to log event:', error);
    // Don't throw - logging shouldn't break auth flow
  }
}

// ============================================
// AUTHENTICATION ROUTES
// ============================================
// These must be BEFORE the general proxy to intercept auth calls

app.post('/api/auth/register', registerRateLimit, async (req, res) => {
  try {
    const response = await fetch('http://localhost:5001/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body)
    });

    const data = await response.json();
    
    if (!response.ok) {
      // Log failed registration
      await logAuthEvent('register', false, req, undefined, { 
        email: req.body.email,
        error: data.detail 
      });
      return res.status(response.status).json(data);
    }

    // Create session on successful registration
    req.session.userId = data.id;
    req.session.user = {
      id: data.id,
      username: data.username,
      email: data.email,
      role: data.role || 'user', // Default to 'user' if not provided
      availableInvites: data.availableInvites
    };

    // Log successful registration
    await logAuthEvent('register', true, req, data.id, { 
      username: data.username,
      email: data.email 
    });

    res.status(201).json(data);
  } catch (error) {
    console.error('[Auth] Register error:', error);
    await logAuthEvent('register', false, req, undefined, { error: 'Internal error' });
    res.status(500).json({ detail: 'Erro ao registrar usuário' });
  }
});

app.post('/api/auth/login', loginRateLimit, async (req, res) => {
  try {
    const response = await fetch('http://localhost:5001/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body)
    });

    const data = await response.json();
    
    if (!response.ok) {
      // Log failed login
      await logAuthEvent('login', false, req, undefined, { 
        email: req.body.email,
        error: data.detail 
      });
      return res.status(response.status).json(data);
    }

    // Create session on successful login
    req.session.userId = data.id;
    req.session.user = {
      id: data.id,
      username: data.username,
      email: data.email,
      role: data.role || 'user', // Default to 'user' if not provided
      availableInvites: data.availableInvites
    };

    // Log successful login
    await logAuthEvent('login', true, req, data.id, { 
      username: data.username,
      email: data.email 
    });

    res.json(data);
  } catch (error) {
    console.error('[Auth] Login error:', error);
    await logAuthEvent('login', false, req, undefined, { error: 'Internal error' });
    res.status(500).json({ detail: 'Erro ao fazer login' });
  }
});

app.post('/api/auth/logout', async (req, res) => {
  const userId = req.session.userId;
  
  req.session.destroy(async (err) => {
    if (err) {
      console.error('[Auth] Logout error:', err);
      await logAuthEvent('logout', false, req, userId, { error: 'Session destroy failed' });
      return res.status(500).json({ detail: 'Erro ao fazer logout' });
    }
    
    res.clearCookie('connect.sid');
    await logAuthEvent('logout', true, req, userId);
    res.json({ message: 'Logout successful' });
  });
});

// Password reset endpoints - public (no session required)
app.post('/api/auth/request-reset', async (req, res) => {
  try {
    const response = await fetch('http://localhost:5001/api/auth/request-reset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body)
    });

    const data = await response.json();
    
    if (!response.ok) {
      await logAuthEvent('password_reset_request', false, req, undefined, { 
        email: req.body.email,
        error: data.detail 
      });
      return res.status(response.status).json(data);
    }

    await logAuthEvent('password_reset_request', true, req, undefined, { email: req.body.email });
    res.json(data);
  } catch (error) {
    console.error('[Auth] Request reset error:', error);
    await logAuthEvent('password_reset_request', false, req, undefined, { error: 'Internal error' });
    res.status(500).json({ detail: 'Erro ao solicitar redefinição de senha' });
  }
});

app.post('/api/auth/verify-reset-token', async (req, res) => {
  try {
    const response = await fetch('http://localhost:5001/api/auth/verify-reset-token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body)
    });

    const data = await response.json();
    
    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    res.json(data);
  } catch (error) {
    console.error('[Auth] Verify token error:', error);
    res.status(500).json({ detail: 'Erro ao verificar token' });
  }
});

app.post('/api/auth/reset-password', async (req, res) => {
  try {
    const response = await fetch('http://localhost:5001/api/auth/reset-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body)
    });

    const data = await response.json();
    
    if (!response.ok) {
      await logAuthEvent('password_reset_complete', false, req, undefined, { error: data.detail });
      return res.status(response.status).json(data);
    }

    await logAuthEvent('password_reset_complete', true, req, undefined);
    res.json(data);
  } catch (error) {
    console.error('[Auth] Reset password error:', error);
    await logAuthEvent('password_reset_complete', false, req, undefined, { error: 'Internal error' });
    res.status(500).json({ detail: 'Erro ao redefinir senha' });
  }
});

app.get('/api/auth/me', async (req, res) => {
  if (!req.session.userId) {
    return res.status(401).json({ detail: 'Não autenticado' });
  }

  try {
    // Fetch fresh user data from Python/database
    const response = await fetch(`http://localhost:5001/api/auth/me?user_id=${req.session.userId}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    if (!response.ok) {
      return res.status(response.status).json(await response.json());
    }

    const userData = await response.json();
    
    // Update session with fresh data
    req.session.user = userData;
    
    res.json(userData);
  } catch (error) {
    console.error('[Auth] Me error:', error);
    res.status(500).json({ detail: 'Erro ao buscar dados do usuário' });
  }
});

// ============================================
// INVITE CODE MANAGEMENT ROUTES (Protected)
// ============================================
// These must be authenticated and forward only session userId to Python

app.post('/api/invites/generate', async (req, res) => {
  if (!req.session.userId) {
    return res.status(401).json({ detail: 'Não autenticado' });
  }

  try {
    // Call Python with authenticated user ID only
    const response = await fetch(`http://localhost:5001/api/invites/generate?user_id=${req.session.userId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });

    const data = await response.json();
    
    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    res.status(201).json(data);
  } catch (error) {
    console.error('[Invites] Generate error:', error);
    res.status(500).json({ detail: 'Erro ao gerar código de convite' });
  }
});

app.get('/api/invites/my-codes', async (req, res) => {
  if (!req.session.userId) {
    return res.status(401).json({ detail: 'Não autenticado' });
  }

  try {
    // Call Python with authenticated user ID only
    const response = await fetch(`http://localhost:5001/api/invites/my-codes?user_id=${req.session.userId}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    const data = await response.json();
    
    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    res.json(data);
  } catch (error) {
    console.error('[Invites] List error:', error);
    res.status(500).json({ detail: 'Erro ao listar códigos de convite' });
  }
});

// ============================================
// AUDIT LOG ROUTES (Protected)
// ============================================

app.get('/api/audit/logs', async (req, res) => {
  if (!req.session.userId) {
    return res.status(401).json({ detail: 'Não autenticado' });
  }

  try {
    const { action, success, limit = '50', offset = '0' } = req.query;
    
    // Build query params
    const params = new URLSearchParams({
      user_id: req.session.userId,
      limit: limit as string,
      offset: offset as string
    });
    
    if (action) params.append('action', action as string);
    if (success !== undefined) params.append('success', success as string);
    
    const response = await fetch(`http://localhost:5001/api/audit/logs?${params.toString()}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    const data = await response.json();
    
    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    res.json(data);
  } catch (error) {
    console.error('[Audit] Get logs error:', error);
    res.status(500).json({ detail: 'Erro ao buscar logs de auditoria' });
  }
});

// ============================================
// ONBOARDING ROUTES (Protected)
// ============================================
// These must be authenticated and forward only session userId to Python

app.post('/api/onboarding/save', async (req, res) => {
  if (!req.session.userId) {
    return res.status(401).json({ detail: 'Não autenticado' });
  }

  try {
    // Call Python with authenticated user ID and onboarding data
    const response = await fetch(`http://localhost:5001/api/onboarding/save?user_id=${req.session.userId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body)
    });

    const data = await response.json();
    
    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    res.json(data);
  } catch (error) {
    console.error('[Onboarding] Save error:', error);
    res.status(500).json({ detail: 'Erro ao salvar progresso do onboarding' });
  }
});

app.get('/api/onboarding/status', async (req, res) => {
  if (!req.session.userId) {
    return res.status(401).json({ detail: 'Não autenticado' });
  }

  try {
    // Call Python with authenticated user ID only
    const response = await fetch(`http://localhost:5001/api/onboarding/status?user_id=${req.session.userId}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    const data = await response.json();
    
    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    res.json(data);
  } catch (error) {
    console.error('[Onboarding] Status error:', error);
    res.status(500).json({ detail: 'Erro ao buscar status do onboarding' });
  }
});

app.post('/api/onboarding/complete', async (req, res) => {
  if (!req.session.userId) {
    return res.status(401).json({ detail: 'Não autenticado' });
  }

  try {
    // Call Python with authenticated user ID only
    const response = await fetch(`http://localhost:5001/api/onboarding/complete?user_id=${req.session.userId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });

    const data = await response.json();
    
    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    res.json(data);
  } catch (error) {
    console.error('[Onboarding] Complete error:', error);
    res.status(500).json({ detail: 'Erro ao completar onboarding' });
  }
});

// ============================================
// PERSONA ROUTES (Protected)
// ============================================
// User persona creation and enrichment endpoints

app.post('/api/persona/create', async (req, res) => {
  if (!req.session.userId) {
    return res.status(401).json({ detail: 'Não autenticado' });
  }

  try {
    // Forward persona data to Python backend with authenticated user ID
    const response = await fetch(`http://localhost:5001/api/persona/create?user_id=${req.session.userId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body)
    });

    const data = await response.json();
    
    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    res.status(201).json(data);
  } catch (error) {
    console.error('[Persona] Create error:', error);
    res.status(500).json({ detail: 'Erro ao criar persona' });
  }
});

app.post('/api/persona/enrich/background', async (req, res) => {
  if (!req.session.userId) {
    return res.status(401).json({ detail: 'Não autenticado' });
  }

  try {
    // Trigger background enrichment
    const response = await fetch(`http://localhost:5001/api/persona/enrich/background?user_id=${req.session.userId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body)
    });

    const data = await response.json();
    
    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    res.status(202).json(data);
  } catch (error) {
    console.error('[Persona] Background enrich error:', error);
    res.status(500).json({ detail: 'Erro ao iniciar enriquecimento' });
  }
});

app.get('/api/persona/enrichment-status', async (req, res) => {
  if (!req.session.userId) {
    return res.status(401).json({ detail: 'Não autenticado' });
  }

  try {
    // Check enrichment status
    const response = await fetch(`http://localhost:5001/api/persona/enrichment-status?user_id=${req.session.userId}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    const data = await response.json();
    
    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    res.json(data);
  } catch (error) {
    console.error('[Persona] Enrichment status error:', error);
    res.status(500).json({ detail: 'Erro ao verificar status do enriquecimento' });
  }
});

app.get('/api/persona/current', async (req, res) => {
  if (!req.session.userId) {
    return res.status(401).json({ detail: 'Não autenticado' });
  }

  try {
    // Get current persona
    const response = await fetch(`http://localhost:5001/api/persona/current?user_id=${req.session.userId}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    const data = await response.json();
    
    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    res.json(data);
  } catch (error) {
    console.error('[Persona] Get current error:', error);
    res.status(500).json({ detail: 'Erro ao buscar persona atual' });
  }
});

app.get('/api/persona/list', async (req, res) => {
  if (!req.session.userId) {
    return res.status(401).json({ detail: 'Não autenticado' });
  }

  try {
    // Get all personas for this user
    const response = await fetch(`http://localhost:5001/api/persona/list?user_id=${req.session.userId}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    const data = await response.json();
    
    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    res.json(data);
  } catch (error) {
    console.error('[Persona] List error:', error);
    res.status(500).json({ detail: 'Erro ao listar personas' });
  }
});

app.post('/api/persona/set-active', async (req, res) => {
  if (!req.session.userId) {
    return res.status(401).json({ detail: 'Não autenticado' });
  }

  try {
    // Set active persona
    const response = await fetch(`http://localhost:5001/api/persona/set-active?user_id=${req.session.userId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body)
    });

    const data = await response.json();
    
    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    res.json(data);
  } catch (error) {
    console.error('[Persona] Set active error:', error);
    res.status(500).json({ detail: 'Erro ao definir persona ativa' });
  }
});

app.delete('/api/persona/:id', async (req, res) => {
  if (!req.session.userId) {
    return res.status(401).json({ detail: 'Não autenticado' });
  }

  try {
    // Delete persona
    const response = await fetch(`http://localhost:5001/api/persona/${req.params.id}?user_id=${req.session.userId}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' }
    });

    const data = await response.json();
    
    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    res.json(data);
  } catch (error) {
    console.error('[Persona] Delete error:', error);
    res.status(500).json({ detail: 'Erro ao deletar persona' });
  }
});

app.get('/api/persona/:id', async (req, res) => {
  if (!req.session.userId) {
    return res.status(401).json({ detail: 'Não autenticado' });
  }

  try {
    // Get specific persona
    const response = await fetch(`http://localhost:5001/api/persona/${req.params.id}?user_id=${req.session.userId}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    const data = await response.json();
    
    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    res.json(data);
  } catch (error) {
    console.error('[Persona] Get by ID error:', error);
    res.status(500).json({ detail: 'Erro ao buscar persona' });
  }
});

// Proxy all OTHER /api requests to Python backend (EXCEPT auth, invites, onboarding, and persona handled above)
// pathRewrite adds /api prefix back (Express removes it when using app.use('/api'))
app.use('/api', createProxyMiddleware({
  target: 'http://localhost:5001',
  pathRewrite: {'^/': '/api/'},
  changeOrigin: true,
  // Allow proxy to handle already-parsed body from express.json()
  // @ts-ignore - parseReqBody option exists in runtime
  parseReqBody: true,
  // Exclude auth, invite, onboarding, and persona endpoints (handled by Express middleware above)
  // Note: pathname here is WITHOUT /api prefix (Express strips it before proxy)
  // @ts-ignore - filter option exists in runtime but not in type definitions
  filter: (pathname: string, req: any) => {
    // Block /auth/*, /invites/*, /onboarding/*, and /persona/* from being proxied
    return !pathname.startsWith('/auth') && !pathname.startsWith('/invites') && !pathname.startsWith('/onboarding') && !pathname.startsWith('/persona');
  },
  // SSE-specific configuration for streaming endpoints
  on: {
    proxyReq: (proxyReq, req, res) => {
      // Re-send body if it was already parsed by express.json()
      if ((req.method === 'POST' || req.method === 'PUT' || req.method === 'PATCH') && req.body) {
        const bodyData = JSON.stringify(req.body);
        proxyReq.setHeader('Content-Type', 'application/json');
        proxyReq.setHeader('Content-Length', Buffer.byteLength(bodyData));
        proxyReq.write(bodyData);
      }
      
      // Set headers for SSE endpoints
      if (req.url?.includes('/stream') || req.url?.includes('/analyze-stream')) {
        proxyReq.setHeader('Accept', 'text/event-stream');
        proxyReq.setHeader('Connection', 'keep-alive');
        proxyReq.setHeader('Cache-Control', 'no-cache');
      }
    },
    proxyRes: (proxyRes, req, res) => {
      // Disable buffering for SSE endpoints
      if (req.url?.includes('/stream') || req.url?.includes('/analyze-stream')) {
        res.setHeader('X-Accel-Buffering', 'no');
        res.setHeader('Cache-Control', 'no-cache, no-transform');
        res.setHeader('Connection', 'keep-alive');
        
        // Preserve SSE content-type
        if (proxyRes.headers['content-type']?.includes('text/event-stream')) {
          res.setHeader('Content-Type', 'text/event-stream');
        }
      }
    },
    error: (err, req, res) => {
      console.error('[SSE Proxy Error]', err);
      // Only send response if res is not a Socket (WebSocket upgrade)
      if ('headersSent' in res && !res.headersSent) {
        (res as Response).status(500).json({ error: 'SSE proxy error' });
      }
    }
  }
}));

app.use((req, res, next) => {
  const start = Date.now();
  const path = req.path;
  let capturedJsonResponse: Record<string, any> | undefined = undefined;

  const originalResJson = res.json;
  res.json = function (bodyJson, ...args) {
    capturedJsonResponse = bodyJson;
    return originalResJson.apply(res, [bodyJson, ...args]);
  };

  res.on("finish", () => {
    const duration = Date.now() - start;
    if (path.startsWith("/api")) {
      let logLine = `${req.method} ${path} ${res.statusCode} in ${duration}ms`;
      if (capturedJsonResponse) {
        logLine += ` :: ${JSON.stringify(capturedJsonResponse)}`;
      }

      if (logLine.length > 80) {
        logLine = logLine.slice(0, 79) + "…";
      }

      log(logLine);
    }
  });

  next();
});

(async () => {
  await seedExperts();
  
  // Serve avatar images and other attached assets
  // This must be before setupVite to avoid Vite intercepting the routes
  app.use('/attached_assets', express.static(path.resolve(process.cwd(), 'attached_assets')));
  
  const server = await registerRoutes(app);
  
  // Register admin routes (protected by RBAC middleware)
  registerAdminRoutes(app);

  app.use((err: any, _req: Request, res: Response, _next: NextFunction) => {
    const status = err.status || err.statusCode || 500;
    const message = err.message || "Internal Server Error";

    res.status(status).json({ message });
    throw err;
  });

  // importantly only setup vite in development and after
  // setting up all the other routes so the catch-all route
  // doesn't interfere with the other routes
  if (app.get("env") === "development") {
    await setupVite(app, server);
  } else {
    serveStatic(app);
  }

  // ALWAYS serve the app on the port specified in the environment variable PORT
  // Other ports are firewalled. Default to 5000 if not specified.
  // this serves both the API and the client.
  // It is the only port that is not firewalled.
  const port = parseInt(process.env.PORT || '5000', 10);
  server.listen({
    port,
    host: "0.0.0.0",
    reusePort: true,
  }, () => {
    log(`serving on port ${port}`);
  });
})();
