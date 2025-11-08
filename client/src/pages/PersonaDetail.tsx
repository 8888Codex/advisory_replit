import { useQuery } from "@tanstack/react-query";
import { useRoute, Link } from "wouter";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, ArrowLeft, Building2, Target, TrendingUp, Lightbulb } from "lucide-react";

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

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-2">
            <Building2 className="w-5 h-5 text-muted-foreground" />
            <h3 className="font-semibold">Empresa</h3>
          </div>
          <p className="text-sm text-muted-foreground mb-1">Tamanho</p>
          <p className="font-medium">{persona.companySize} funcionários</p>
        </Card>

        <Card className="p-6">
          <div className="flex items-center gap-3 mb-2">
            <Target className="w-5 h-5 text-muted-foreground" />
            <h3 className="font-semibold">Público-Alvo</h3>
          </div>
          <p className="text-sm">{persona.targetAudience}</p>
        </Card>

        <Card className="p-6">
          <div className="flex items-center gap-3 mb-2">
            <TrendingUp className="w-5 h-5 text-muted-foreground" />
            <h3 className="font-semibold">Objetivo Principal</h3>
          </div>
          <p className="text-sm">{persona.primaryGoal}</p>
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
          {persona.psychographicCore && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lightbulb className="w-5 h-5" />
                  Core Psicográfico
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {persona.psychographicCore.values && (
                  <div>
                    <h4 className="font-semibold mb-2 text-sm text-muted-foreground">Valores</h4>
                    <div className="flex flex-wrap gap-2">
                      {persona.psychographicCore.values.map((value: string, idx: number) => (
                        <Badge key={idx} variant="secondary">
                          {value}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                {persona.psychographicCore.motivations && (
                  <div>
                    <h4 className="font-semibold mb-2 text-sm text-muted-foreground">Motivações</h4>
                    <p className="text-sm">{persona.psychographicCore.motivations}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {persona.jobsToBeDone && (
            <Card>
              <CardHeader>
                <CardTitle>Jobs to Be Done</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Array.isArray(persona.jobsToBeDone) ? (
                    persona.jobsToBeDone.map((job: any, idx: number) => (
                      <div key={idx} className="p-4 bg-muted rounded-lg">
                        <h4 className="font-semibold mb-1">{job.job || job}</h4>
                        {job.context && (
                          <p className="text-sm text-muted-foreground">{job.context}</p>
                        )}
                      </div>
                    ))
                  ) : (
                    <p className="text-sm">{JSON.stringify(persona.jobsToBeDone)}</p>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {persona.behavioralProfile && (
            <Card>
              <CardHeader>
                <CardTitle>Perfil Comportamental</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4 text-sm">
                  {Object.entries(persona.behavioralProfile).map(([key, value]) => (
                    <div key={key}>
                      <h4 className="font-semibold mb-1 capitalize">
                        {key.replace(/([A-Z])/g, " $1").trim()}
                      </h4>
                      <p className="text-muted-foreground">
                        {Array.isArray(value) ? value.join(", ") : String(value)}
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {persona.buyerJourney && (
            <Card>
              <CardHeader>
                <CardTitle>Jornada do Comprador</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(persona.buyerJourney).map(([stage, details]) => (
                    <div key={stage} className="p-4 bg-muted rounded-lg">
                      <h4 className="font-semibold mb-2 capitalize">{stage}</h4>
                      <p className="text-sm text-muted-foreground">{String(details)}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {persona.strategicInsights && (
            <Card>
              <CardHeader>
                <CardTitle>Insights Estratégicos</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="prose prose-sm max-w-none">
                  {typeof persona.strategicInsights === "string" ? (
                    <p>{persona.strategicInsights}</p>
                  ) : (
                    <div className="space-y-4">
                      {Object.entries(persona.strategicInsights).map(([key, value]) => (
                        <div key={key}>
                          <h4 className="font-semibold capitalize">
                            {key.replace(/([A-Z])/g, " $1").trim()}
                          </h4>
                          <p className="text-muted-foreground">{String(value)}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
