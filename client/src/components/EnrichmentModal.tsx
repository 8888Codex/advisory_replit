import { useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Zap, TrendingUp, Sparkles, Loader2, CheckCircle2 } from "lucide-react";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

interface EnrichmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  personaId: string;
  currentMode?: "quick" | "strategic" | "complete";
}

const RESEARCH_MODES = [
  {
    id: "quick",
    name: "QUICK",
    duration: "2-3 minutos",
    icon: Zap,
    features: [
      "Reddit research",
      "Análise básica de público",
      "Ideal para primeiros insights",
    ],
  },
  {
    id: "strategic",
    name: "STRATEGIC",
    duration: "5-8 minutos",
    icon: TrendingUp,
    recommended: true,
    features: [
      "Reddit + YouTube (5 vídeos)",
      "Referências de campanhas",
      "Recomendado para a maioria",
    ],
  },
  {
    id: "complete",
    name: "COMPLETE",
    duration: "10-15 minutos",
    icon: Sparkles,
    features: [
      "Pesquisa abrangente (10+ vídeos)",
      "Insights profundos + tendências",
      "Análise mais completa disponível",
    ],
  },
];

const PROGRESS_STEPS = [
  { percent: 10, text: "Gerando queries de pesquisa..." },
  { percent: 30, text: "Buscando vídeos no YouTube..." },
  { percent: 60, text: "Analisando insights com Claude..." },
  { percent: 85, text: "Sintetizando campanhas relevantes..." },
  { percent: 95, text: "Finalizando enriquecimento..." },
  { percent: 100, text: "Concluído!" },
];

const DURATIONS = {
  quick: 3 * 60 * 1000,      // 3 min
  strategic: 7 * 60 * 1000,  // 7 min
  complete: 12 * 60 * 1000,  // 12 min
};

export default function EnrichmentModal({
  isOpen,
  onClose,
  personaId,
  currentMode = "strategic",
}: EnrichmentModalProps) {
  const [selectedMode, setSelectedMode] = useState<string>(currentMode);
  const [isEnriching, setIsEnriching] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusText, setStatusText] = useState("");
  const { toast } = useToast();
  const queryClient = useQueryClient();

  useEffect(() => {
    setSelectedMode(currentMode);
  }, [currentMode]);

  const enrichMutation = useMutation({
    mutationFn: async (mode: string) => {
      return await apiRequest(`/api/persona/enrich/youtube`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ personaId, mode }),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/persona/current"] });
      toast({
        title: "Persona enriquecida!",
        description: "YouTube research concluído com sucesso.",
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Erro",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const startEnrichment = async () => {
    setIsEnriching(true);
    setProgress(0);
    setStatusText(PROGRESS_STEPS[0].text);

    const totalTime = DURATIONS[selectedMode as keyof typeof DURATIONS];
    const startTime = Date.now();
    const interval = 500;

    let currentStep = 0;
    let apiCompleted = false;
    
    const progressInterval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const percentByTime = Math.min((elapsed / totalTime) * 100, 100);
      
      setProgress(percentByTime);
      
      if (percentByTime >= PROGRESS_STEPS[currentStep]?.percent && currentStep < PROGRESS_STEPS.length) {
        setStatusText(PROGRESS_STEPS[currentStep].text);
        currentStep++;
      }
      
      if (elapsed >= totalTime && apiCompleted) {
        clearInterval(progressInterval);
        setProgress(100);
        setStatusText(PROGRESS_STEPS[PROGRESS_STEPS.length - 1].text);
        setTimeout(() => {
          setIsEnriching(false);
          onClose();
        }, 1000);
      }
    }, interval);

    try {
      await enrichMutation.mutateAsync(selectedMode);
      apiCompleted = true;
    } catch (error) {
      clearInterval(progressInterval);
      setIsEnriching(false);
      setProgress(0);
      setStatusText("");
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl rounded-2xl p-6" data-testid="modal-enrichment">
        <DialogHeader>
          <DialogTitle className="text-2xl font-medium" data-testid="text-modal-title">
            Enriquecer Persona com YouTube Research
          </DialogTitle>
          <DialogDescription className="text-base text-muted-foreground" data-testid="text-modal-description">
            Escolha o modo de pesquisa para enriquecer sua persona com insights de campanhas reais do YouTube.
          </DialogDescription>
        </DialogHeader>

        {!isEnriching ? (
          <div className="space-y-6 py-4" data-testid="section-mode-selection">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {RESEARCH_MODES.map((mode) => {
                const Icon = mode.icon;
                const isSelected = selectedMode === mode.id;

                return (
                  <Card
                    key={mode.id}
                    onClick={() => setSelectedMode(mode.id)}
                    className={`p-6 rounded-2xl cursor-pointer transition-all duration-200 hover-elevate ${
                      isSelected ? "border-2 border-accent" : "border border-border/50"
                    }`}
                    data-testid={`card-mode-${mode.id}`}
                  >
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <Icon className="w-5 h-5 text-accent" data-testid={`icon-mode-${mode.id}`} />
                        <h3 className="text-base font-medium" data-testid={`text-mode-name-${mode.id}`}>
                          {mode.name}
                        </h3>
                        {mode.recommended && (
                          <Badge 
                            variant="secondary" 
                            className="ml-auto text-xs bg-accent/10 text-accent"
                            data-testid="badge-recommended"
                          >
                            Recomendado
                          </Badge>
                        )}
                      </div>
                      
                      <p className="text-sm text-muted-foreground" data-testid={`text-mode-duration-${mode.id}`}>
                        {mode.duration}
                      </p>
                      
                      <ul className="space-y-2">
                        {mode.features.map((feature, idx) => (
                          <li 
                            key={idx} 
                            className="flex items-start gap-2 text-sm"
                            data-testid={`feature-${mode.id}-${idx}`}
                          >
                            <CheckCircle2 className="w-4 h-4 text-accent mt-0.5 flex-shrink-0" />
                            <span>{feature}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </Card>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="py-8 space-y-4" data-testid="section-progress">
            <Progress value={progress} className="mb-4" data-testid="progress-enrichment" />
            <p className="text-center text-sm text-muted-foreground" data-testid="text-status">
              {statusText}
            </p>
            <p className="text-center text-xs text-muted-foreground" data-testid="text-progress-percent">
              {Math.round(progress)}% concluído
            </p>
          </div>
        )}

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isEnriching}
            className="rounded-xl"
            data-testid="button-cancel"
          >
            Cancelar
          </Button>
          <Button
            onClick={startEnrichment}
            disabled={isEnriching}
            className="bg-accent text-accent-foreground rounded-xl"
            data-testid="button-start-enrichment"
          >
            {isEnriching ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" data-testid="icon-loading" />
                Enriquecendo...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" data-testid="icon-sparkles" />
                Iniciar Enrichment
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
