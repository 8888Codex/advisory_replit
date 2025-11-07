import { sql } from "drizzle-orm";
import { pgTable, text, varchar, timestamp, integer, json, index } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const users = pgTable("users", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
  email: text("email").notNull().unique(),
  availableInvites: integer("available_invites").notNull().default(5),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const insertUserSchema = createInsertSchema(users).omit({
  id: true,
  availableInvites: true,
  createdAt: true,
}).extend({
  email: z.string().email("Email inválido"),
  password: z.string().min(6, "Senha deve ter pelo menos 6 caracteres"),
});

export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;

// Invite Codes - Sistema de convites limitados (5 por usuário)
export const inviteCodes = pgTable("invite_codes", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  code: varchar("code", { length: 16 }).notNull().unique(),
  creatorId: varchar("creator_id").notNull(),
  usedBy: varchar("used_by"),
  usedAt: timestamp("used_at"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const insertInviteCodeSchema = createInsertSchema(inviteCodes).omit({
  id: true,
  createdAt: true,
});

export type InsertInviteCode = z.infer<typeof insertInviteCodeSchema>;
export type InviteCode = typeof inviteCodes.$inferSelect;

// ============================================
// ONBOARDING SYSTEM
// ============================================

// Onboarding Status - Tracks user onboarding progress in PostgreSQL (replacing localStorage)
export const onboardingStatus = pgTable("onboarding_status", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  userId: varchar("user_id").notNull().unique(), // One onboarding record per user
  currentStep: integer("current_step").notNull().default(0), // 0=business, 1=audience, 2=goals, 3=enrichment
  
  // Step 1: Business Context
  companyName: text("company_name"),
  industry: text("industry"),
  companySize: text("company_size"), // "1-10", "11-50", "51-200", "200+"
  
  // Step 2: Target Audience
  targetAudience: text("target_audience"),
  
  // Step 3: Goals & Challenges
  goals: text("goals").array(), // ["growth", "positioning", "retention"]
  mainChallenge: text("main_challenge"),
  
  // Step 4: Enrichment Level
  enrichmentLevel: text("enrichment_level"), // "quick" | "strategic" | "complete"
  
  // Completion tracking
  completedAt: timestamp("completed_at"), // null = incomplete, timestamp = completed
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().notNull(),
});

export const insertOnboardingStatusSchema = createInsertSchema(onboardingStatus).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
});

export const updateOnboardingStatusSchema = createInsertSchema(onboardingStatus).omit({
  id: true,
  userId: true,
  createdAt: true,
  updatedAt: true,
}).partial();

export type InsertOnboardingStatus = z.infer<typeof insertOnboardingStatusSchema>;
export type UpdateOnboardingStatus = z.infer<typeof updateOnboardingStatusSchema>;
export type OnboardingStatus = typeof onboardingStatus.$inferSelect;

// ============================================
// PASSWORD RESET SYSTEM
// ============================================

// Password Reset Tokens - Stores secure tokens for password recovery
export const passwordResetTokens = pgTable("password_reset_tokens", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  userId: varchar("user_id").notNull(),
  hashedToken: varchar("hashed_token", { length: 64 }).notNull().unique(), // SHA-256 hash
  expiresAt: timestamp("expires_at").notNull(), // Tokens expire after 1 hour
  usedAt: timestamp("used_at"), // null = not used yet, timestamp = already used
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const insertPasswordResetTokenSchema = createInsertSchema(passwordResetTokens).omit({
  id: true,
  createdAt: true,
});

export type InsertPasswordResetToken = z.infer<typeof insertPasswordResetTokenSchema>;
export type PasswordResetToken = typeof passwordResetTokens.$inferSelect;

// ============================================
// AUDIT LOGGING SYSTEM
// ============================================

// Auth action types for audit logging
export const authActionEnum = z.enum([
  "login",
  "register",
  "logout",
  "password_reset_request",
  "password_reset_complete",
]);

export type AuthAction = z.infer<typeof authActionEnum>;

// Login Audit - Tracks all authentication events for security monitoring
export const loginAudit = pgTable("login_audit", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  userId: varchar("user_id"), // Nullable - failed attempts may not have valid user
  action: text("action").notNull(), // login, register, logout, password_reset_request, etc.
  success: text("success").notNull(), // "true" or "false" as text for consistency
  ipAddress: varchar("ip_address", { length: 45 }), // IPv6 max length
  userAgent: text("user_agent"),
  metadata: json("metadata").$type<Record<string, any>>(), // Additional context (email attempted, error message, etc.)
  timestamp: timestamp("timestamp").defaultNow().notNull(),
}, (table) => ({
  // Indexes for optimized queries
  userIdIdx: index("login_audit_user_id_idx").on(table.userId),
  actionIdx: index("login_audit_action_idx").on(table.action),
  successIdx: index("login_audit_success_idx").on(table.success),
  timestampIdx: index("login_audit_timestamp_idx").on(table.timestamp),
}));

