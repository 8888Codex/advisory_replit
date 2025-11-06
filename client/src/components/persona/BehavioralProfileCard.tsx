import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Users, MessageSquare, TrendingUp, Radio } from "lucide-react";

interface BehavioralProfileCardProps {
  data: {
    cialdiniPrinciples?: string[];
    preferredChannels?: string[];
    influencerTypes?: string[];
    contentFormat?: string;
    engagementPatterns?: {
      bestTime?: string;
      frequency?: string;
    };
  } | null;
}

export function BehavioralProfileCard({ data }: BehavioralProfileCardProps) {
  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            Perfil Comportamental
          </CardTitle>
          <CardDescription>
            Análise comportamental não disponível
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Users className="w-5 h-5 text-primary" />
          Perfil Comportamental
        </CardTitle>
        <CardDescription>
          Princípios de persuasão e padrões de engajamento
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {data.cialdiniPrinciples && data.cialdiniPrinciples.length > 0 && (
          <div className="space-y-2">
            <div className="text-sm font-semibold">Princípios de Cialdini Ativos</div>
            <div className="flex flex-wrap gap-2">
              {data.cialdiniPrinciples.map((principle, idx) => (
                <Badge key={idx} variant="default">
                  {principle}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {data.preferredChannels && data.preferredChannels.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Radio className="w-4 h-4 text-primary" />
              Canais Preferidos
            </div>
            <div className="flex flex-wrap gap-2">
              {data.preferredChannels.map((channel, idx) => (
                <Badge key={idx} variant="secondary">
                  {channel}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {data.influencerTypes && data.influencerTypes.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <TrendingUp className="w-4 h-4 text-primary" />
              Tipos de Influenciadores
            </div>
            <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
              {data.influencerTypes.map((type, idx) => (
                <li key={idx}>{type}</li>
              ))}
            </ul>
          </div>
        )}

        {data.contentFormat && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <MessageSquare className="w-4 h-4 text-primary" />
              Formato de Conteúdo Preferido
            </div>
            <p className="text-sm text-muted-foreground">{data.contentFormat}</p>
          </div>
        )}

        {data.engagementPatterns && (
          <div className="space-y-2">
            <div className="text-sm font-semibold">Padrões de Engajamento</div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              {data.engagementPatterns.bestTime && (
                <div>
                  <div className="text-muted-foreground">Melhor Horário</div>
                  <div className="font-medium">{data.engagementPatterns.bestTime}</div>
                </div>
              )}
              {data.engagementPatterns.frequency && (
                <div>
                  <div className="text-muted-foreground">Frequência</div>
                  <div className="font-medium">{data.engagementPatterns.frequency}</div>
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
