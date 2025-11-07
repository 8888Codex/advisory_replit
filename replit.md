# O Conselho - Replit Agent Guide

## Overview
O Conselho is a premium AI consultancy platform offering expert advice through cognitive clones of 18 specialists across 15 disciplines. It consolidates over 450 years of marketing expertise into an accessible, interactive format, leveraging a 20-point "Framework EXTRACT" with Anthropic's Claude for ultra-realistic AI personalities and specialized multi-category consulting.

## User Preferences
Preferred communication style: Simple, everyday language.

## Recent Changes (November 7, 2025)

### Avatar Integration Completed
- **Fixed duplicate seeding**: Disabled redundant `seed_legends()` call in Python backend startup to prevent 36 duplicate experts (18 from CloneRegistry + 18 from PostgreSQL).
- **Centralized avatar mapping**: Created `SEED_EXPERT_AVATARS` dictionary in `python_backend/clones/registry.py` mapping all 18 seed experts to their avatar paths (e.g., `/avatars/philip-kotler.png`).
- **Automatic avatar assignment**: CloneRegistry now automatically applies avatars to seed experts during instantiation via `clone_instance.avatar = SEED_EXPERT_AVATARS[clone_name]`.
- **Fixed name mismatches**: Corrected expert names in avatar mapping ("Al Ries & Jack Trout" → "Al Ries", "Claude C. Hopkins" → "Claude Hopkins").
- **Verified integration**: All 18 seed experts now have valid avatar paths. Landing page displays 19 avatar images with zero 404 errors. End-to-end test confirmed successful loading.

### Architecture Clarification
- **CloneRegistry**: 18 seed HIGH_FIDELITY experts with avatars (in-memory Python classes).
- **PostgreSQL**: Only stores CUSTOM user-created experts from `/api/experts/auto-clone`.
- **API `/api/experts`**: Combines CloneRegistry seed experts + PostgreSQL custom experts for complete expert list.

### Production Security Hardening (November 7, 2025)
- **CORS Security**: Replaced wildcard `allow_origins=["*"]` with environment-based origins. Development allows `localhost`, production requires `REPL_SLUG` and `REPL_OWNER` environment variables or throws `ValueError` (no unsafe fallback).
- **SESSION_SECRET Enforcement**: Made `SESSION_SECRET` mandatory in production environments. Throws error if not set in production, uses safe fallback only in development (`NODE_ENV !== 'production'`).
- **Python Backend Configuration**: Fixed `--reload` flag to only run in development mode. Production uses stable server without auto-reload.
- **TypeScript LSP Cleanup**: Fixed proxy middleware type errors in `server/index.ts` using `// @ts-ignore` for filter option (exists in runtime but not in type definitions).
- **Code Cleanup**: Deleted 4 backup files (`main.py.new`, `main.py.new2`, `main.py.broken`, `main.py.original`) to reduce technical debt.
- **Production Readiness**: All E2E tests passed. Zero LSP errors. Application verified ready for Replit Autoscale deployment.

## System Architecture

### UI/UX Decisions
The platform features an Apple-style minimalist design with a professional dark-mode aesthetic, utilizing a neutral color palette and a coral accent. UI components are built with `shadcn/ui` on `Radix UI` and styled with `Tailwind CSS`. Visual standardization includes consistent `gap-4` spacing, a defined icon color system for quick actions, and standardized page layouts (Home, Categories, Landing, Analytics, Personas, TestCouncil).

### Technical Implementations
- **Frontend**: React 18, TypeScript, Vite, Wouter for routing, TanStack Query v5 for server state, React Context for themes, `react-hook-form` and Zod for forms.
- **Backend (Hybrid)**: An Express.js proxy server forwards API requests to a Python/FastAPI backend, handles automatic Python backend startup, and serves the static frontend.
- **Python/FastAPI Backend**: Uses FastAPI for async API routes and AsyncAnthropic client. Data storage for auto-cloned experts is currently in-memory using Pydantic models (`MemStorage`), with future plans for PostgreSQL migration.
- **Authentication System**: Invite-based registration, secure password reset with Resend email delivery, and PostgreSQL-backed audit logging. User onboarding progress is also stored in PostgreSQL. A rate-limiting system protects against brute-force attacks.
- **AI Integration (Cognitive Cloning)**: Employs a 20-point cognitive fidelity framework (Framework EXTRACT). Expert creation uses a 4-tier research pipeline: Perplexity for biographical data, YouTube Data API v3 for video discovery, YouTube Transcript API for speech patterns, and Claude for synthesis into Framework EXTRACT prompts. Auto-cloned experts are generated as full Python classes.
- **Disney Effect UX Features**: Enhancements for expert creation including sample conversations, real-time SSE progress streaming with animated steps, auto avatar generation, a cognitive fidelity score (0-20 points), AI category inference using Claude, and an interactive test chat.
- **Council Room**: Real-time SSE streaming for follow-up questions to a council of experts, ensuring memory retention and conversational, multi-expert dialogue. Messages are persisted in PostgreSQL.
- **Multi-LLM Router**: Optimizes costs by routing tasks to different LLM tiers (Claude Haiku for simple tasks, Claude Sonnet for complex tasks).
- **Persona Intelligence Hub**: Premium profile system for user personas, enriched with real YouTube and Reddit data via YouTube Data API v3 and Perplexity, stored in PostgreSQL.
- **Analytics & Insights Dashboard**: Provides user activity and expert usage metrics, with AI-generated recommendations, using PostgreSQL and a Python `AnalyticsEngine`.
- **Semantic Search**: AI-powered expert recommendation system on the `/categories` page.

### System Design Choices
- **Monorepo Structure**: `/client`, `/server`, `/python_backend`, `/shared`.
- **Data Flow**: React -> TanStack Query -> Express -> FastAPI -> Storage/AI -> React.
- **Route Architecture**: Public landing page (`/`), authenticated dashboard (`/home`), and a 4-step onboarding flow (`/onboarding`).
- **Authentication Gate**: Onboarding completion (stored in localStorage and PostgreSQL) gates access to authenticated areas.
- **Expert Assets**: Professional stock photos for 18 marketing experts stored in `client/public/avatars/` with URL-safe filenames. Seeding is idempotent.
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