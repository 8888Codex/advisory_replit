import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Map, AlertCircle, Shield, Repeat, Eye, ThumbsUp, CheckCircle, RefreshCw, Heart } from "lucide-react";

// Helper function to render nested objects
function renderNestedObject(obj: any): JSX.Element {
  if (!obj) return <></>;
  
  if (Array.isArray(obj)) {
    return (
      <ul className="space-y-1 text-sm">
        {obj.map((item, idx) => (
          <li key={idx} className="p-2 bg-muted/30 rounded-md">
            {typeof item === 'object' ? renderNestedObject(item) : String(item)}
          </li>
        ))}
      </ul>
    );
  }
  
  if (typeof obj === 'object') {
    return (
      <div className="space-y-2 pl-3">
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
              renderNestedObject(value)
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

interface BuyerJourneyCardProps {
  data: {
    // New format (from enrichment)
    awareness?: any;
    consideration?: any;
    decision?: any;
    retention?: any;
    advocacy?: any;
    // Old format (fallback)
    awarenessLevel?: string;
    primaryTriggers?: string[];
    mainObjections?: string[];
    buyingCycle?: string;
    touchpointsNeeded?: number;
  } | null;
}

export function BuyerJourneyCard({ data }: BuyerJourneyCardProps) {
  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Map className="w-5 h-5" />
            Jornada do Comprador
          </CardTitle>
          <CardDescription>
            Análise da jornada não disponível
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Map className="w-5 h-5 text-primary" />
          Jornada do Comprador
        </CardTitle>
        <CardDescription>
          Níveis de consciência e ciclo de compra
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* New format - Journey stages */}
        {data.awareness && (
          <div className="space-y-2 p-4 bg-blue-500/5 rounded-lg border-l-4 border-blue-500">
            <div className="flex items-center gap-2 text-sm font-semibold text-blue-600 dark:text-blue-400">
              <Eye className="w-4 h-4" />
              Awareness (Consciência)
            </div>
            {renderNestedObject(data.awareness)}
          </div>
        )}

        {data.consideration && (
          <div className="space-y-2 p-4 bg-yellow-500/5 rounded-lg border-l-4 border-yellow-500">
            <div className="flex items-center gap-2 text-sm font-semibold text-yellow-600 dark:text-yellow-400">
              <ThumbsUp className="w-4 h-4" />
              Consideration (Consideração)
            </div>
            {renderNestedObject(data.consideration)}
          </div>
        )}

        {data.decision && (
          <div className="space-y-2 p-4 bg-green-500/5 rounded-lg border-l-4 border-green-500">
            <div className="flex items-center gap-2 text-sm font-semibold text-green-600 dark:text-green-400">
              <CheckCircle className="w-4 h-4" />
              Decision (Decisão)
            </div>
            {renderNestedObject(data.decision)}
          </div>
        )}

        {data.retention && (
          <div className="space-y-2 p-4 bg-purple-500/5 rounded-lg border-l-4 border-purple-500">
            <div className="flex items-center gap-2 text-sm font-semibold text-purple-600 dark:text-purple-400">
              <RefreshCw className="w-4 h-4" />
              Retention (Retenção)
            </div>
            {renderNestedObject(data.retention)}
          </div>
        )}

        {data.advocacy && (
          <div className="space-y-2 p-4 bg-rose-500/5 rounded-lg border-l-4 border-rose-500">
            <div className="flex items-center gap-2 text-sm font-semibold text-rose-600 dark:text-rose-400">
              <Heart className="w-4 h-4" />
              Advocacy (Advocacia)
            </div>
            {renderNestedObject(data.advocacy)}
          </div>
        )}

        {/* Old format (fallback) */}
        {data.awarenessLevel && (
          <div className="space-y-2">
            <div className="text-sm font-semibold">Nível de Consciência</div>
            <Badge variant="default" className="text-base">
              {data.awarenessLevel}
            </Badge>
          </div>
        )}

        {data.primaryTriggers && data.primaryTriggers.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <AlertCircle className="w-4 h-4 text-primary" />
              Gatilhos Primários
            </div>
            <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
              {data.primaryTriggers.map((trigger, idx) => (
                <li key={idx}>{trigger}</li>
              ))}
            </ul>
          </div>
        )}

        {data.mainObjections && data.mainObjections.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Shield className="w-4 h-4 text-destructive" />
              Principais Objeções
            </div>
            <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
              {data.mainObjections.map((objection, idx) => (
                <li key={idx}>{objection}</li>
              ))}
            </ul>
          </div>
        )}

        {data.buyingCycle && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Repeat className="w-4 h-4 text-primary" />
              Ciclo de Compra
            </div>
            <p className="text-sm text-muted-foreground">{data.buyingCycle}</p>
          </div>
        )}

        {data.touchpointsNeeded && (
          <div className="space-y-2">
            <div className="text-sm font-semibold">Touchpoints Necessários</div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-lg font-bold">
                {data.touchpointsNeeded}
              </Badge>
              <span className="text-sm text-muted-foreground">interações até conversão</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
