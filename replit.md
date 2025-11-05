# AdvisorIA - Replit Agent Guide

## Overview
AdvisorIA is a premium AI consultancy platform offering expert advice through cognitive clones of 18 specialists across 15 disciplines. It leverages a 20-point "Framework EXTRACT" with Anthropic's Claude to create ultra-realistic AI personalities. The platform features a React/TypeScript frontend, an Express.js proxy, and a Python/FastAPI backend with asynchronous AI integration. Its purpose is to consolidate 450+ years of marketing expertise into an accessible, interactive format, providing specialized multi-category consulting.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend
- **Framework & Tooling**: React 18 with TypeScript, Vite, Wouter for routing, TanStack Query v5 for server state.
- **UI Component System**: shadcn/ui on Radix UI, Tailwind CSS for styling, professional dark-mode aesthetic (Apple-style minimalist design with a neutral palette and coral accent color).
- **State Management**: TanStack Query for server state, React Context for theme, react-hook-form with Zod for forms.

### Backend (Hybrid Proxy + Python)
- **Express.js Proxy Server**: Forwards `/api` requests to Python backend, handles automatic Python backend startup, serves static frontend in production.
- **Python/FastAPI Backend**: FastAPI for async API routes, AsyncAnthropic client for non-blocking AI calls.
- **API Endpoints**: Includes endpoints for experts, categories, suggested questions, chat, auto-cloning, user profiles, insights, and persona management.
- **Storage Layer**: In-memory Python storage (MemStorage) using Pydantic models.

### AI Integration - Cognitive Cloning
- **Framework EXTRACT de 20 Pontos**: Each specialist utilizes a 20-point cognitive fidelity framework for ultra-realistic personalities, covering identity, experiences, reasoning, terminology, and more.
- **Implementation Architecture**: Rich Python classes inherit from `ExpertCloneBase`, dynamically loaded via `CloneRegistry`. Claude API (`claude-sonnet-4-20250514`) processes dynamic system prompts.
- **Specialists**: 18 specialists with cross-referencing capabilities and Socratic questioning.

### Council Room - Real-Time SSE Streaming
- **Feature**: Allows users to ask follow-up questions to a council of experts with real-time streaming responses and full memory retention.
- **Architecture**: SSE Streaming Endpoint (`GET /api/council/chat/{session_id}/stream`), PostgreSQL for message persistence (`council_messages` table), sequential expert contributions with visual attribution, and synthesis of consensus.
- **Event Types**: `user_message`, `expert_thinking`, `contribution`, `synthesizing`, `synthesis`, `complete`, `error`.
- **Frontend (CouncilRoom.tsx)**: Uses `EventSource` API, ReactMarkdown for rich formatting, displays expert avatars and loading states.
- **Backend (FastAPI)**: `StreamingResponse` for SSE, integrates `CouncilOrchestrator`, loads full conversation history for context.
- **Memory System**: Nov 2025 bug fix - experts now receive full `analysis_context` including initial problem, consensus, and all prior contributions. Fixed issue where `user_context["analysis_context"]` was passed but never used in `_get_expert_analysis()`.

### Research Tools Integration
- **Feature**: AdvisorIA experts can access real-time research capabilities via Perplexity API.
- **Available Tools**:
    1. **YouTubeResearchTool**: Finds relevant marketing campaigns and content on YouTube.
    2. **TrendAnalysisTool**: Analyzes Google Trends data and market movements.
    3. **NewsMonitorTool**: Monitors recent news about markets, competitors, and industries.
- **Integration Architecture**: Tools use Perplexity's `sonar-pro` model, lazy initialization, async `httpx` client, and structured JSON responses. Tools are documented in expert system prompts.

### Key Architectural Decisions
- **Monorepo Structure**: `/client` (React), `/server` (Express), `/python_backend` (FastAPI), and `/shared` (TypeScript types).
- **Data Flow**: User -> React -> TanStack Query -> Express -> FastAPI -> Storage/AI -> React.
- **UX/UI Decisions**: Apple-style minimalist design, neutral color palette (grays, coral accent), subtle animations, `font-semibold` for headings, rounded-2xl corners.
- **Multi-Category Navigation System**: 15 distinct categories with consistent iconography and filtering.
- **Personalization System**: Expert recommendations, contextual AI prompt enrichment, Perplexity-powered suggested questions, business insights, and smart filters.

## External Dependencies

- **Anthropic Claude API**: AI model interactions and cognitive cloning.
- **Perplexity API**: Research for auto-cloning and content generation.
- **React**: Frontend library.
- **Vite**: Build tool.
- **Wouter**: Client-side router.
- **TanStack Query**: Server state management.
- **shadcn/ui & Radix UI**: UI component libraries.
- **Tailwind CSS**: Styling framework.
- **Express.js**: Proxy server.
- **FastAPI**: Python backend framework.
- **AsyncAnthropic**: Asynchronous Python client for Anthropic API.
- **Uvicorn**: ASGI server for FastAPI.
- **Pydantic**: Data validation for Python models.
- **Zod**: Schema declaration and validation for TypeScript.
- **Framer Motion**: Animation library for React.
- **PostgreSQL**: Database for storing persona data and council messages.