import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Sparkles } from "lucide-react";
import type { UserPersona } from "@shared/schema";

interface PersonaContextBadgeProps {
  persona: UserPersona | null;
  compact?: boolean;
}

export function PersonaContextBadge({ persona, compact = false }: PersonaContextBadgeProps) {
  if (!persona) return null;

  const hasEnrichment = 
    (persona.campaignReferences && persona.campaignReferences.length > 0) ||
    (persona.painPoints && persona.painPoints.length > 0);

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge 
            variant="secondary" 
            className="gap-1.5 cursor-help"
            data-testid="badge-persona-context"
          >
            <Sparkles className="h-3 w-3" />
            {compact ? "Contexto Ativo" : `Usando contexto: ${persona.companyName}`}
          </Badge>
        </TooltipTrigger>
        <TooltipContent className="max-w-xs" side="bottom">
          <div className="space-y-2">
            <p className="font-semibold text-sm">Contexto Personalizado Ativo</p>
            <div className="text-xs space-y-1">
              <p>• <span className="font-medium">Empresa:</span> {persona.companyName}</p>
              <p>• <span className="font-medium">Indústria:</span> {persona.industry}</p>
              <p>• <span className="font-medium">Público-alvo:</span> {persona.targetAudience}</p>
              {persona.primaryGoal && (
                <p>• <span className="font-medium">Objetivo:</span> {persona.primaryGoal}</p>
              )}
              {persona.mainChallenge && (
                <p>• <span className="font-medium">Desafio:</span> {persona.mainChallenge}</p>
              )}
              {hasEnrichment && (
                <p className="text-accent mt-2">
                  ✨ Enriquecido com pesquisa de mercado
                </p>
              )}
            </div>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
