import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Users, MessageSquare, TrendingUp, Radio } from "lucide-react";

// Helper function to render nested objects
function renderNestedObject(obj: any, depth: number = 0): JSX.Element {
  if (!obj) return <></>;
  
  if (Array.isArray(obj)) {
    return (
      <ul className="space-y-1 text-sm">
        {obj.map((item, idx) => (
          <li key={idx} className="p-2 bg-muted/30 rounded-md">
            {typeof item === 'object' ? renderNestedObject(item, depth + 1) : String(item)}
          </li>
        ))}
      </ul>
    );
  }
  
  if (typeof obj === 'object') {
    return (
      <div className={`space-y-2 ${depth > 0 ? 'pl-4 border-l-2 border-muted' : ''}`}>
        {Object.entries(obj).map(([key, value]) => (
          <div key={key}>
            <p className="text-xs font-medium text-muted-foreground mb-1 capitalize">
              {key.replace(/([A-Z])/g, ' $1').trim()}:
            </p>
            {Array.isArray(value) ? (
              <div className="flex flex-wrap gap-1.5">
                {value.map((item, idx) => (
                  <Badge key={idx} variant="outline" className="text-xs">
                    {String(item)}
                  </Badge>
                ))}
              </div>
            ) : typeof value === 'object' && value !== null ? (
              renderNestedObject(value, depth + 1)
            ) : (
              <p className="text-sm">{String(value)}</p>
            )}
          </div>
        ))}
      </div>
    );
  }
  
  return <p className="text-sm">{String(obj)}</p>;
}

interface BehavioralProfileCardProps {
  data: {
    // New format (from enrichment)
    onlineBehavior?: any;
    purchaseBehavior?: any;
    decisionMaking?: any;
    engagement?: any;
    // Old format (fallback)
    cialdiniPrinciples?: Array<string | { principle: string; priority?: string }>;
    preferredChannels?: Array<string | { channel: string; usage?: string }>;
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
        {/* New format - render all nested objects */}
        {data.onlineBehavior && (
          <div className="space-y-2">
            <div className="text-sm font-semibold text-blue-500">Online Behavior</div>
            {renderNestedObject(data.onlineBehavior)}
          </div>
        )}

        {data.purchaseBehavior && (
          <div className="space-y-2">
            <div className="text-sm font-semibold text-green-500">Purchase Behavior</div>
            {renderNestedObject(data.purchaseBehavior)}
          </div>
        )}

        {data.decisionMaking && (
          <div className="space-y-2">
            <div className="text-sm font-semibold text-purple-500">Decision Making</div>
            {renderNestedObject(data.decisionMaking)}
          </div>
        )}

        {data.engagement && (
          <div className="space-y-2">
            <div className="text-sm font-semibold text-orange-500">Engagement</div>
            {renderNestedObject(data.engagement)}
          </div>
        )}

        {/* Old format (fallback) */}
        {data.cialdiniPrinciples && data.cialdiniPrinciples.length > 0 && (
          <div className="space-y-2">
            <div className="text-sm font-semibold">Princípios de Cialdini Ativos</div>
            <div className="flex flex-wrap gap-2">
              {data.cialdiniPrinciples.map((item, idx) => {
                const text = typeof item === 'string' ? item : item.principle;
                const priority = typeof item === 'object' && item.priority ? ` (${item.priority})` : '';
                return (
                  <Badge key={idx} variant="default">
                    {text}{priority}
                  </Badge>
                );
              })}
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
              {data.preferredChannels.map((item, idx) => {
                const text = typeof item === 'string' ? item : item.channel;
                const usage = typeof item === 'object' && item.usage ? ` (${item.usage})` : '';
                return (
                  <Badge key={idx} variant="secondary">
                    {text}{usage}
                  </Badge>
                );
              })}
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
