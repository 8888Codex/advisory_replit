import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "wouter";
import { 
  Building2, 
  Zap, 
  TrendingUp, 
  Sparkles, 
  Target, 
  Brain,
  Map,
  Users as UsersIcon,
  MessageCircle,
  Lightbulb,
  Briefcase,
  UserCheck,
  FileText
} from "lucide-react";
import { motion } from "framer-motion";
import type { UserPersona } from "@shared/schema";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { extractPersonaSummary } from "@/lib/textUtils";
import { useToast } from "@/hooks/use-toast";
import EnrichmentModal from "@/components/EnrichmentModal";
import UpgradePersonaDialog from "@/components/UpgradePersonaDialog";
import { PsychographicCoreCard } from "@/components/persona/PsychographicCoreCard";
import { BuyerJourneyCard } from "@/components/persona/BuyerJourneyCard";
import { BehavioralProfileCard } from "@/components/persona/BehavioralProfileCard";
import { LanguageCommunicationCard } from "@/components/persona/LanguageCommunicationCard";
import { StrategicInsightsCard } from "@/components/persona/StrategicInsightsCard";
import { JobsToBeDoneCard } from "@/components/persona/JobsToBeDoneCard";
import { DecisionProfileCard } from "@/components/persona/DecisionProfileCard";
import { CopyExamplesCard } from "@/components/persona/CopyExamplesCard";

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
    <div className="min-h-screen py-8 sm:py-10 md:py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8 sm:space-y-12">
        <div className="space-y-3 sm:space-y-4">
          <Skeleton className="h-10 sm:h-12 w-64 sm:w-96" />
          <Skeleton className="h-5 sm:h-6 w-48 sm:w-64" />
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4 md:gap-6">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-28 sm:h-32 rounded-2xl" />
          ))}
        </div>
        
        <Skeleton className="h-48 sm:h-56 md:h-64 rounded-2xl" />
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4 sm:p-6">
      <Card className="p-6 sm:p-8 md:p-12 text-center max-w-lg rounded-2xl" data-testid="card-empty-state">
        <Building2 className="mx-auto h-12 w-12 sm:h-14 sm:w-14 md:h-16 md:w-16 text-muted-foreground mb-3 sm:mb-4" data-testid="icon-empty-state" />
        <h2 className="text-xl sm:text-2xl font-semibold mb-2">Crie sua Persona</h2>
        <p className="text-sm sm:text-base text-muted-foreground mb-4 sm:mb-6">
          Complete o onboarding para começar a usar o Conselho de Clones.
        </p>
        <Button asChild className="h-12 sm:h-auto w-full sm:w-auto" data-testid="button-start-onboarding">
          <Link href="/onboarding">Começar Agora</Link>
        </Button>
      </Card>
    </div>
  );
}

const ENRICHMENT_LEVEL_CONFIG = {
  quick: { icon: Zap, label: "Quick", color: "bg-yellow-500/10 text-yellow-700 dark:text-yellow-400", modules: 3 },
  strategic: { icon: TrendingUp, label: "Strategic", color: "bg-blue-500/10 text-blue-700 dark:text-blue-400", modules: 6 },
  complete: { icon: Sparkles, label: "Complete", color: "bg-purple-500/10 text-purple-700 dark:text-purple-400", modules: 8 },
};

