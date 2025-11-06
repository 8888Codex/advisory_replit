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

  const hasDeepModules = !!(persona.psychographicCore || persona.buyerJourney || persona.strategicInsights);
  const canUpgrade = enrichmentLevel !== "complete";

  return (
    <div className="min-h-screen py-12">
      <div className="max-w-7xl mx-auto px-6 lg:px-8 space-y-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="flex items-start justify-between"
          data-testid="section-header"
        >
          <div className="space-y-2">
            <h1 className="text-4xl font-semibold tracking-tight">Sua Persona de Marketing</h1>
            <p className="text-lg text-muted-foreground">
              {persona.companyName || persona.industry || "Seu perfil de negócio"}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className={`flex items-center gap-2 px-4 py-2 rounded-lg ${levelColor}`}>
              <LevelIcon className="w-5 h-5" />
              <span className="font-semibold">{levelLabel}</span>
              <Badge variant="outline" className="ml-2">{modulesCount} módulos</Badge>
            </div>
            {canUpgrade && hasDeepModules && (
              <Button
                variant="default"
                onClick={() => setShowUpgrade(true)}
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
            className="flex justify-center py-12"
            data-testid="section-enrichment-cta"
          >
            <Card className="p-12 text-center max-w-2xl rounded-2xl">
              <Sparkles className="mx-auto h-16 w-16 text-primary mb-4" />
              <h2 className="text-2xl font-semibold mb-2">Enriqueça sua Persona</h2>
              <p className="text-muted-foreground mb-6">
                Desbloqueie insights profundos com análise de YouTube, psicografia, jornada do comprador e muito mais.
              </p>
              <Button
                size="lg"
                onClick={() => setShowEnrichment(true)}
                data-testid="button-enrich-persona"
              >
                <Sparkles className="w-5 h-5 mr-2" />
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
            <Tabs defaultValue="overview" className="space-y-6">
              <TabsList className="grid w-full grid-cols-4 lg:grid-cols-9 gap-2">
                <TabsTrigger value="overview" data-testid="tab-overview">
                  <Target className="w-4 h-4 mr-2" />
                  Resumo
                </TabsTrigger>
                <TabsTrigger value="psychographic" data-testid="tab-psychographic">
                  <Brain className="w-4 h-4 mr-2" />
                  Psicográfico
                </TabsTrigger>
                <TabsTrigger value="journey" data-testid="tab-journey">
                  <Map className="w-4 h-4 mr-2" />
                  Jornada
                </TabsTrigger>
                <TabsTrigger value="behavioral" disabled={!persona.behavioralProfile} data-testid="tab-behavioral">
                  <UsersIcon className="w-4 h-4 mr-2" />
                  Comportamento
                </TabsTrigger>
                <TabsTrigger value="language" disabled={!persona.languageCommunication} data-testid="tab-language">
                  <MessageCircle className="w-4 h-4 mr-2" />
                  Linguagem
                </TabsTrigger>
                <TabsTrigger value="strategic" data-testid="tab-strategic">
                  <Lightbulb className="w-4 h-4 mr-2" />
                  Estratégico
                </TabsTrigger>
                <TabsTrigger value="jtbd" disabled={!persona.jobsToBeDone} data-testid="tab-jtbd">
                  <Briefcase className="w-4 h-4 mr-2" />
                  JTBD
                </TabsTrigger>
                <TabsTrigger value="decision" disabled={!persona.decisionProfile} data-testid="tab-decision">
                  <UserCheck className="w-4 h-4 mr-2" />
                  Decisão
                </TabsTrigger>
                <TabsTrigger value="copy" disabled={!persona.copyExamples} data-testid="tab-copy">
                  <FileText className="w-4 h-4 mr-2" />
                  Copy
                </TabsTrigger>
              </TabsList>

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
                          <p className="font-medium">{persona.targetAudience}</p>
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
