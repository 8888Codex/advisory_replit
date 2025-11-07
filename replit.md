# O Conselho - Replit Agent Guide

## Overview
O Conselho is a premium AI consultancy platform providing expert advice through cognitive clones of 18 specialists across 15 disciplines. It consolidates over 450 years of marketing expertise into an accessible, interactive format. The platform utilizes a 20-point "Framework EXTRACT" with Anthropic's Claude to create ultra-realistic AI personalities, offering specialized multi-category consulting.

## Recent Updates (November 2025)

### Landing Page Expert Count Fix
- **Problem**: Landing page displayed "31,900+ Anos de Expertise" instead of "450+" because it counted ALL 1,438 experts instead of just 18 seed experts
- **Solution**: 
  1. Modified `/api/experts` endpoint to combine HIGH_FIDELITY seed experts (from CloneRegistry) with CUSTOM experts (from PostgreSQL)
  2. Added `expertType` field to TypeScript Expert type (`shared/schema.ts`)
  3. Landing.tsx filters by `expertType === "high_fidelity"` to show only 18 seed legends
- **Result**: Correct display of "450+ Anos de Expertise" (18 experts × 25 years)
- **Auto-Redirect**: Authenticated users visiting `/` are automatically redirected to `/home`

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### UI/UX Decisions
The platform features an Apple-style minimalist design with a professional dark-mode aesthetic, utilizing a neutral color palette and a coral accent color. UI components are built with `shadcn/ui` on `Radix UI` and styled with `Tailwind CSS`. Headings use `font-semibold` and corners are `rounded-2xl`.

**Visual Standardization (November 2025)**:
- **Spacing Standard**: `gap-4` (1rem/16px) applied consistently across all major pages for harmonious visual rhythm
- **Icon Color System** (Home Quick Actions):
  - Users: `text-purple-500` with `bg-purple-50 dark:bg-purple-950`
  - Sparkles: `text-amber-500` with `bg-amber-50 dark:bg-amber-950`
  - TrendingUp: `text-blue-500` with `bg-blue-50 dark:bg-blue-950`
- **Pages Standardized**: Home, Categories, Landing, Analytics, Personas, TestCouncil all use consistent gap-4 spacing
- **Design Reference**: Analytics page serves as the aesthetic standard for spacing and layout patterns

