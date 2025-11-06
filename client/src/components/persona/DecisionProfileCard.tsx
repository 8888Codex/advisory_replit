import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { UserCheck, Scale, Clock, CheckCircle, AlertTriangle } from "lucide-react";

interface DecisionProfileCardProps {
  data: {
    decisionMakerType?: string;
    decisionCriteria?: Array<{
      criterion: string;
      weight: number;
    }>;
    decisionSpeed?: string;
    validationNeeded?: string[];
    riskTolerance?: string;
  } | null;
}

export function DecisionProfileCard({ data }: DecisionProfileCardProps) {
  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <UserCheck className="w-5 h-5" />
            Perfil de Decisão
          </CardTitle>
          <CardDescription>
            Análise de decisão não disponível
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <UserCheck className="w-5 h-5 text-primary" />
          Perfil de Decisão
        </CardTitle>
        <CardDescription>
          Como essa persona toma decisões
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {data.decisionMakerType && (
          <div className="space-y-2">
            <div className="text-sm font-semibold">Tipo de Decisor</div>
            <Badge variant="default" className="text-base">
              {data.decisionMakerType}
            </Badge>
          </div>
        )}

        {data.decisionCriteria && data.decisionCriteria.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Scale className="w-4 h-4 text-primary" />
              Critérios de Decisão
            </div>
            <div className="space-y-2">
              {data.decisionCriteria.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-muted rounded-md">
                  <span className="text-sm">{item.criterion}</span>
                  <Badge variant="outline">
                    Peso: {item.weight}/10
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data.decisionSpeed && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <Clock className="w-4 h-4 text-primary" />
                Velocidade de Decisão
              </div>
              <Badge variant="secondary">{data.decisionSpeed}</Badge>
            </div>
          )}

          {data.riskTolerance && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <AlertTriangle className="w-4 h-4 text-primary" />
                Tolerância ao Risco
              </div>
              <Badge variant="secondary">{data.riskTolerance}</Badge>
            </div>
          )}
        </div>

        {data.validationNeeded && data.validationNeeded.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <CheckCircle className="w-4 h-4 text-primary" />
              Validação Necessária
            </div>
            <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
              {data.validationNeeded.map((validation, idx) => (
                <li key={idx}>{validation}</li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
