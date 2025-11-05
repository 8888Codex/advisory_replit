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
- **Conversational Transformation (Nov 2025)**: Council Room responses transformed from formal academic format to natural Brazilian Portuguese conversation:
  - **Expert Responses**: Conversational tone (500-600 words max), explicit memory references ("Como mencionei...", "Voltando ao que discutimos..."), Brazilian expressions ("O lance é...", "Olha só..."), token limit 800 (vs. 3000 before)
  - **Synthesis**: Moderator tone ("Ok, pessoal trouxe pontos interessantes..."), 150-200 words, informal structure, token limit 500 (vs. 2500 before)
  - **Language**: 100% PT-BR guaranteed with explicit instruction at prompt start
  - **Format**: Free-flowing conversation vs. structured headers/bullets
- **Roundtable Discussion (Nov 2025)**: Experts now dialogue with each other, not just provide parallel opinions:
  - **Sequential Context Passing**: Each expert sees contributions from colleagues who already spoke (`colleague_contributions` parameter)
  - **Dialogue Instructions**: Mandatory instructions to comment on colleagues: "Concordo com [nome]...", "Interessante o ponto do [nome], mas...", "Diferente do que [nome] sugeriu..."
  - **Conversational Build-up**: Expert 2 references Expert 1, Expert 3 references 1+2, creating authentic roundtable dynamic
  - **Synthesis Evolution**: Synthesis now narrates the CONVERSATION ("Teve uma discussão boa - [Expert 1] começou com X, aí [Expert 2] complementou...") highlighting agreement, divergence, and consensus evolution
  - **Implementation**: `crew_council.py` `_get_expert_analysis()` accepts optional `colleague_contributions`, `main.py` accumulates via `current_round_contributions` list
  - **Backward Compatible**: Works without `colleague_contributions` for initial analysis (no colleagues yet)
  - **Sprint 1 (Nov 2025)**: Enhanced dialogue specificity with checkmark-based prompt examples forcing concrete point references, PT-BR quotation translation rules
  - **Sprint 2 (Nov 2025)**: Visual polish - colleague mention badges ("Dialoga com X"), synthesis differentiation (Users icon, "🎯 Consenso da Mesa", `border-primary/30`, `bg-primary/10`)

### Multi-LLM Router (Nov 2025) - Cost Optimization Architecture
- **Purpose**: Route simple tasks to cheaper models and complex tasks to premium models for significant cost reduction.
- **Implementation**: `python_backend/llm_router.py` - task-based routing with unified Anthropic API.
- **Task Routing Map**:
  - **FAST tier (Claude Haiku 3.5)**: Expert recommendations, suggested questions (~$0.25/1M input tokens)
  - **STANDARD tier (Claude Sonnet 4)**: 1:1 chat, Council dialogue, auto-cloning, synthesis (~$3/1M input tokens)
- **Status (Nov 2025)**:
  - ✅ **Fully Operational**: Active in production with Claude Haiku 3.5 for cost optimization
  - ✅ End-to-end tested: Semantic search, recommendations, Quick Actions all working with Haiku
  - ✅ Logs confirm routing: "[LLM Router] Using Claude Haiku for recommend_experts (cost-optimized ~92% cheaper)"
  - ⚡ **Simple integration**: No SDK complexity - uses same AsyncAnthropic client for both tiers
- **Actual Savings**: ~92% cost reduction on FAST tier tasks (Haiku vs Sonnet)
  - Haiku: $0.25 input / $1.25 output per 1M tokens
  - Sonnet: $3 input / $15 output per 1M tokens
  - **12x cheaper** for ~60% of LLM calls (recommendations, questions)
- **Architecture Quality**: Clean, maintainable design using single API provider - no fallback complexity needed

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

### Semantic Search on Categories Page (Nov 2025)
- **Feature**: AI-powered expert recommendation system that analyzes user's specific challenge and recommends the most relevant specialists across ALL categories.
- **Location**: `/categories` page (main category grid page), prominent search card positioned ABOVE the category grid.
- **Architecture**:
  - **Frontend**: Debounced textarea (800ms), min 10 chars for analysis, integrates with `/api/recommend-experts` endpoint.
  - **Backend**: Reuses existing TestCouncil recommendation engine (Anthropic Claude analysis of problem vs. expert capabilities).
  - **Cross-Category Search**: NO category filter - searches all 18 experts across all categories for maximum relevance.
- **UI/UX Flow**:
  1. User describes challenge in textarea (generic placeholder for cross-category search)
  2. Loading state: "🔍 Analisando seu desafio..."
  3. Top 5 experts displayed with Avatar, stars (1-5), and AI-generated justification
  4. Two-button layout per card: "Conversar" (direct chat) + "Conselho" (add to council)
  5. FAB (Floating Action Button) appears when experts selected for council
  6. "Iniciar Conselho" navigates to TestCouncil with pre-selected experts and challenge
- **Quick Actions**:
  - **"Conversar" button**: Direct navigation to `/chat/{expertId}` for 1:1 conversation
  - **"Conselho" button**: Toggle expert in/out of council selection (visual feedback: outline ↔ default variant, "Conselho" ↔ "Adicionado")
  - **FAB (Fixed bottom-right)**: Shows count "N especialistas selecionados", navigates to `/test-council` with localStorage pre-selection
- **State Management**: 
  - `councilExperts` state tracks selected expert IDs
  - localStorage keys: `preselectedExperts` (array), `preselectedProblem` (string)
  - TestCouncil auto-loads from localStorage on mount, cleans up immediately
- **Safety Guards**: FAB only appears when `councilExperts.length > 0`, button disabled if empty, `startCouncil()` guards against zero-selection navigation
- **Fallback**: Complete expert grid always visible below recommendations (hybrid approach - AI suggestions + manual fallback)
- **Implementation**: Sprint 1 (semantic search + recommendations), Sprint 2 (Quick Actions + FAB + contextual hints), Nov 2025

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