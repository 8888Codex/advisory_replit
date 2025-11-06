import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Briefcase, Heart, Users, TrendingUp, Target } from "lucide-react";

interface JobsToBeDoneCardProps {
  data: {
    functionalJob?: string;
    emotionalJob?: string;
    socialJob?: string;
    progressDesired?: string;
    successMetrics?: string[];
  } | null;
}

export function JobsToBeDoneCard({ data }: JobsToBeDoneCardProps) {
  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Briefcase className="w-5 h-5" />
            Jobs-to-be-Done
          </CardTitle>
          <CardDescription>
            Análise de JTBD não disponível
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Briefcase className="w-5 h-5 text-primary" />
          Jobs-to-be-Done
        </CardTitle>
        <CardDescription>
          Trabalhos funcionais, emocionais e sociais
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {data.functionalJob && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Briefcase className="w-4 h-4 text-primary" />
              Trabalho Funcional
            </div>
            <p className="text-sm p-4 bg-muted rounded-md border-l-4 border-primary">
              {data.functionalJob}
            </p>
          </div>
        )}

        {data.emotionalJob && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Heart className="w-4 h-4 text-primary" />
              Trabalho Emocional
            </div>
            <p className="text-sm p-4 bg-muted rounded-md border-l-4 border-primary">
              {data.emotionalJob}
            </p>
          </div>
        )}

        {data.socialJob && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Users className="w-4 h-4 text-primary" />
              Trabalho Social
            </div>
            <p className="text-sm p-4 bg-muted rounded-md border-l-4 border-primary">
              {data.socialJob}
            </p>
          </div>
        )}

        {data.progressDesired && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <TrendingUp className="w-4 h-4 text-primary" />
              Progresso Desejado
            </div>
            <p className="text-sm p-4 bg-muted rounded-md">
              {data.progressDesired}
            </p>
          </div>
        )}

        {data.successMetrics && data.successMetrics.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Target className="w-4 h-4 text-primary" />
              Métricas de Sucesso
            </div>
            <div className="flex flex-wrap gap-2">
              {data.successMetrics.map((metric, idx) => (
                <Badge key={idx} variant="secondary">
                  {metric}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