export const insertLoginAuditSchema = createInsertSchema(loginAudit).omit({
  id: true,
  timestamp: true,
});

export type InsertLoginAudit = z.infer<typeof insertLoginAuditSchema>;
export type LoginAudit = typeof loginAudit.$inferSelect;

// Category type for expert specializations
export const categoryTypeEnum = z.enum([
  "marketing",        // Traditional marketing strategy
  "positioning",      // Strategic positioning (Al Ries & Trout)
  "creative",         // Creative advertising (Bill Bernbach)
  "direct_response",  // Direct response marketing (Dan Kennedy)
  "content",          // Content marketing (Seth Godin, Ann Handley)
  "seo",              // SEO & digital marketing (Neil Patel)
  "social",           // Social media marketing (Gary Vaynerchuk)
  "growth",           // Growth hacking & systems (Sean Ellis, Brian Balfour, Andrew Chen)
  "viral",            // Viral marketing (Jonah Berger)
  "product",          // Product psychology & habits (Nir Eyal)
]);

export type CategoryType = z.infer<typeof categoryTypeEnum>;

// Expert type enum for distinguishing seed vs custom experts
export const expertTypeEnum = z.enum(["high_fidelity", "custom"]);
export type ExpertTypeEnum = z.infer<typeof expertTypeEnum>;

export const experts = pgTable("experts", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  name: text("name").notNull(),
  title: text("title").notNull(),
  expertise: text("expertise").array().notNull(),
  bio: text("bio").notNull(),
  avatar: text("avatar"),
  systemPrompt: text("system_prompt").notNull(),
  category: text("category").notNull().default("marketing"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const insertExpertSchema = createInsertSchema(experts).omit({
  id: true,
  createdAt: true,
}).extend({
  category: categoryTypeEnum.default("marketing"),
  expertType: expertTypeEnum.optional(), // Optional for backward compat
});

export type InsertExpert = z.infer<typeof insertExpertSchema>;

// Expert type with expertType field from API (not in DB)
export type Expert = typeof experts.$inferSelect & {
  expertType?: ExpertTypeEnum;
};

export const conversations = pgTable("conversations", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  expertId: varchar("expert_id").notNull(),
  title: text("title").notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().notNull(),
});

export const insertConversationSchema = createInsertSchema(conversations).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
});

export type InsertConversation = z.infer<typeof insertConversationSchema>;
export type Conversation = typeof conversations.$inferSelect;

