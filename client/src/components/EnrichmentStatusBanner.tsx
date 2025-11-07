import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Sparkles, CheckCircle2, AlertCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Badge } from "@/components/ui/badge";

type EnrichmentStatus = "pending" | "processing" | "completed" | "failed" | "no_persona";

export function EnrichmentStatusBanner() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [previousStatus, setPreviousStatus] = useState<EnrichmentStatus | null>(null);

  // Poll enrichment status every 5 seconds
  const { data: statusData } = useQuery<{
    status: EnrichmentStatus;
    personaId?: string;
    enrichmentLevel?: string;
    researchCompleteness?: number;
  }>({
    queryKey: ["/api/persona/enrichment-status"],
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      // Poll every 5s while pending or processing, stop when completed/failed/no_persona
      return (status === "pending" || status === "processing") ? 5000 : false;
    },
    staleTime: 0, // Always refetch to get latest status
  });

  const status = statusData?.status || "no_persona";

  // Show toast when enrichment completes
  useEffect(() => {
    if (previousStatus === "processing" && status === "completed") {
      toast({
        title: "✨ Persona enriquecida!",
        description: "Sua persona está pronta com todos os módulos de análise.",
      });
      // Invalidate persona query to refresh data
      queryClient.invalidateQueries({ queryKey: ["/api/persona/current"] });
    } else if (previousStatus === "processing" && status === "failed") {
      toast({
        title: "Erro no enriquecimento",
        description: "Houve um problema ao enriquecer sua persona. Por favor, tente novamente.",
        variant: "destructive",
      });
    }
    setPreviousStatus(status);
  }, [status, previousStatus, toast, queryClient]);

  // Don't show banner if no persona or already completed
  if (status === "no_persona" || status === "completed" || status === "pending") {
    return null;
  }

  const levelLabels = {
    quick: "Quick (3 módulos)",
    strategic: "Strategic (6 módulos)",
    complete: "Complete (8 módulos)",
  };

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-accent/10 border-b border-accent/20 backdrop-blur-sm">
      <div className="container mx-auto px-4 py-2">
        <div className="flex items-center justify-center gap-3">
          {status === "processing" && (
            <>
              <Sparkles className="w-4 h-4 text-accent animate-pulse" />
              <span className="text-sm font-medium text-foreground">
                Enriquecendo sua persona...
              </span>
              {statusData?.enrichmentLevel && (
                <Badge variant="outline" className="text-xs">
                  {levelLabels[statusData.enrichmentLevel as keyof typeof levelLabels] || statusData.enrichmentLevel}
                </Badge>
              )}
              <span className="text-xs text-muted-foreground">
                Isso pode levar alguns minutos. Você já pode usar a plataforma!
              </span>
            </>
          )}
          {status === "failed" && (
            <>
              <AlertCircle className="w-4 h-4 text-destructive" />
              <span className="text-sm font-medium text-destructive">
                Erro ao enriquecer persona
              </span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