### Technical Implementations
- **Frontend**: Developed with React 18, TypeScript, Vite, Wouter for routing, and TanStack Query v5 for server state. State management uses TanStack Query for server state and React Context for themes. Forms are handled with `react-hook-form` and Zod.
- **Backend (Hybrid)**: An Express.js proxy server forwards API requests to a Python/FastAPI backend, handles automatic Python backend startup, and serves the static frontend.
- **Python/FastAPI Backend**: Uses FastAPI for async API routes and AsyncAnthropic client for non-blocking AI calls. **Data storage** is primarily in-memory using Pydantic models (`MemStorage` class) - **NOTE: Auto-cloned experts are not persisted across server restarts** and will need PostgreSQL migration in the future for permanent storage.
- **Invite-Based Authentication System (November 2025)**: Secure registration system requiring unique invite codes. PostgreSQL tables: `users` (username, email, bcrypt password, availableInvites=5), `invite_codes` (code, creatorId, usedBy, usedAt), `onboarding_status` (userId, currentStep, industry, companySize, targetAudience, goals, enrichmentLevel, completedAt), `password_reset_tokens` (userId, hashedToken SHA-256, expiresAt, usedAt), and `login_audit` (userId, action, success, ipAddress, userAgent, metadata JSONB, timestamp). Express session management with `connect-pg-simple` store for persistent sessions. Three-layer security: (1) Express handlers validate `req.session.userId` before forwarding requests, (2) Proxy filter blocks direct access to `/auth/*` and `/invites/*` endpoints, (3) Only authenticated userId passed to Python backend. Frontend auth via `AuthContext` provider with `ProtectedRoute` wrapper. Settings page allows users to generate/manage invite codes (max 5 available per user). All passwords hashed with bcrypt. **PostgreSQL-backed onboarding** (November 2025): User onboarding progress migrated from localStorage to PostgreSQL `onboarding_status` table with shared hook `useOnboardingComplete()` preventing race conditions. **Rate limiting system** (November 2025): PostgreSQL-backed rate limiting using `rate-limiter-flexible` with limits of 5 login attempts per 15min and 3 registrations per hour per IP. Frontend disables forms during cooldown and shows "Aguarde..." message. Trust proxy configured for accurate IP detection behind Replit proxies. **Password recovery system** (November 2025): Secure token-based password reset using Resend for email delivery. Tokens generated with `secrets.token_urlsafe(32)`, stored as SHA-256 hashes, expire in 1 hour, and marked as used after successful reset. Apple-inspired email templates with clear CTAs. Frontend flows: `/forgot-password` (request reset) → email with link → `/reset-password?token=xxx` (verify & reset) → auto-redirect to `/login`. **Audit logging system** (November 2025): Comprehensive security monitoring tracking all authentication events. PostgreSQL `login_audit` table with 4 optimized indexes (userId, action, success, timestamp) stores action type (login, register, logout, password_reset_request, password_reset_complete), success/failure status, IP address, user agent, and structured JSONB metadata (email, error messages). Express middleware (`logAuthEvent` helper) automatically captures all auth events without breaking auth flow. Python storage methods handle log creation and dynamic filtering. Settings page displays "Histórico de Segurança" section showing 10 most recent activities with success/failure indicators, timestamps, IPs, and error details. Native asyncpg JSONB handling ensures metadata is returned as structured objects (not strings) for proper UI rendering.
- **AI Integration (Cognitive Cloning)**: Employs a 20-point cognitive fidelity framework (Framework EXTRACT) for creating ultra-realistic specialist personalities. Rich Python classes inherit from `ExpertCloneBase` and are dynamically loaded. The Claude API (`claude-sonnet-4-20250514`) processes dynamic system prompts. **Expert creation system** (`/api/experts/auto-clone-stream`) uses a **4-tier research pipeline** with YouTube transcript extraction (November 2025): (1) Perplexity API for biographical/philosophical research, (2) YouTube Data API v3 for video/lecture discovery (up to 10 videos with real metrics), (3) **YouTube Transcript API** extracts full transcripts from top 5 videos (~25K chars of authentic speech patterns, mannerisms, and quotes), (4) Claude synthesis combining all sources into 350+ line Framework EXTRACT prompts with maximum cognitive fidelity (19-20/20 score). **Architecture upgrade**: Auto-cloned experts now generate as **full Python classes** (not JSON), inheriting from `ExpertCloneBase` and saved to `python_backend/clones/custom/`, achieving complete parity with the 18 seed experts. CloneRegistry auto-discovers custom clones on startup for seamless integration.
- **Disney Effect UX Features (November 2025)**: Premium user experience enhancements creating "magical moments" during expert creation:
  1. **Sample Conversations**: Auto-generates 3 contextual Q&A samples after expert synthesis using Claude 3.5 Haiku (`claude-3-5-haiku-20241022`), displaying the expert's authentic voice and thought patterns before saving
  2. **Real-time SSE Progress**: Server-Sent Events streaming via `/api/experts/auto-clone-stream` endpoint with 7 animated progress steps (researching → analyzing → synthesizing → avatar-generation → score-calculation → **category-inference** → generating-samples) using Framer Motion
  3. **Auto Avatar Generation**: Integrated stock image search automatically downloads professional avatars to `attached_assets/custom_experts/`, providing polished visual identity without manual uploads
  4. **Cognitive Fidelity Score**: Analyzes Framework EXTRACT quality across 8 dimensions (Essência, Expertise, Storytelling, Terminologia, Raciocínio, Adaptação, Conversação, Transformação) with 0-20 point scoring system and visual breakdown showing each category's contribution
  5. **AI Category Inference** (November 2025): Automatic categorization using Claude 3.5 Haiku during auto-clone process - analyzes expert name, title, bio, and context to intelligently assign one of 10 categories (marketing, positioning, creative, direct_response, content, seo, social, growth, viral, product) with fallback to "marketing" on error
  6. **Interactive Preview**: Test chat functionality integrated in Create.tsx allows users to converse with newly created experts before committing, using `/api/experts/test-chat` endpoint
