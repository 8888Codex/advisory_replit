import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MessageCircle, Volume2, BookOpen, FileText } from "lucide-react";

interface LanguageCommunicationCardProps {
  data: {
    toneOfVoice?: string;
    vocabulary?: string;
    complexityLevel?: string;
    storyBrandFramework?: {
      character?: string;
      problem?: string;
      guide?: string;
      plan?: string;
      callToAction?: string;
      success?: string;
      failure?: string;
    };
  } | null;
}

export function LanguageCommunicationCard({ data }: LanguageCommunicationCardProps) {
  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageCircle className="w-5 h-5" />
            Linguagem & Comunicação
          </CardTitle>
          <CardDescription>
            Análise de comunicação não disponível
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageCircle className="w-5 h-5 text-primary" />
          Linguagem & Comunicação
        </CardTitle>
        <CardDescription>
          Tom, vocabulário e framework StoryBrand
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {data.toneOfVoice && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <Volume2 className="w-4 h-4 text-primary" />
                Tom de Voz
              </div>
              <Badge variant="secondary">{data.toneOfVoice}</Badge>
            </div>
          )}

          {data.vocabulary && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <BookOpen className="w-4 h-4 text-primary" />
                Vocabulário
              </div>
              <Badge variant="secondary">{data.vocabulary}</Badge>
            </div>
          )}

          {data.complexityLevel && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <FileText className="w-4 h-4 text-primary" />
                Complexidade
              </div>
              <Badge variant="secondary">{data.complexityLevel}</Badge>
            </div>
          )}
        </div>

        {data.storyBrandFramework && (
          <div className="space-y-4">
            <div className="text-sm font-semibold border-b pb-2">Framework StoryBrand</div>
            <div className="grid gap-4">
              {data.storyBrandFramework.character && (
                <div className="p-3 bg-muted rounded-md">
                  <div className="text-xs font-semibold text-muted-foreground mb-1">PERSONAGEM</div>
                  <div className="text-sm">{data.storyBrandFramework.character}</div>
                </div>
              )}
              {data.storyBrandFramework.problem && (
                <div className="p-3 bg-muted rounded-md">
                  <div className="text-xs font-semibold text-muted-foreground mb-1">PROBLEMA</div>
                  <div className="text-sm">{data.storyBrandFramework.problem}</div>
                </div>
              )}
              {data.storyBrandFramework.guide && (
                <div className="p-3 bg-muted rounded-md">
                  <div className="text-xs font-semibold text-muted-foreground mb-1">GUIA</div>
                  <div className="text-sm">{data.storyBrandFramework.guide}</div>
                </div>
              )}
              {data.storyBrandFramework.plan && (
                <div className="p-3 bg-muted rounded-md">
                  <div className="text-xs font-semibold text-muted-foreground mb-1">PLANO</div>
                  <div className="text-sm">{data.storyBrandFramework.plan}</div>
                </div>
              )}
              {data.storyBrandFramework.callToAction && (
                <div className="p-3 bg-muted rounded-md">
                  <div className="text-xs font-semibold text-muted-foreground mb-1">CHAMADA PARA AÇÃO</div>
                  <div className="text-sm">{data.storyBrandFramework.callToAction}</div>
                </div>
              )}
              <div className="grid grid-cols-2 gap-4">
                {data.storyBrandFramework.success && (
                  <div className="p-3 bg-muted rounded-md">
                    <div className="text-xs font-semibold text-muted-foreground mb-1">SUCESSO</div>
                    <div className="text-sm">{data.storyBrandFramework.success}</div>
                  </div>
                )}
                {data.storyBrandFramework.failure && (
                  <div className="p-3 bg-muted rounded-md">
                    <div className="text-xs font-semibold text-muted-foreground mb-1">FRACASSO</div>
                    <div className="text-sm">{data.storyBrandFramework.failure}</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
