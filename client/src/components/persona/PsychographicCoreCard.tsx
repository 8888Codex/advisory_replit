import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Brain, Heart, Zap, Target } from "lucide-react";

interface PsychographicCoreCardProps {
  data: {
    coreValues?: string[];
    deepFears?: string[];
    trueDreams?: string[];
    thinkingSystem?: string;
    decisionDrivers?: string[];
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
          Sistema de valores, medos e aspirações
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
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

        {data.deepFears && data.deepFears.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Zap className="w-4 h-4 text-destructive" />
              Medos Profundos
            </div>
            <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
              {data.deepFears.map((fear, idx) => (
                <li key={idx}>{fear}</li>
              ))}
            </ul>
          </div>
        )}

        {data.trueDreams && data.trueDreams.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Heart className="w-4 h-4 text-primary" />
              Aspirações Verdadeiras
            </div>
            <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
              {data.trueDreams.map((dream, idx) => (
                <li key={idx}>{dream}</li>
              ))}
            </ul>
          </div>
        )}

        {data.thinkingSystem && (
          <div className="space-y-2">
            <div className="text-sm font-semibold">Sistema de Pensamento</div>
            <p className="text-sm text-muted-foreground">{data.thinkingSystem}</p>
          </div>
        )}

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