- **Council Room**: Features real-time SSE streaming for follow-up questions to a council of experts, ensuring full memory retention. Responses are conversational, in Brazilian Portuguese, and experts dialogue with each other. PostgreSQL is used for message persistence.
- **Multi-LLM Router**: Routes tasks to different LLM tiers for cost optimization. Simple tasks (e.g., expert recommendations, suggested questions) use Claude Haiku (FAST tier), while complex tasks (e.g., 1:1 chat, Council dialogue, synthesis) use Claude Sonnet (STANDARD tier).
- **Persona Intelligence Hub**: A premium profile system for user persona creation, enriched with **100% real YouTube data** via YouTube Data API v3 and Reddit insights via Perplexity. Data is stored in PostgreSQL (`user_personas` table). Features various research modes (Quick, Strategic, Complete) orchestrated using Claude Haiku and Sonnet. **Zero mock data** - all video statistics (views, likes, channels, dates) are authentic and verifiable.
- **Analytics & Insights Dashboard**: Provides comprehensive user activity metrics, expert usage patterns, and AI-generated personalized recommendations. Utilizes PostgreSQL (`user_activity` table) and a Python `AnalyticsEngine`.
- **Semantic Search**: An AI-powered expert recommendation system on the `/categories` page that analyzes user challenges and suggests relevant specialists across all categories.

### System Design Choices
- **Monorepo Structure**: Organized into `/client` (React), `/server` (Express), `/python_backend` (FastAPI), and `/shared` (TypeScript types).
- **Data Flow**: User interaction flows from React -> TanStack Query -> Express -> FastAPI -> Storage/AI -> React.
- **Route Architecture**: Clear separation between public and authenticated areas:
  - `/` - Public Landing page with conversion-focused messaging
  - `/home` - Authenticated dashboard with featured experts and quick actions
  - `/onboarding` - 4-step user onboarding flow
  - All expert interactions require `onboarding_complete` localStorage flag
- **Landing Page (Conversion-Focused)**: Route `/` serves `Landing.tsx` - a Steve Jobs-inspired minimalist conversion funnel with "450+ Anos de Expertise em Marketing" core message, expert tour carousel, and final CTA redirecting to `/onboarding`.
- **Authenticated Dashboard**: Route `/home` serves authenticated users with featured expert grid (6 experts), quick action cards (Categories, Council, Personas), and analytics teaser. Only accessible after onboarding completion.
- **Onboarding Gate & Header Authentication**: localStorage-based authentication using `onboarding_complete` flag. Header component uses `useLocation()` hook to reactively update when authentication state changes:
  - Before onboarding: Logo redirects to `/`, no "Home" link visible
  - After onboarding: Logo redirects to `/home`, "Home" link appears in navigation
  - Persists across all page navigations
- **Expert Assets**: All 18 marketing experts use real professional stock photos uploaded to `/attached_assets/stock_images/`. Avatar paths in `python_backend/seed.py` now reference exact user-uploaded filenames (e.g., "Philip Kotler.png", "David Ogilvy .png", "Gary Vaynerchuk .jpg"). Photos render successfully across all platform interfaces (dashboard, categories, chats, landing carousel). Note: Some filenames contain trailing spaces and inconsistent casing, but this doesn't affect current Linux-based deployment.
- **Multi-Category Navigation**: Supports 15 distinct categories with consistent iconography and filtering.
- **Personalization System**: Includes expert recommendations, contextual AI prompt enrichment, Perplexity-powered suggested questions, business insights, and smart filters.
- **Research Tools Integration**: Experts can access real-time research capabilities via Perplexity API, including YouTube research, trend analysis, and news monitoring.

## External Dependencies

- **Anthropic Claude API**: For AI model interactions, cognitive cloning, and conversational AI.
- **YouTube Data API v3**: Official Google API for retrieving real video metadata (views, likes, channels, thumbnails). Free tier provides 10,000 queries/day.
- **Perplexity API**: For real-time research capabilities and content enrichment (Reddit insights, trends, news).
- **React**: Frontend library.
- **Vite**: Frontend build tool.
- **Wouter**: Client-side routing.
- **TanStack Query**: Server state management in the frontend.
- **shadcn/ui & Radix UI**: UI component libraries.
- **Tailwind CSS**: Utility-first CSS framework.
- **Express.js**: Proxy server.
- **FastAPI**: Python web framework for the backend.
- **AsyncAnthropic**: Asynchronous Python client for the Anthropic API.
- **Uvicorn**: ASGI server.
- **Pydantic**: Data validation and settings management for Python.
- **Zod**: TypeScript-first schema declaration and validation.
- **Framer Motion**: Animation library for React.
- **PostgreSQL**: Database for persisting council messages, user personas, and activity analytics.