export default function PersonaDashboard() {
  const [showEnrichment, setShowEnrichment] = useState(false);
  const [showUpgrade, setShowUpgrade] = useState(false);
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

  const enrichmentLevel = (persona.enrichmentLevel || "quick") as keyof typeof ENRICHMENT_LEVEL_CONFIG;
  const LevelIcon = ENRICHMENT_LEVEL_CONFIG[enrichmentLevel]?.icon || Zap;
  const levelLabel = ENRICHMENT_LEVEL_CONFIG[enrichmentLevel]?.label || "Quick";
  const levelColor = ENRICHMENT_LEVEL_CONFIG[enrichmentLevel]?.color || "";
  const modulesCount = ENRICHMENT_LEVEL_CONFIG[enrichmentLevel]?.modules || 0;

  const hasDeepModules = !!(
    persona.psychographicCore ||
    persona.buyerJourney ||
    persona.behavioralProfile ||
    persona.languageCommunication ||
    persona.strategicInsights ||
    persona.jobsToBeDone ||
    persona.decisionProfile ||
    persona.copyExamples
  );
  const canUpgrade = enrichmentLevel !== "complete";

  return (
    <div className="min-h-screen py-8 sm:py-10 md:py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8 sm:space-y-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="flex flex-col sm:flex-row items-start justify-between gap-4"
          data-testid="section-header"
        >
          <div className="space-y-1 sm:space-y-2 flex-1 min-w-0">
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-semibold tracking-tight">Sua Persona de Marketing</h1>
            <p className="text-sm sm:text-base md:text-lg text-muted-foreground truncate">
              {persona.companyName || persona.industry || "Seu perfil de negócio"}
            </p>
          </div>
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-3 w-full sm:w-auto">
            <div className={`flex items-center gap-2 px-3 sm:px-4 py-2 rounded-lg ${levelColor} w-full sm:w-auto justify-center sm:justify-start`}>
              <LevelIcon className="w-4 h-4 sm:w-5 sm:h-5 flex-shrink-0" />
              <span className="font-semibold text-sm sm:text-base">{levelLabel}</span>
              <Badge variant="outline" className="ml-2 text-xs px-2 py-0.5">{modulesCount} módulos</Badge>
            </div>
            {canUpgrade && hasDeepModules && (
              <Button
                variant="default"
                onClick={() => setShowUpgrade(true)}
                className="w-full sm:w-auto h-10 sm:h-auto"
                data-testid="button-upgrade-persona"
              >
                <Sparkles className="w-4 h-4 mr-2" />
                Upgrade Persona
              </Button>
            )}
          </div>
        </motion.div>

        {/* Enrichment CTA (only if no deep modules) */}
        {!hasDeepModules && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.2 }}
            className="flex justify-center py-8 sm:py-12"
            data-testid="section-enrichment-cta"
          >
            <Card className="p-6 sm:p-8 md:p-12 text-center max-w-2xl rounded-2xl">
              <Sparkles className="mx-auto h-12 w-12 sm:h-14 sm:w-14 md:h-16 md:w-16 text-primary mb-3 sm:mb-4" />
              <h2 className="text-xl sm:text-2xl font-semibold mb-2">Enriqueça sua Persona</h2>
              <p className="text-sm sm:text-base text-muted-foreground mb-4 sm:mb-6">
                Desbloqueie insights profundos com análise de YouTube, psicografia, jornada do comprador e muito mais.
              </p>
              <Button
                size="lg"
                onClick={() => setShowEnrichment(true)}
                className="h-12 sm:h-auto w-full sm:w-auto"
                data-testid="button-enrich-persona"
              >
                <Sparkles className="w-4 h-4 sm:w-5 sm:h-5 mr-2" />
                Começar Enriquecimento
              </Button>
            </Card>
          </motion.div>
        )}

        {/* Deep Modules Tabs */}
        {hasDeepModules && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.2 }}
            data-testid="section-deep-modules"
          >
            <Tabs defaultValue="overview" className="space-y-4 sm:space-y-6">
              <div className="overflow-x-auto scrollbar-hide -mx-4 px-4 sm:mx-0 sm:px-0">
                <TabsList className="inline-flex w-max min-w-full sm:grid sm:w-full sm:grid-cols-4 lg:grid-cols-9 gap-1 sm:gap-2">
                  <TabsTrigger value="overview" data-testid="tab-overview" className="text-xs sm:text-sm whitespace-nowrap">
                    <Target className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" />
                    Resumo
                  </TabsTrigger>
                  <TabsTrigger value="psychographic" data-testid="tab-psychographic" className="text-xs sm:text-sm whitespace-nowrap">
                    <Brain className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" />
                    Psicográfico
                  </TabsTrigger>
                  <TabsTrigger value="journey" data-testid="tab-journey" className="text-xs sm:text-sm whitespace-nowrap">
                    <Map className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" />
                    Jornada
                  </TabsTrigger>
                  <TabsTrigger value="behavioral" disabled={!persona.behavioralProfile} data-testid="tab-behavioral" className="text-xs sm:text-sm whitespace-nowrap">
                    <UsersIcon className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" />
                    Comportamento
                  </TabsTrigger>
                  <TabsTrigger value="language" disabled={!persona.languageCommunication} data-testid="tab-language" className="text-xs sm:text-sm whitespace-nowrap">
                    <MessageCircle className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" />
                    Linguagem
                  </TabsTrigger>
                  <TabsTrigger value="strategic" data-testid="tab-strategic" className="text-xs sm:text-sm whitespace-nowrap">
                    <Lightbulb className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" />
                    Estratégico
                  </TabsTrigger>
                  <TabsTrigger value="jtbd" disabled={!persona.jobsToBeDone} data-testid="tab-jtbd" className="text-xs sm:text-sm whitespace-nowrap">
                    <Briefcase className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" />
                    JTBD
                  </TabsTrigger>
                  <TabsTrigger value="decision" disabled={!persona.decisionProfile} data-testid="tab-decision" className="text-xs sm:text-sm whitespace-nowrap">
                    <UserCheck className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" />
                    Decisão
                  </TabsTrigger>
                  <TabsTrigger value="copy" disabled={!persona.copyExamples} data-testid="tab-copy" className="text-xs sm:text-sm whitespace-nowrap">
                    <FileText className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-2" />
                    Copy
                  </TabsTrigger>
                </TabsList>
              </div>

              <TabsContent value="overview" className="space-y-6">
                <Card className="rounded-2xl">
                  <CardHeader>
                    <CardTitle>Resumo da Persona</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {persona.industry && (
                        <div>
                          <p className="text-sm text-muted-foreground mb-1">Indústria</p>
                          <p className="font-medium">{persona.industry}</p>
                        </div>
                      )}
                      {persona.companySize && (
                        <div>
                          <p className="text-sm text-muted-foreground mb-1">Tamanho</p>
                          <p className="font-medium">{persona.companySize} funcionários</p>
                        </div>
                      )}
                      {persona.targetAudience && (
                        <div>
                          <p className="text-sm text-muted-foreground mb-1">Público-Alvo</p>
                          <p className="font-medium line-clamp-3">
                            {extractPersonaSummary(persona.targetAudience, 180)}
                          </p>
                        </div>
                      )}
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {persona.primaryGoal && (
                        <div>
                          <p className="text-sm text-muted-foreground mb-1">Objetivo Principal</p>
                          <Badge variant="secondary">{persona.primaryGoal}</Badge>
                        </div>
                      )}
                      {persona.mainChallenge && (
                        <div>
                          <p className="text-sm text-muted-foreground mb-1">Maior Desafio</p>
                          <p className="text-sm">{persona.mainChallenge}</p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="psychographic">
                <PsychographicCoreCard data={persona.psychographicCore} />
              </TabsContent>

              <TabsContent value="journey">
                <BuyerJourneyCard data={persona.buyerJourney} />
              </TabsContent>

              <TabsContent value="behavioral">
                <BehavioralProfileCard data={persona.behavioralProfile} />
              </TabsContent>

              <TabsContent value="language">
                <LanguageCommunicationCard data={persona.languageCommunication} />
              </TabsContent>

              <TabsContent value="strategic">
                <StrategicInsightsCard data={persona.strategicInsights} />
              </TabsContent>

              <TabsContent value="jtbd">
                <JobsToBeDoneCard data={persona.jobsToBeDone} />
              </TabsContent>

              <TabsContent value="decision">
                <DecisionProfileCard data={persona.decisionProfile} />
              </TabsContent>

              <TabsContent value="copy">
                <CopyExamplesCard data={persona.copyExamples} />
              </TabsContent>
            </Tabs>
          </motion.div>
        )}
      </div>

      <EnrichmentModal
        isOpen={showEnrichment}
        onClose={() => setShowEnrichment(false)}
        personaId={persona.id}
        currentMode={persona.researchMode as "quick" | "strategic" | "complete" | undefined}
      />

      <UpgradePersonaDialog
        isOpen={showUpgrade}
        onClose={() => setShowUpgrade(false)}
        personaId={persona.id}
        currentLevel={enrichmentLevel}
      />
    </div>
  );
}