export const messages = pgTable("messages", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  conversationId: varchar("conversation_id").notNull(),
  role: text("role").notNull(),
  content: text("content").notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const insertMessageSchema = createInsertSchema(messages).omit({
  id: true,
  createdAt: true,
});

export type InsertMessage = z.infer<typeof insertMessageSchema>;
export type Message = typeof messages.$inferSelect;

// Business Profile (Python backend)
export const businessProfileSchema = z.object({
  id: z.string(),
  userId: z.string(),
  companyName: z.string(),
  industry: z.string(),
  companySize: z.string(),
  targetAudience: z.string(),
  mainProducts: z.string(),
  channels: z.array(z.string()),
  budgetRange: z.string(),
  primaryGoal: z.string(),
  mainChallenge: z.string(),
  timeline: z.string(),
  createdAt: z.string(),
  updatedAt: z.string(),
});

export const insertBusinessProfileSchema = z.object({
  companyName: z.string().min(1, "Nome da empresa é obrigatório"),
  industry: z.string().min(1, "Setor é obrigatório"),
  companySize: z.string().min(1, "Tamanho da empresa é obrigatório"),
  targetAudience: z.string().min(1, "Público-alvo é obrigatório"),
  mainProducts: z.string().min(1, "Produtos/serviços são obrigatórios"),
  channels: z.array(z.string()).min(1, "Selecione pelo menos um canal"),
  budgetRange: z.string().min(1, "Faixa de orçamento é obrigatória"),
  primaryGoal: z.string().min(1, "Objetivo principal é obrigatório"),
  mainChallenge: z.string().min(1, "Maior desafio é obrigatório"),
  timeline: z.string().min(1, "Prazo é obrigatório"),
});

export type BusinessProfile = z.infer<typeof businessProfileSchema>;
export type InsertBusinessProfile = z.infer<typeof insertBusinessProfileSchema>;

// ============================================
// COUNCIL & COLLABORATION SCHEMAS
// ============================================

// Council Sessions - Tracks multi-expert collaborative analysis sessions
export const councilSessions = pgTable("council_sessions", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  userId: varchar("user_id").notNull(),
  problem: text("problem").notNull(),
  profileId: varchar("profile_id"),  // Optional BusinessProfile reference
  marketResearch: text("market_research"),  // Perplexity findings
  consensus: text("consensus").notNull(),  // Synthesized council consensus
  citations: text("citations").array(),  // Research sources
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const insertCouncilSessionSchema = createInsertSchema(councilSessions).omit({
  id: true,
  createdAt: true,
});

export type InsertCouncilSession = z.infer<typeof insertCouncilSessionSchema>;
export type CouncilSession = typeof councilSessions.$inferSelect;

// Council Participants - Tracks which experts participated in each session
export const councilParticipants = pgTable("council_participants", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  sessionId: varchar("session_id").notNull(),
  expertId: varchar("expert_id").notNull(),
  expertName: text("expert_name").notNull(),
  contribution: text("contribution").notNull(),  // Expert's analysis
  contributedAt: timestamp("contributed_at").defaultNow().notNull(),
});

export const insertCouncilParticipantSchema = createInsertSchema(councilParticipants).omit({
  id: true,
  contributedAt: true,
});

export type InsertCouncilParticipant = z.infer<typeof insertCouncilParticipantSchema>;
export type CouncilParticipant = typeof councilParticipants.$inferSelect;

// Council Insights - Valuable outputs from council sessions
export const councilInsights = pgTable("council_insights", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  sessionId: varchar("session_id").notNull(),
  userId: varchar("user_id").notNull(),
  expertName: text("expert_name").notNull(),
  insight: text("insight").notNull(),
  category: text("category").notNull(),  // strategy, tactic, warning, case_study, etc.
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const insertCouncilInsightSchema = createInsertSchema(councilInsights).omit({
  id: true,
  createdAt: true,
});

export type InsertCouncilInsight = z.infer<typeof insertCouncilInsightSchema>;
export type CouncilInsight = typeof councilInsights.$inferSelect;

// Expert Collaboration Graph - Tracks which expert combos work well together
export const expertCollaborationGraph = pgTable("expert_collaboration_graph", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  expertIds: text("expert_ids").array().notNull(),  // Array of expert IDs in combo
  expertNames: text("expert_names").array().notNull(),  // Array of expert names
  sessionCount: integer("session_count").notNull().default(0),  // How many times this combo was used
  successCount: integer("success_count").notNull().default(0),  // User feedback: successful outcomes
  lastUsed: timestamp("last_used").defaultNow().notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const insertExpertCollaborationSchema = createInsertSchema(expertCollaborationGraph).omit({
  id: true,
  createdAt: true,
  lastUsed: true,
});

export type InsertExpertCollaboration = z.infer<typeof insertExpertCollaborationSchema>;
export type ExpertCollaboration = typeof expertCollaborationGraph.$inferSelect;

// Council Messages - Chat history for follow-up conversations with the council
export const councilMessages = pgTable("council_messages", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  sessionId: varchar("session_id").notNull(),
  role: text("role").notNull(),  // "user" or "assistant"
  content: text("content").notNull(),  // User question or assistant synthesis
  contributions: text("contributions"),  // JSON: [{expertName, content, order}]
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const insertCouncilMessageSchema = createInsertSchema(councilMessages).omit({
  id: true,
  createdAt: true,
});

export type InsertCouncilMessage = z.infer<typeof insertCouncilMessageSchema>;
export type CouncilMessage = typeof councilMessages.$inferSelect;

// ============================================
// USER MEMORY & PERSONALIZATION SCHEMAS
// ============================================

// User Profiles Extended - Rich psychographic data for personalization
export const userProfilesExtended = pgTable("user_profiles_extended", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  userId: varchar("user_id").notNull().unique(),
  
  // Psychographics
  niche: text("niche"),  // Specific market niche
  businessStage: text("business_stage"),  // startup, growth, mature, transformation
  marketingMaturity: text("marketing_maturity"),  // beginner, intermediate, advanced
  values: text("values").array(),  // Core values that drive decisions
  
  // Expert Affinity - Which experts user engages with most
  expertAffinity: text("expert_affinity"),  // JSON: {expertId: engagementScore}
  
  // Behavioral Insights
  preferredCommunicationStyle: text("preferred_communication_style"),  // direct, storytelling, data-driven, etc.
  topChallenges: text("top_challenges").array(),  // Recurring challenges across sessions
  
  // Metadata
  updatedAt: timestamp("updated_at").defaultNow().notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const insertUserProfileExtendedSchema = createInsertSchema(userProfilesExtended).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
});

export type InsertUserProfileExtended = z.infer<typeof insertUserProfileExtendedSchema>;
export type UserProfileExtended = typeof userProfilesExtended.$inferSelect;

// ============================================
// PERSONA INTELLIGENCE HUB
// ============================================

// User Personas - Unified persona system (Business Context + Psychographics + YouTube Research)
export const userPersonas = pgTable("user_personas", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  userId: varchar("user_id").notNull().unique(),
  
  // Business Context (from Onboarding)
  companyName: text("company_name"),
  industry: text("industry"),
  companySize: text("company_size"),  // "1-10", "11-50", "51-200", etc.
  targetAudience: text("target_audience"),
  mainProducts: text("main_products"),
  channels: text("channels").array(),  // ["online", "retail", "b2b", etc.]
  budgetRange: text("budget_range"),  // "< $10k/month", "$10k-$50k/month", etc.
  primaryGoal: text("primary_goal"),  // "growth", "positioning", "retention", etc.
  mainChallenge: text("main_challenge"),
  timeline: text("timeline"),  // "immediate", "3-6 months", etc.
  
  // Psychographic Data (from Reddit Research)
  demographics: json("demographics").$type<Record<string, any>>(),  // Age, location, occupation
  psychographics: json("psychographics").$type<Record<string, any>>(),  // Personality traits
  painPoints: text("pain_points").array(),  // Array of pain points
  goals: text("goals").array(),  // Array of goals
  values: text("values").array(),  // Array of core values
  communities: text("communities").array(),  // Subreddits where audience hangs out
  behavioralPatterns: json("behavioral_patterns").$type<Record<string, any>>(),  // Decision-making patterns
  contentPreferences: json("content_preferences").$type<Record<string, any>>(),  // Preferred content formats
  
  // YouTube Research Enrichment
  youtubeResearch: json("youtube_research").$type<any[]>(),  // Raw video data from Perplexity
  videoInsights: text("video_insights").array(),  // Extracted key insights
  campaignReferences: json("campaign_references").$type<any[]>(),  // Structured campaign data
  inspirationVideos: json("inspiration_videos").$type<any[]>(),  // Top curated videos
  
  // 8-Module Deep Persona System (Quick/Strategic/Complete)
  psychographicCore: json("psychographic_core").$type<{
    values?: string[];  // Core values that drive decisions
    fears?: string[];  // Dominant fears
    aspirations?: string[];  // Where they want to be in 1-3 years
    thinkingSystem?: 'system1' | 'system2' | 'balanced';  // Kahneman: emotional/fast vs logical/analytical
    decisionDrivers?: string[];  // What motivates their decisions
  }>(),
  
  buyerJourney: json("buyer_journey").$type<{
    awarenessLevel?: string;  // Schwartz 5 levels: unaware, problem-aware, solution-aware, product-aware, most-aware
    currentStage?: string;  // Where they are in journey
    triggers?: string[];  // What moves them to next stage
    objections?: string[];  // Points of friction
    salesCycle?: string;  // 7 days, 3 months, 1 year, etc.
    touchpointsNeeded?: number;  // Average interactions before purchase
  }>(),
  
  behavioralProfile: json("behavioral_profile").$type<{
    cialdiniPrinciples?: Array<{principle: string; priority: number}>;  // 6 principles ranked
    researchChannels?: string[];  // Google, YouTube, LinkedIn, Reddit, etc.
    trustedInfluencers?: string[];  // Who they listen to
    preferredFormat?: string[];  // Video, articles, podcasts, infographics
    engagementPatterns?: Record<string, any>;  // When/how they engage
  }>(),
  
  languageCommunication: json("language_communication").$type<{
    idealTone?: string;  // corporate, casual, technical, inspirational
    vocabularyKeys?: string[];  // Words that resonate
    vocabularyAvoid?: string[];  // Words that repel
    complexityLevel?: string;  // technical-details, simplified, executive-summary
    storyBrandFramework?: {
      hero?: string;
      problem?: string;
      guide?: string;
      plan?: string;
      callToAction?: string;
    };
  }>(),
  
  strategicInsights: json("strategic_insights").$type<{
    coreMessage?: string;  // The phrase that captures their heart
    uniqueValueProp?: string;  // What makes them choose you
    channelPriority?: Array<{channel: string; priority: number}>;  // LinkedIn > Email > Ads
    contentStrategy?: string[];  // Educational, case studies, demos, etc.
    competitivePosition?: string;  // How to differentiate
  }>(),
  
  jobsToBeDone: json("jobs_to_be_done").$type<{
    functionalJob?: string;  // What they're trying to accomplish
    emotionalJob?: string;  // How they want to feel
    socialJob?: string;  // How they want to be seen
    progressDesired?: string;  // From where to where
    successMetrics?: string[];  // How they measure success
  }>(),
  
  decisionProfile: json("decision_profile").$type<{
    decisionMakerType?: string;  // Analytical, Impulsive, Social, Cautious
    decisionCriteria?: Array<{criterion: string; weight: number}>;  // ROI, ease, support, innovation ranked
    decisionSpeed?: string;  // Fast (days), Medium (weeks), Slow (months)
    validationNeeded?: string[];  // Team, Board, Partner, References
    riskTolerance?: string;  // high, medium, low
  }>(),
  
  copyExamples: json("copy_examples").$type<{
    headlines?: string[];  // Ready-to-use headlines
    emailSubjects?: string[];  // Email subject lines
    socialPosts?: string[];  // LinkedIn/Twitter posts
    ctas?: string[];  // Call-to-action examples
    landingPageCopy?: string;  // Full landing page template
  }>(),
  
  // Research Metadata
  enrichmentLevel: text("enrichment_level"),  // "quick" | "strategic" | "complete"
  researchMode: text("research_mode"),  // "quick" | "strategic" | "complete" (deprecated, use enrichmentLevel)
  researchCompleteness: integer("research_completeness").default(0),  // 0-100 score
  lastEnrichedAt: timestamp("last_enriched_at"),
  
  // Timestamps
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().notNull(),
});

export const insertUserPersonaSchema = createInsertSchema(userPersonas).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
  lastEnrichedAt: true,
});

