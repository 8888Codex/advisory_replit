import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Brain, Heart, Zap, Target, TrendingUp, Users } from "lucide-react";

interface PsychographicCoreCardProps {
  data: {
    // Old format (fallback)
    coreValues?: string[];
    deepFears?: string[];
    trueDreams?: string[];
    thinkingSystem?: string;
    decisionDrivers?: string[];
    // New format (from enrichment)
    demographics?: {
      age?: string;
      location?: string;
      education?: string;
      income?: string;
    };
    psychographics?: {
      personality?: string;
      lifestyle?: string;
      interests?: string[];
    };
    motivations?: {
      intrinsic?: string[];
      extrinsic?: string[];
    };
    fears?: string[];
    aspirations?: string[];
  } | null;
}

export function PsychographicCoreCard({ data }: PsychographicCoreCardProps) {
  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5" />
            Núcleo Psicográfico
          </CardTitle>
          <CardDescription>
            Análise psicológica profunda não disponível
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-primary" />
          Núcleo Psicográfico
        </CardTitle>
        <CardDescription>
          Sistema de valores, comportamentos e motivações profundas
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Demographics */}
        {data.demographics && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Users className="w-4 h-4 text-primary" />
              Demografia
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              {data.demographics.age && (
                <div>
                  <span className="text-muted-foreground">Idade:</span> {data.demographics.age}
                </div>
              )}
              {data.demographics.location && (
                <div>
                  <span className="text-muted-foreground">Localização:</span> {data.demographics.location}
                </div>
              )}
              {data.demographics.education && (
                <div>
                  <span className="text-muted-foreground">Educação:</span> {data.demographics.education}
                </div>
              )}
              {data.demographics.income && (
                <div>
                  <span className="text-muted-foreground">Renda:</span> {data.demographics.income}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Psychographics */}
        {data.psychographics && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Brain className="w-4 h-4 text-primary" />
              Psicográfico
            </div>
            <div className="space-y-2 text-sm">
              {data.psychographics.personality && (
                <div>
                  <span className="font-medium text-muted-foreground">Personalidade:</span>{" "}
                  {data.psychographics.personality}
                </div>
              )}
              {data.psychographics.lifestyle && (
                <div>
                  <span className="font-medium text-muted-foreground">Estilo de Vida:</span>{" "}
                  {data.psychographics.lifestyle}
                </div>
              )}
              {data.psychographics.interests && data.psychographics.interests.length > 0 && (
                <div>
                  <span className="font-medium text-muted-foreground">Interesses:</span>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {data.psychographics.interests.map((interest, idx) => (
                      <Badge key={idx} variant="secondary" className="text-xs">
                        {interest}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Motivations */}
        {data.motivations && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <TrendingUp className="w-4 h-4 text-primary" />
              Motivações
            </div>
            <div className="space-y-3">
              {data.motivations.intrinsic && data.motivations.intrinsic.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-muted-foreground mb-1">Intrínsecas:</p>
                  <ul className="list-disc list-inside space-y-1 text-sm">
                    {data.motivations.intrinsic.map((m, idx) => (
                      <li key={idx}>{m}</li>
                    ))}
                  </ul>
                </div>
              )}
              {data.motivations.extrinsic && data.motivations.extrinsic.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-muted-foreground mb-1">Extrínsecas:</p>
                  <ul className="list-disc list-inside space-y-1 text-sm">
                    {data.motivations.extrinsic.map((m, idx) => (
                      <li key={idx}>{m}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Fears */}
        {(data.fears && data.fears.length > 0) || (data.deepFears && data.deepFears.length > 0) ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Zap className="w-4 h-4 text-destructive" />
              Medos Profundos
            </div>
            <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
              {(data.fears || data.deepFears || []).map((fear, idx) => (
                <li key={idx}>{fear}</li>
              ))}
            </ul>
          </div>
        ) : null}

        {/* Aspirations */}
        {(data.aspirations && data.aspirations.length > 0) || (data.trueDreams && data.trueDreams.length > 0) ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Heart className="w-4 h-4 text-primary" />
              Aspirações Verdadeiras
            </div>
            <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
              {(data.aspirations || data.trueDreams || []).map((aspiration, idx) => (
                <li key={idx}>{aspiration}</li>
              ))}
            </ul>
          </div>
        ) : null}

        {/* Core Values (old format fallback) */}
        {data.coreValues && data.coreValues.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Target className="w-4 h-4 text-primary" />
              Valores Fundamentais
            </div>
            <div className="flex flex-wrap gap-2">
              {data.coreValues.map((value, idx) => (
                <Badge key={idx} variant="secondary">
                  {value}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Thinking System (old format fallback) */}
        {data.thinkingSystem && (
          <div className="space-y-2">
            <div className="text-sm font-semibold">Sistema de Pensamento</div>
            <p className="text-sm text-muted-foreground">{data.thinkingSystem}</p>
          </div>
        )}

        {/* Decision Drivers (old format fallback) */}
        {data.decisionDrivers && data.decisionDrivers.length > 0 && (
          <div className="space-y-2">
            <div className="text-sm font-semibold">Drivers de Decisão</div>
            <div className="flex flex-wrap gap-2">
              {data.decisionDrivers.map((driver, idx) => (
                <Badge key={idx} variant="outline">
                  {driver}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
