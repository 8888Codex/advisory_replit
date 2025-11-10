import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Lightbulb, Target, Radio, Award, AlertTriangle, Zap, TrendingUp, CheckCircle } from "lucide-react";

interface StrategicInsightsCardProps {
  data: {
    // New format (from enrichment)
    opportunities?: string[];
    threats?: string[];
    recommendations?: string[];
    quickWins?: string[];
    longTermStrategy?: string[];
    // Old format (fallback)
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
        {/* New format - Strategic sections */}
        {data.threats && data.threats.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold text-red-600 dark:text-red-400">
              <AlertTriangle className="w-4 h-4" />
              Threats (Ameaças)
            </div>
            <ul className="space-y-1.5">
              {data.threats.map((threat, idx) => (
                <li key={idx} className="text-sm p-2.5 bg-red-500/5 rounded-md border-l-2 border-red-500">
                  {threat}
                </li>
              ))}
            </ul>
          </div>
        )}

        {data.quickWins && data.quickWins.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold text-orange-600 dark:text-orange-400">
              <Zap className="w-4 h-4" />
              Quick Wins (Vitórias Rápidas)
            </div>
            <ul className="space-y-1.5">
              {data.quickWins.map((win, idx) => (
                <li key={idx} className="text-sm p-2.5 bg-orange-500/5 rounded-md border-l-2 border-orange-500">
                  {win}
                </li>
              ))}
            </ul>
          </div>
        )}

        {data.opportunities && data.opportunities.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold text-green-600 dark:text-green-400">
              <TrendingUp className="w-4 h-4" />
              Opportunities (Oportunidades)
            </div>
            <ul className="space-y-1.5">
              {data.opportunities.map((opp, idx) => (
                <li key={idx} className="text-sm p-2.5 bg-green-500/5 rounded-md border-l-2 border-green-500">
                  {opp}
                </li>
              ))}
            </ul>
          </div>
        )}

        {data.recommendations && data.recommendations.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold text-blue-600 dark:text-blue-400">
              <CheckCircle className="w-4 h-4" />
              Recommendations (Recomendações)
            </div>
            <ul className="space-y-1.5">
              {data.recommendations.map((rec, idx) => (
                <li key={idx} className="text-sm p-2.5 bg-blue-500/5 rounded-md border-l-2 border-blue-500">
                  {rec}
                </li>
              ))}
            </ul>
          </div>
        )}

        {data.longTermStrategy && data.longTermStrategy.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold text-purple-600 dark:text-purple-400">
              <Target className="w-4 h-4" />
              Long Term Strategy (Estratégia de Longo Prazo)
            </div>
            <ul className="space-y-1.5">
              {data.longTermStrategy.map((strategy, idx) => (
                <li key={idx} className="text-sm p-2.5 bg-purple-500/5 rounded-md border-l-2 border-purple-500">
                  {strategy}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Old format (fallback) */}
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