export type InsertUserPersona = z.infer<typeof insertUserPersonaSchema>;
export type UserPersona = typeof userPersonas.$inferSelect;

// ============================================
// ANALYTICS & INSIGHTS DASHBOARD
// ============================================

// User Activity Tracking - Records all user actions for analytics
export const userActivity = pgTable("user_activity", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  userId: varchar("user_id").notNull(),
  activityType: text("activity_type").notNull(), // 'chat_sent' | 'council_started' | 'expert_consulted' | 'message_favorited'
  metadata: json("metadata").$type<{
    expertId?: string;
    expertName?: string;
    categoryId?: string;
    conversationId?: string;
    councilSessionId?: string;
    messageId?: string;
    duration?: number; // Duration in seconds (for sessions)
  }>(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const insertUserActivitySchema = createInsertSchema(userActivity).omit({
  id: true,
  createdAt: true,
});

export type InsertUserActivity = z.infer<typeof insertUserActivitySchema>;
export type UserActivity = typeof userActivity.$inferSelect;

// User Favorites - Save insights, messages, campaigns for later reference
export const userFavorites = pgTable("user_favorites", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  userId: varchar("user_id").notNull(),
  itemType: text("item_type").notNull(), // 'council_message' | 'conversation_message' | 'campaign' | 'consensus'
  itemId: varchar("item_id").notNull(),
  notes: text("notes"), // Optional user notes about why they saved this
  metadata: json("metadata").$type<{
    expertName?: string;
    snippet?: string;
    category?: string;
    tags?: string[];
  }>(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const insertUserFavoriteSchema = createInsertSchema(userFavorites).omit({
  id: true,
  createdAt: true,
});

export type InsertUserFavorite = z.infer<typeof insertUserFavoriteSchema>;
export type UserFavorite = typeof userFavorites.$inferSelect;
