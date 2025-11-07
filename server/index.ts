import express, { type Request, Response, NextFunction } from "express";
import { createProxyMiddleware } from 'http-proxy-middleware';
import { spawn } from 'child_process';
import path from 'path';
import { registerRoutes } from "./routes";
import { setupVite, serveStatic, log } from "./vite";
import { seedExperts } from "./seed";

const app = express();

// Start Python backend automatically
function startPythonBackend() {
  log("Starting Python backend on port 5001...");
  const pythonProcess = spawn('python3', ['-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '5001', '--reload'], {
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

// Proxy all /api requests to Python backend BEFORE any other middleware
// This ensures the request body is not consumed by express.json()
// pathRewrite adds /api prefix back (Express removes it when using app.use('/api'))
app.use('/api', createProxyMiddleware({
  target: 'http://localhost:5001',
  pathRewrite: {'^/': '/api/'},
  changeOrigin: true,
  // SSE-specific configuration for streaming endpoints
  on: {
    proxyReq: (proxyReq, req, res) => {
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

declare module 'http' {
  interface IncomingMessage {
    rawBody: unknown
  }
}
app.use(express.json({
  verify: (req, _res, buf) => {
    req.rawBody = buf;
  }
}));
app.use(express.urlencoded({ extended: false }));

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
