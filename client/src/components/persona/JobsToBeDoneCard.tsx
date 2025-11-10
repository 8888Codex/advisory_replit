import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Briefcase, Heart, Users, TrendingUp, Target } from "lucide-react";

interface JobsToBeDoneCardProps {
  data: {
    // New format (from enrichment)
    functionalJobs?: string[];
    emotionalJobs?: string[];
    socialJobs?: string[];
    contextualFactors?: string[];
    successCriteria?: string[];
    // Old format (fallback)
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
        {/* Functional Jobs */}
        {(data.functionalJobs && data.functionalJobs.length > 0) || data.functionalJob ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Briefcase className="w-4 h-4 text-primary" />
              Trabalhos Funcionais
            </div>
            {data.functionalJobs ? (
              <ul className="space-y-2">
                {data.functionalJobs.map((job, idx) => (
                  <li key={idx} className="text-sm p-3 bg-muted/50 rounded-md border-l-4 border-blue-500">
                    {job}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm p-4 bg-muted rounded-md border-l-4 border-primary">
                {data.functionalJob}
              </p>
            )}
          </div>
        ) : null}

        {/* Emotional Jobs */}
        {(data.emotionalJobs && data.emotionalJobs.length > 0) || data.emotionalJob ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Heart className="w-4 h-4 text-rose-500" />
              Trabalhos Emocionais
            </div>
            {data.emotionalJobs ? (
              <ul className="space-y-2">
                {data.emotionalJobs.map((job, idx) => (
                  <li key={idx} className="text-sm p-3 bg-muted/50 rounded-md border-l-4 border-rose-500">
                    {job}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm p-4 bg-muted rounded-md border-l-4 border-rose-500">
                {data.emotionalJob}
              </p>
            )}
          </div>
        ) : null}

        {/* Social Jobs */}
        {(data.socialJobs && data.socialJobs.length > 0) || data.socialJob ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Users className="w-4 h-4 text-purple-500" />
              Trabalhos Sociais
            </div>
            {data.socialJobs ? (
              <ul className="space-y-2">
                {data.socialJobs.map((job, idx) => (
                  <li key={idx} className="text-sm p-3 bg-muted/50 rounded-md border-l-4 border-purple-500">
                    {job}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm p-4 bg-muted rounded-md border-l-4 border-purple-500">
                {data.socialJob}
              </p>
            )}
          </div>
        ) : null}

        {/* Contextual Factors */}
        {data.contextualFactors && data.contextualFactors.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <TrendingUp className="w-4 h-4 text-orange-500" />
              Fatores Contextuais
            </div>
            <div className="flex flex-wrap gap-2">
              {data.contextualFactors.map((factor, idx) => (
                <Badge key={idx} variant="outline" className="text-xs">
                  {factor}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Success Criteria */}
        {(data.successCriteria && data.successCriteria.length > 0) || (data.successMetrics && data.successMetrics.length > 0) ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Target className="w-4 h-4 text-green-500" />
              Critérios de Sucesso
            </div>
            <div className="flex flex-wrap gap-2">
              {(data.successCriteria || data.successMetrics || []).map((metric, idx) => (
                <Badge key={idx} variant="secondary">
                  {metric}
                </Badge>
              ))}
            </div>
          </div>
        ) : null}

        {/* Progress Desired (old format) */}
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
      </CardContent>
    </Card>
  );
}
