import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Map, AlertCircle, Shield, Repeat } from "lucide-react";

interface BuyerJourneyCardProps {
  data: {
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
