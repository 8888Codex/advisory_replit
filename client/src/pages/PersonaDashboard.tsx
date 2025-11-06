import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "wouter";
import { 
  Building2, 
  Zap, 
  TrendingUp, 
  Sparkles, 
  Target, 
  AlertCircle,
  CheckCircle2,
  Users,
  Video,
  ExternalLink,
  Lightbulb
} from "lucide-react";
import { motion } from "framer-motion";
import type { UserPersona } from "@shared/schema";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import EnrichmentModal from "@/components/EnrichmentModal";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: "easeOut" } }
};

function LoadingSkeleton() {
  return (
    <div className="min-h-screen py-12">
      <div className="max-w-7xl mx-auto px-6 lg:px-8 space-y-12">
        <div className="space-y-4">
          <Skeleton className="h-12 w-96" />
          <Skeleton className="h-6 w-64" />
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-32 rounded-2xl" />
          ))}
        </div>
        
        <Skeleton className="h-64 rounded-2xl" />
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <Card className="p-12 text-center max-w-lg rounded-2xl" data-testid="card-empty-state">
        <Building2 className="mx-auto h-16 w-16 text-muted-foreground mb-4" data-testid="icon-empty-state" />
        <h2 className="text-2xl font-semibold mb-2">Crie sua Persona</h2>
        <p className="text-muted-foreground mb-6">
          Complete o onboarding para começar a usar o Conselho de Clones.
        </p>
        <Button asChild data-testid="button-start-onboarding">
          <Link href="/onboarding">Começar Agora</Link>
        </Button>
      </Card>
    </div>
  );
}

const RESEARCH_MODE_CONFIG = {
  quick: { icon: Zap, label: "Quick", color: "bg-yellow-500/10 text-yellow-700 dark:text-yellow-400" },
  strategic: { icon: TrendingUp, label: "Strategic", color: "bg-blue-500/10 text-blue-700 dark:text-blue-400" },
  complete: { icon: Sparkles, label: "Complete", color: "bg-purple-500/10 text-purple-700 dark:text-purple-400" },
};

