# O Conselho - Replit Agent Guide

## Overview
O Conselho is a premium AI consultancy platform leveraging cognitive clones of 18 specialists across 15 disciplines to offer expert advice. It condenses over 450 years of marketing expertise, using a 20-point "Framework EXTRACT" with Anthropic's Claude to create ultra-realistic AI personalities and specialized multi-category consulting. The platform aims to provide accessible and interactive expert guidance, focusing on high-fidelity AI personality replication and advanced consulting capabilities.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### UI/UX Decisions
The platform features an Apple-style minimalist design with a professional dark-mode aesthetic, utilizing a neutral color palette and a coral accent. UI components are built with `shadcn/ui` on `Radix UI` and styled with `Tailwind CSS`. Visual standardization includes consistent `gap-4` spacing, a defined icon color system for quick actions, and standardized page layouts. All pages are comprehensively optimized for mobile devices using consistent mobile-first responsive patterns, including responsive breakpoints, touch-friendly UX, typography scaling, adaptive layouts, and a consistent spacing system.

### Technical Implementations
- **Frontend**: React 18, TypeScript, Vite, Wouter for routing, TanStack Query v5 for server state, React Context for themes, `react-hook-form` and Zod for forms.
- **Backend (Hybrid)**: An Express.js proxy server forwards API requests to a Python/FastAPI backend, handles automatic Python backend startup, and serves the static frontend. The Python/FastAPI backend uses FastAPI for async API routes and AsyncAnthropic client.
- **Authentication System**: Invite-based registration, secure password reset with Resend email delivery, PostgreSQL-backed audit logging, and user onboarding progress tracking. A rate-limiting system is in place. A 3-tier role-based access control system (user, admin, superadmin) is implemented with PostgreSQL-backed roles and RBAC middleware to protect administrative endpoints.
- **AI Integration (Cognitive Cloning)**: Employs a 20-point cognitive fidelity framework (Framework EXTRACT) for creating expert personalities. This involves a 4-tier research pipeline using Perplexity, YouTube Data API v3, and YouTube Transcript API, with Claude for synthesis. Auto-cloned experts are generated as full Python classes.
- **Disney Effect UX Features**: Enhancements for expert creation include sample conversations, real-time SSE progress streaming, auto avatar generation, cognitive fidelity scoring, AI category inference, and an interactive test chat.
- **Council Room**: Features real-time SSE streaming for multi-expert dialogue, memory retention, and message persistence in PostgreSQL.
- **Multi-LLM Router**: Optimizes costs by routing tasks to different LLM tiers (e.g., Claude Haiku for simple tasks, Claude Sonnet for complex tasks).
- **Persona Intelligence Hub**: A premium profile system for user personas, enriched with real YouTube and Reddit data via YouTube Data API v3 and Perplexity, stored in PostgreSQL.
- **Analytics & Insights Dashboard**: Provides user activity and expert usage metrics with AI-generated recommendations, using PostgreSQL and a Python `AnalyticsEngine`.
- **Semantic Search**: AI-powered expert recommendation system.
- **Expert Card Component**: A unified `ExpertCard` component (`client/src/components/ExpertCard.tsx`) replaces inconsistent implementations, offering "rich" and "compact" variants with smart data hydration and interactive features.
- **Security Hardening**: Implemented comprehensive route protection for all authenticated routes, environment-based CORS security, mandatory `SESSION_SECRET` in production, and proper handling of Python backend reload.
- **Background Persona Enrichment**: Non-blocking UX for persona enrichment (30s-7min depending on level). Users can immediately access the platform while enrichment runs in background. Features real-time status polling (`EnrichmentStatusBanner`), toast notifications on completion, and three enrichment tiers (Quick ~30-45s, Strategic ~2-3min, Complete ~5-7min). Status tracking via `enrichment_status` field ("pending" | "processing" | "completed" | "failed") and `enrichment_level` field in `user_personas` table.
  - **Architecture Fix (2025-11-07)**: Moved all UserPersona CRUD methods from MemStorage to PostgresStorage (production uses PostgresStorage). Fire-and-forget pattern implemented for background tasks (completeOnboarding, enrichment) ensuring immediate navigation to /home without blocking user experience.
- **Multi-Persona Management System (2025-11-08)**: Complete persona CRUD operations with list/detail views and active persona switching. Fully tested with end-to-end Playwright tests confirming all functionality works correctly.
  - **3-Layer Architecture**: Express proxy (session auth + userId injection) → FastAPI routes (persona ownership validation) → PostgresStorage (async connection pool)
  - **Backend Routes**: Express handles `GET /api/persona/list`, `POST /api/persona/set-active`, `GET /api/persona/:id`, all extract userId from `req.session.userId` and forward to Python backend with query parameter
  - **PostgresStorage Methods** (lines 1316-1378): `list_user_personas(user_id)` returns all personas ordered by creation date, `set_active_persona(user_id, persona_id)` updates users.active_persona_id using `async with self.pool.acquire() as conn:` pattern
  - **Frontend Pages**: `/personas` grid view with persona cards, `/personas/:id` detailed view with enrichment modules, active persona summary card on `/home` with "Manage Personas" navigation
  - **Critical Bug Fixes**: (1) Relocated PostgresStorage methods from module scope to class body - initial attempt placed them after class definition at line 2078 instead of inside class which ends at 1312; (2) Fixed connection pattern from `_get_db_connection()` to `async with self.pool.acquire() as conn:`; (3) Fixed user_id migration issue where personas had `user_id: "default_user"` instead of actual user IDs
  - **Testing**: Comprehensive E2E tests verify login → home → persona list → detail view → back navigation flow works correctly

### System Design Choices
- **Monorepo Structure**: Organized into `/client`, `/server`, `/python_backend`, `/shared`.
- **Data Flow**: React -> TanStack Query -> Express -> FastAPI -> Storage/AI -> React.
- **Route Architecture**: Includes a public landing page (`/`), authenticated dashboard (`/home`), and a 4-step onboarding flow (`/onboarding`). Onboarding completion gates access to authenticated areas.
- **Expert Assets**: Professional stock photos for 18 marketing experts are stored in `client/public/avatars/`.
- **Multi-Category Navigation**: Supports 15 distinct categories.
- **Personalization System**: Includes expert recommendations, contextual AI prompt enrichment, and business insights.
- **Research Tools Integration**: Experts can access real-time research via Perplexity API.

## External Dependencies

- **Anthropic Claude API**: AI model interactions, cognitive cloning.
- **YouTube Data API v3**: Real video metadata, transcript extraction.
- **Perplexity API**: Real-time research, content enrichment.
- **React**: Frontend library.
- **Vite**: Frontend build tool.
- **Wouter**: Client-side routing.
- **TanStack Query**: Server state management.
- **shadcn/ui & Radix UI**: UI component libraries.
- **Tailwind CSS**: CSS framework.
- **Express.js**: Proxy server.
- **FastAPI**: Python web framework.
- **AsyncAnthropic**: Python client for Anthropic API.
- **Uvicorn**: ASGI server.
- **Pydantic**: Data validation (Python).
- **Zod**: Schema validation (TypeScript).
- **Framer Motion**: Animation library.
- **PostgreSQL**: Database for persistence.
- **Resend**: Email delivery for password recovery.