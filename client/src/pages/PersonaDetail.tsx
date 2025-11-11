import { useQuery } from "@tanstack/react-query";
import { useRoute, Link } from "wouter";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, ArrowLeft, Building2, Target, TrendingUp, Lightbulb } from "lucide-react";
import { RedditInsightsCard } from "@/components/persona/RedditInsightsCard";
import { JobsToBeDoneCard } from "@/components/persona/JobsToBeDoneCard";
import { BehavioralProfileCard } from "@/components/persona/BehavioralProfileCard";
import { BuyerJourneyCard } from "@/components/persona/BuyerJourneyCard";
import { StrategicInsightsCard } from "@/components/persona/StrategicInsightsCard";
import { PsychographicCoreCard } from "@/components/persona/PsychographicCoreCard";
import { extractPersonaSummary } from "@/lib/textUtils";

interface UserPersona {
  id: string;
  userId: string;
  companyName: string;
  industry: string;
  companySize: string;
  targetAudience: string;
  primaryGoal: string;
  mainChallenge: string;
  enrichmentLevel: "quick" | "strategic" | "complete";
  enrichmentStatus: "pending" | "processing" | "completed" | "failed";
  researchCompleteness: number;
  psychographicCore: any;
  jobsToBeDone: any;
  decisionProfile: any;
  behavioralProfile: any;
  buyerJourney: any;
  strategicInsights: any;
  redditInsights: any;
  createdAt: string;
  lastEnrichedAt: string | null;
}

export default function PersonaDetail() {
  const [, params] = useRoute("/personas/:id");
  const personaId = params?.id;

  const { data: persona, isLoading } = useQuery<UserPersona>({
    queryKey: [`/api/persona/${personaId}`],
    enabled: !!personaId,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!persona) {
    return (
      <div className="container max-w-4xl mx-auto p-6">
        <Card className="p-12">
          <div className="flex flex-col items-center justify-center text-center space-y-4">
            <Building2 className="w-12 h-12 text-muted-foreground" />
            <div className="space-y-2">
              <h3 className="text-xl font-semibold">Persona não encontrada</h3>
              <p className="text-muted-foreground">
                A persona que você está procurando não existe ou foi removida
              </p>
            </div>
            <Link href="/personas">
              <Button>Voltar para Personas</Button>
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  const isEnriched = persona.enrichmentStatus === "completed";

  return (
    <div className="container max-w-6xl mx-auto p-6 space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/personas">
          <Button variant="outline" size="icon" data-testid="button-back">
            <ArrowLeft className="w-4 h-4" />
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="text-3xl font-bold tracking-tight">{persona.companyName}</h1>
          <p className="text-muted-foreground mt-1">{persona.industry}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <Card className="p-6 hover:shadow-lg transition-shadow">
          <div className="flex items-center gap-3 mb-2">
            <Building2 className="w-5 h-5 text-muted-foreground" />
            <h3 className="font-semibold">Empresa</h3>
          </div>
          <p className="text-sm text-muted-foreground mb-1">Tamanho</p>
          <p className="font-medium leading-relaxed">{persona.companySize} funcionários</p>
        </Card>

        <Card className="p-6 hover:shadow-lg transition-shadow">
          <div className="flex items-center gap-3 mb-2">
            <Target className="w-5 h-5 text-muted-foreground" />
            <h3 className="font-semibold">Público-Alvo</h3>
          </div>
          <p className="text-sm line-clamp-4 leading-relaxed">
            {extractPersonaSummary(persona.targetAudience, 200)}
          </p>
        </Card>

        <Card className="p-6 hover:shadow-lg transition-shadow">
          <div className="flex items-center gap-3 mb-2">
            <TrendingUp className="w-5 h-5 text-muted-foreground" />
            <h3 className="font-semibold">Objetivo Principal</h3>
          </div>
          <p className="text-sm leading-relaxed">{persona.primaryGoal}</p>
        </Card>
      </div>

      {!isEnriched ? (
        <Card className="p-12">
          <div className="flex flex-col items-center justify-center text-center space-y-4">
            <Loader2 className="w-12 h-12 animate-spin text-primary" />
            <div className="space-y-2">
              <h3 className="text-xl font-semibold">
                {persona.enrichmentStatus === "processing"
                  ? "Enriquecimento em andamento"
                  : "Aguardando enriquecimento"}
              </h3>
              <p className="text-muted-foreground max-w-md">
                {persona.enrichmentStatus === "processing"
                  ? "Estamos analisando dados de YouTube, Reddit e outras fontes para criar insights profundos sobre sua persona"
                  : "Esta persona ainda não foi enriquecida. O processo de enriquecimento começará em breve"}
              </p>
              {persona.researchCompleteness > 0 && (
                <div className="mt-4">
                  <Badge variant="secondary">
                    {persona.researchCompleteness}% completo
                  </Badge>
                </div>
              )}
            </div>
          </div>
        </Card>
      ) : (
        <div className="space-y-6">
          <PsychographicCoreCard data={persona.psychographicCore} />

          <JobsToBeDoneCard data={persona.jobsToBeDone} />

          <BehavioralProfileCard data={persona.behavioralProfile} />

          <BuyerJourneyCard data={persona.buyerJourney} />

          <StrategicInsightsCard data={persona.strategicInsights} />

          {persona.redditInsights && (
            <RedditInsightsCard data={persona.redditInsights} />
          )}
        </div>
      )}
    </div>
  );
}
