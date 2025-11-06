import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Lightbulb, Target, Radio, Award } from "lucide-react";

interface StrategicInsightsCardProps {
  data: {
    coreMessage?: string;
    uniqueValueProposition?: string;
    channelStrategy?: string[];
    competitivePosition?: string;
  } | null;
}

export function StrategicInsightsCard({ data }: StrategicInsightsCardProps) {
  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="w-5 h-5" />
            Insights Estratégicos
          </CardTitle>
          <CardDescription>
            Análise estratégica não disponível
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Lightbulb className="w-5 h-5 text-primary" />
          Insights Estratégicos
        </CardTitle>
        <CardDescription>
          Mensagem central e posicionamento competitivo
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {data.coreMessage && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Target className="w-4 h-4 text-primary" />
              Mensagem Central
            </div>
            <p className="text-sm p-4 bg-muted rounded-md border-l-4 border-primary">
              {data.coreMessage}
            </p>
          </div>
        )}

        {data.uniqueValueProposition && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Award className="w-4 h-4 text-primary" />
              Proposta de Valor Única
            </div>
            <p className="text-sm p-4 bg-muted rounded-md">
              {data.uniqueValueProposition}
            </p>
          </div>
        )}

        {data.channelStrategy && data.channelStrategy.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Radio className="w-4 h-4 text-primary" />
              Estratégia de Canais
            </div>
            <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
              {data.channelStrategy.map((strategy, idx) => (
                <li key={idx}>{strategy}</li>
              ))}
            </ul>
          </div>
        )}

        {data.competitivePosition && (
          <div className="space-y-2">
            <div className="text-sm font-semibold">Posicionamento Competitivo</div>
            <Badge variant="secondary" className="text-sm">
              {data.competitivePosition}
            </Badge>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
