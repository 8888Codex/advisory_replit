from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum

class ExpertType(str, Enum):
    HIGH_FIDELITY = "high_fidelity"
    CUSTOM = "custom"

class CategoryType(str, Enum):
    """Expert specialization categories"""
    MARKETING = "marketing"          # Traditional marketing strategy (Kotler, Ogilvy, Hopkins, Burnett, Wells, Wanamaker)
    POSITIONING = "positioning"       # Strategic positioning (Al Ries & Trout)
    CREATIVE = "creative"             # Creative advertising (Bill Bernbach)
    DIRECT_RESPONSE = "direct_response"  # Direct response marketing (Dan Kennedy)
    CONTENT = "content"               # Content marketing (Seth Godin, Ann Handley)
    SEO = "seo"                       # SEO & digital marketing (Neil Patel)
    SOCIAL = "social"                 # Social media marketing (Gary Vaynerchuk)
    GROWTH = "growth"                 # Growth hacking & systems (Sean Ellis, Brian Balfour, Andrew Chen)
    VIRAL = "viral"                   # Viral marketing (Jonah Berger)
    PRODUCT = "product"               # Product psychology & habits (Nir Eyal)

class Expert(BaseModel):
    id: str
    name: str
    title: str
    expertise: List[str]
    bio: str
    systemPrompt: str
    avatar: Optional[str] = None
    expertType: ExpertType = ExpertType.HIGH_FIDELITY
    category: CategoryType = CategoryType.MARKETING  # Default to marketing
    createdAt: datetime = Field(default_factory=datetime.utcnow)

class ExpertCreate(BaseModel):
    name: str
    title: str
    expertise: List[str]
    bio: str
    systemPrompt: str
    avatar: Optional[str] = None
    expertType: ExpertType = ExpertType.CUSTOM
    category: CategoryType = CategoryType.MARKETING

class Conversation(BaseModel):
    id: str
    expertId: str
    title: str
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

class ConversationCreate(BaseModel):
    expertId: str
    title: str

class Message(BaseModel):
    id: str
    conversationId: str
    role: Literal["user", "assistant"]
    content: str
    createdAt: datetime = Field(default_factory=datetime.utcnow)

class MessageCreate(BaseModel):
    conversationId: str
    role: Literal["user", "assistant"]
    content: str

class MessageSend(BaseModel):
    content: str

class MessageResponse(BaseModel):
    userMessage: Message
    assistantMessage: Message

class BusinessProfile(BaseModel):
    id: str
    userId: str  # Will use session/auth later
    companyName: str
    industry: str
    companySize: str  # "1-10", "11-50", "51-200", "201-1000", "1000+"
    targetAudience: str
    mainProducts: str
    channels: List[str]  # ["online", "retail", "b2b", "marketplace"]
    budgetRange: str  # "< $10k/month", "$10k-$50k/month", "$50k-$100k/month", "> $100k/month"
    primaryGoal: str  # "growth", "positioning", "retention", "launch"
    mainChallenge: str
    timeline: str  # "immediate", "3-6 months", "6-12 months", "long-term"
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

class BusinessProfileCreate(BaseModel):
    companyName: str
    industry: str
    companySize: str
    targetAudience: str
    mainProducts: str
    channels: List[str]
    budgetRange: str
    primaryGoal: str
    mainChallenge: str
    timeline: str

class AgentContribution(BaseModel):
    """Individual expert's contribution to council analysis"""
    expertId: str
    expertName: str
    analysis: str
    keyInsights: List[str]
    recommendations: List[str]

class CouncilAnalysis(BaseModel):
    """Complete council analysis with all expert contributions"""
    id: str
    userId: str
    problem: str
    profileId: Optional[str] = None  # BusinessProfile ID if used
    marketResearch: Optional[str] = None  # Perplexity findings
    contributions: List[AgentContribution]
    consensus: str  # Synthesized final recommendation
    citations: List[str] = []  # From Perplexity
    createdAt: datetime = Field(default_factory=datetime.utcnow)

class CouncilAnalysisCreate(BaseModel):
    """Request payload for council analysis"""
    problem: str
    expertIds: Optional[List[str]] = None  # If None, use all 8 legends

class StreamContribution(BaseModel):
    """Individual expert contribution for SSE streaming"""
    expertName: str
    content: str
    order: int
    isResearching: bool = False  # True when expert is using tools

class CouncilChatMessage(BaseModel):
    """Chat message in council room conversation"""
    id: str
    sessionId: str
    role: Literal["user", "assistant"]
    content: str
    contributions: Optional[List[StreamContribution]] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)

class CouncilChatRequest(BaseModel):
    """Request payload for council chat follow-up"""
    message: str

class ClaudeRecommendation(BaseModel):
    """Expert recommendation from Claude (before enrichment)"""
    expertId: str
    expertName: str
    relevanceScore: int  # 1-5 stars
    justification: str

class ExpertRecommendation(BaseModel):
    """Enriched expert recommendation with avatar and stars (sent to frontend)"""
    expertId: str
    expertName: str
    avatar: Optional[str] = None  # Expert avatar URL
    relevanceScore: int  # 1-5 stars (from Claude analysis)
    stars: int  # Same as relevanceScore (for frontend compatibility)
    justification: str

class RecommendExpertsRequest(BaseModel):
    """Request to get expert recommendations based on problem"""
    problem: str

class ClaudeRecommendationsResponse(BaseModel):
    """Response from Claude with recommendations (before enrichment)"""
    recommendations: List[ClaudeRecommendation]

class RecommendExpertsResponse(BaseModel):
    """Enriched response with recommended experts (sent to frontend)"""
    recommendations: List[ExpertRecommendation]

class AutoCloneRequest(BaseModel):
    """Request to auto-clone a cognitive expert from minimal input"""
    targetName: str
    context: Optional[str] = None  # Optional additional context

class CategoryInfo(BaseModel):
    """Category metadata with expert count"""
    id: str  # CategoryType value
    name: str  # Display name in Portuguese
    description: str  # Short description
    icon: str  # Lucide icon name suggestion
    color: str  # Tailwind color class (e.g., "violet", "emerald")
    expertCount: int  # Number of experts in this category

class Persona(BaseModel):
    """User persona created from strategic research"""
    id: str
    userId: str
    name: str
    researchMode: Literal["quick", "strategic"]
    
    # Core Demographics
    demographics: dict = {}
    
    # Psychographics
    psychographics: dict = {}
    
    # Pain Points & Goals
    painPoints: List[str] = []
    goals: List[str] = []
    values: List[str] = []
    
    # Content & Behavioral Patterns
    contentPreferences: dict = {}
    communities: List[str] = []
    behavioralPatterns: dict = {}
    
    # Raw Research Data (Reddit, YouTube, Perplexity)
    researchData: dict = {}
    
    # Timestamps
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

class PersonaCreate(BaseModel):
    """Request payload for persona creation"""
    mode: Literal["quick", "strategic"]
    targetDescription: str  # "Empreendedores de e-commerce no Brasil"
    industry: Optional[str] = None
    additionalContext: Optional[str] = None