export default function PersonaDashboard() {
  const [showEnrichment, setShowEnrichment] = useState(false);
  const { toast } = useToast();

  const { data: persona, isLoading, error } = useQuery<UserPersona | null>({
    queryKey: ["/api/persona/current"],
  });

  useEffect(() => {
    if (error) {
      toast({
        title: "Erro ao carregar persona",
        description: "Não foi possível carregar seus dados. Tente novamente.",
        variant: "destructive",
      });
    }
  }, [error, toast]);

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (!persona) {
    return <EmptyState />;
  }

  const researchMode = persona.researchMode || "quick";
  const ModeIcon = RESEARCH_MODE_CONFIG[researchMode as keyof typeof RESEARCH_MODE_CONFIG]?.icon || Zap;
  const modeLabel = RESEARCH_MODE_CONFIG[researchMode as keyof typeof RESEARCH_MODE_CONFIG]?.label || "Quick";
  const modeColor = RESEARCH_MODE_CONFIG[researchMode as keyof typeof RESEARCH_MODE_CONFIG]?.color || "";

  const videosCount = persona.videoInsights?.length || 0;
  const campaignsCount = persona.campaignReferences?.length || 0;
  const isEnriched = (persona.researchCompleteness || 0) > 0;

  return (
    <div className="min-h-screen py-12">
      <div className="max-w-7xl mx-auto px-6 lg:px-8 space-y-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="space-y-2"
          data-testid="section-header"
        >
          <h1 className="text-4xl font-semibold tracking-tight">Sua Persona de Marketing</h1>
          <p className="text-lg text-muted-foreground">
            {persona.companyName || persona.industry || "Seu perfil de negócio"}
          </p>
        </motion.div>

        {/* Stats Cards */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-3 gap-6"
          data-testid="section-stats"
        >
          {/* Research Mode Card */}
          <motion.div variants={cardVariants}>
            <Card className="rounded-2xl border border-border/50 hover-elevate transition-shadow" data-testid="card-research-mode">
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-2">
                  <div className={`p-2 rounded-lg ${modeColor}`}>
                    <ModeIcon className="w-5 h-5" data-testid="icon-research-mode" />
                  </div>
                  <p className="text-sm font-medium text-muted-foreground">Modo de Pesquisa</p>
                </div>
                <p className="text-2xl font-semibold" data-testid="text-mode-label">{modeLabel}</p>
              </CardContent>
            </Card>
          </motion.div>

          {/* Videos Found Card */}
          <motion.div variants={cardVariants}>
            <Card className="rounded-2xl border border-border/50 hover-elevate transition-shadow" data-testid="card-videos-count">
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 rounded-lg bg-accent/10">
                    <Video className="w-5 h-5 text-accent" data-testid="icon-videos" />
                  </div>
                  <p className="text-sm font-medium text-muted-foreground">Vídeos Encontrados</p>
                </div>
                <p className="text-2xl font-semibold" data-testid="text-videos-count">{videosCount}</p>
              </CardContent>
            </Card>
          </motion.div>

          {/* Campaigns Identified Card */}
          <motion.div variants={cardVariants}>
            <Card className="rounded-2xl border border-border/50 hover-elevate transition-shadow" data-testid="card-campaigns-count">
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 rounded-lg bg-accent/10">
                    <Lightbulb className="w-5 h-5 text-accent" data-testid="icon-campaigns" />
                  </div>
                  <p className="text-sm font-medium text-muted-foreground">Campanhas Identificadas</p>
                </div>
                <p className="text-2xl font-semibold" data-testid="text-campaigns-count">{campaignsCount}</p>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>

        {/* Business Context Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
          data-testid="section-business-context"
        >
          <Card className="rounded-2xl border border-border/50">
            <CardHeader>
              <CardTitle className="text-2xl font-medium">Contexto de Negócio</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Industry & Company Size */}
              {(persona.industry || persona.companySize) && (
                <div className="flex flex-wrap gap-2" data-testid="section-industry-size">
                  {persona.industry && (
                    <Badge variant="secondary" className="text-sm" data-testid="badge-industry">
                      <Building2 className="w-3 h-3 mr-1" />
                      {persona.industry}
                    </Badge>
                  )}
                  {persona.companySize && (
                    <Badge variant="secondary" className="text-sm" data-testid="badge-company-size">
                      <Users className="w-3 h-3 mr-1" />
                      {persona.companySize} funcionários
                    </Badge>
                  )}
                </div>
              )}

              {/* Target Audience */}
              {persona.targetAudience && (
                <div data-testid="section-target-audience">
                  <p className="text-sm font-medium text-muted-foreground mb-2">Público-Alvo</p>
                  <p className="text-lg leading-relaxed">{persona.targetAudience}</p>
                </div>
              )}

              {/* Primary Goal */}
              {persona.primaryGoal && (
                <div data-testid="section-primary-goal">
                  <p className="text-sm font-medium text-muted-foreground mb-2">Objetivo Principal</p>
                  <Badge variant="secondary" className="text-sm">
                    <Target className="w-3 h-3 mr-1" />
                    {persona.primaryGoal}
                  </Badge>
                </div>
              )}

              {/* Main Challenge */}
              {persona.mainChallenge && (
                <div data-testid="section-main-challenge">
                  <p className="text-sm font-medium text-muted-foreground mb-2">Maior Desafio</p>
                  <p className="text-base text-muted-foreground leading-relaxed">{persona.mainChallenge}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Enrichment CTA (only if not enriched) */}
        {!isEnriched && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.3 }}
            className="flex justify-center py-12"
            data-testid="section-enrichment-cta"
          >
            <Button
              size="lg"
              className="bg-accent text-accent-foreground font-medium px-8 py-4 rounded-xl"
              onClick={() => setShowEnrichment(true)}
              data-testid="button-enrich-persona"
            >
              <Sparkles className="w-5 h-5 mr-2" />
              Enriquecer Persona com YouTube Research
            </Button>
          </motion.div>
        )}

        {/* Enriched Content (only if enriched) */}
        {isEnriched && (
          <div className="space-y-12">
            {/* Key Insights Section */}
            {persona.videoInsights && persona.videoInsights.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.4 }}
                data-testid="section-key-insights"
              >
                <Card className="rounded-2xl border border-border/50">
                  <CardHeader>
                    <CardTitle className="text-2xl font-medium">Principais Insights</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-3">
                      {persona.videoInsights.slice(0, 8).map((insight, idx) => (
                        <li key={idx} className="flex items-start gap-3" data-testid={`insight-item-${idx}`}>
                          <CheckCircle2 className="w-5 h-5 text-accent mt-0.5 flex-shrink-0" />
                          <p className="leading-relaxed">{insight}</p>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {/* Top Videos Section */}
            {persona.inspirationVideos && persona.inspirationVideos.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.5 }}
                data-testid="section-videos"
              >
                <h2 className="text-2xl font-medium mb-6">Vídeos de Inspiração</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {persona.inspirationVideos.slice(0, 6).map((video: any, idx: number) => (
                    <Card 
                      key={idx} 
                      className="rounded-2xl border border-border/50 hover-elevate transition-shadow overflow-hidden"
                      data-testid={`video-card-${idx}`}
                    >
                      <div className="aspect-video bg-muted flex items-center justify-center">
                        <Video className="w-12 h-12 text-muted-foreground" />
                      </div>
                      <CardContent className="p-4 space-y-2">
                        <h3 className="font-medium line-clamp-2" data-testid={`video-title-${idx}`}>
                          {video.title || "Vídeo de Inspiração"}
                        </h3>
                        {video.channel && (
                          <p className="text-sm text-muted-foreground" data-testid={`video-channel-${idx}`}>
                            {video.channel}
                          </p>
                        )}
                        {video.views && (
                          <p className="text-xs text-muted-foreground" data-testid={`video-views-${idx}`}>
                            {video.views} visualizações
                          </p>
                        )}
                        {video.url && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="w-full mt-2"
                            asChild
                            data-testid={`button-video-link-${idx}`}
                          >
                            <a href={video.url} target="_blank" rel="noopener noreferrer">
                              Assistir
                              <ExternalLink className="w-3 h-3 ml-2" />
                            </a>
                          </Button>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Campaign References Section */}
            {persona.campaignReferences && persona.campaignReferences.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.6 }}
                data-testid="section-campaigns"
              >
                <h2 className="text-2xl font-medium mb-6">Campanhas Relevantes</h2>
                <div className="space-y-4">
                  {persona.campaignReferences.map((campaign: any, idx: number) => (
                    <Card 
                      key={idx} 
                      className="rounded-2xl border border-border/50 hover-elevate transition-shadow"
                      data-testid={`campaign-card-${idx}`}
                    >
                      <CardContent className="p-6 space-y-4">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1">
                            <h3 className="text-xl font-medium mb-2" data-testid={`campaign-name-${idx}`}>
                              {campaign.title || campaign.name || `Campanha ${idx + 1}`}
                            </h3>
                            {campaign.channel && (
                              <p className="text-sm text-muted-foreground mb-2" data-testid={`campaign-channel-${idx}`}>
                                Canal: {campaign.channel}
                              </p>
                            )}
                            <div className="flex items-center gap-4 text-sm text-muted-foreground">
                              {campaign.viewCount !== undefined && (
                                <span data-testid={`campaign-views-${idx}`}>
                                  {campaign.viewCount.toLocaleString('pt-BR')} visualizações
                                </span>
                              )}
                              {campaign.likeCount !== undefined && (
                                <span data-testid={`campaign-likes-${idx}`}>
                                  {campaign.likeCount.toLocaleString('pt-BR')} likes
                                </span>
                              )}
                              {campaign.publishedAt && (
                                <span data-testid={`campaign-date-${idx}`}>
                                  {new Date(campaign.publishedAt).toLocaleDateString('pt-BR')}
                                </span>
                              )}
                            </div>
                          </div>
                          {(campaign.url || campaign.videoUrl) && (
                            <Button
                              variant="ghost"
                              size="sm"
                              asChild
                              data-testid={`button-campaign-link-${idx}`}
                            >
                              <a href={campaign.url || campaign.videoUrl} target="_blank" rel="noopener noreferrer">
                                <ExternalLink className="w-4 h-4" />
                              </a>
                            </Button>
                          )}
                        </div>
                        {campaign.insights && campaign.insights.length > 0 && (
                          <ul className="space-y-2">
                            {campaign.insights.map((insight: string, insightIdx: number) => (
                              <li 
                                key={insightIdx} 
                                className="flex items-start gap-2 text-sm text-muted-foreground"
                                data-testid={`campaign-insight-${idx}-${insightIdx}`}
                              >
                                <span className="text-accent mt-1">•</span>
                                <span>{insight}</span>
                              </li>
                            ))}
                          </ul>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </motion.div>
            )}
          </div>
        )}
      </div>

      <EnrichmentModal
        isOpen={showEnrichment}
        onClose={() => setShowEnrichment(false)}
        personaId={persona.id}
        currentMode={persona.researchMode as "quick" | "strategic" | "complete" | undefined}
      />
    </div>
  );
}
