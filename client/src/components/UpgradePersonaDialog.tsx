import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Zap, TrendingUp, Sparkles, Clock, Layers, Users, CheckCircle, Loader2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { queryClient, apiRequest } from "@/lib/queryClient";
import type { UserPersona } from "@shared/schema";

interface UpgradePersonaDialogProps {
  isOpen: boolean;
  onClose: () => void;
  personaId: string;
  currentLevel: "quick" | "strategic" | "complete";
}

const LEVEL_CONFIG = {
  quick: {
    icon: Zap,
    label: "Quick",
    color: "text-yellow-600",
    bgColor: "bg-yellow-500/10",
    borderColor: "border-yellow-500/20",
    time: "~30-45s",
    modules: 3,
    features: [
      "Núcleo Psicográfico (valores, medos, aspirações)",
      "Jornada do Comprador (gatilhos, objeções)",
      "Insights Estratégicos (mensagem central)",
    ],
  },
  strategic: {
    icon: TrendingUp,
    label: "Strategic",
    color: "text-blue-600",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/20",
    time: "~2-3min",
    modules: 6,
    features: [
      "Tudo do Quick +",
      "Perfil Comportamental (Cialdini, canais)",
      "Linguagem & Comunicação (StoryBrand)",
      "Jobs-to-be-Done (funcional, emocional, social)",
    ],
  },
  complete: {
    icon: Sparkles,
    label: "Complete",
    color: "text-purple-600",
    bgColor: "bg-purple-500/10",
    borderColor: "border-purple-500/20",
    time: "~5-7min",
    modules: 8,
    features: [
      "Tudo do Strategic +",
      "Perfil de Decisão (critérios, velocidade)",
      "Exemplos de Copy Prontos (headline, email, LinkedIn)",
      "Análise completa com todos os 18 especialistas",
    ],
  },
};

export default function UpgradePersonaDialog({
  isOpen,
  onClose,
  personaId,
  currentLevel,
}: UpgradePersonaDialogProps) {
  const { toast } = useToast();
  const [upgrading, setUpgrading] = useState(false);

  const nextLevel = currentLevel === "quick" ? "strategic" : "complete";
  const currentConfig = LEVEL_CONFIG[currentLevel];
  const nextConfig = LEVEL_CONFIG[nextLevel];
  const CurrentIcon = currentConfig.icon;
  const NextIcon = nextConfig.icon;

  const upgradeMutation = useMutation({
    mutationFn: async () => {
      setUpgrading(true);
      const result = await apiRequest<UserPersona>(`/api/persona/${personaId}/upgrade`, {
        method: "POST",
      });
      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/persona/current"] });
      toast({
        title: "Upgrade Concluído!",
        description: `Sua persona foi enriquecida para o nível ${nextConfig.label}.`,
      });
      setUpgrading(false);
      onClose();
    },
    onError: (error: any) => {
      setUpgrading(false);
      toast({
        title: "Erro no Upgrade",
        description: error.message || "Não foi possível fazer o upgrade. Tente novamente.",
        variant: "destructive",
      });
    },
  });

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl">Upgrade de Persona</DialogTitle>
          <DialogDescription>
            Desbloqueie insights mais profundos e exemplos de copy prontos para usar
          </DialogDescription>
        </DialogHeader>

        {!upgrading ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 my-6">
              {/* Current Level */}
              <Card className={`border-2 ${currentConfig.borderColor} ${currentConfig.bgColor}`}>
                <CardContent className="p-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`p-3 rounded-lg ${currentConfig.bgColor}`}>
                        <CurrentIcon className={`w-6 h-6 ${currentConfig.color}`} />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold">{currentConfig.label}</h3>
                        <Badge variant="outline">Nível Atual</Badge>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Clock className="w-4 h-4" />
                      <span>{currentConfig.time}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Layers className="w-4 h-4" />
                      <span>{currentConfig.modules} módulos</span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <p className="text-sm font-semibold">Inclui:</p>
                    <ul className="space-y-2">
                      {currentConfig.features.map((feature, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm">
                          <CheckCircle className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </CardContent>
              </Card>

              {/* Next Level */}
              <Card className={`border-2 ${nextConfig.borderColor} ${nextConfig.bgColor} relative overflow-hidden`}>
                <div className="absolute top-4 right-4">
                  <Badge variant="default">Upgrade</Badge>
                </div>
                <CardContent className="p-6 space-y-4">
                  <div className="flex items-center gap-3">
                    <div className={`p-3 rounded-lg ${nextConfig.bgColor}`}>
                      <NextIcon className={`w-6 h-6 ${nextConfig.color}`} />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold">{nextConfig.label}</h3>
                      <Badge variant="secondary">Próximo Nível</Badge>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Clock className="w-4 h-4" />
                      <span>{nextConfig.time}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Layers className="w-4 h-4" />
                      <span>{nextConfig.modules} módulos</span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <p className="text-sm font-semibold">Inclui:</p>
                    <ul className="space-y-2">
                      {nextConfig.features.map((feature, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm">
                          <CheckCircle className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="bg-muted p-4 rounded-lg">
              <div className="flex items-start gap-3">
                <Users className="w-5 h-5 text-primary mt-0.5" />
                <div className="flex-1">
                  <p className="font-semibold mb-1">Upgrade Incremental</p>
                  <p className="text-sm text-muted-foreground">
                    Seus módulos existentes serão preservados. Apenas os novos módulos serão gerados,
                    economizando tempo e garantindo consistência.
                  </p>
                </div>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={onClose} data-testid="button-cancel-upgrade">
                Cancelar
              </Button>
              <Button
                onClick={() => upgradeMutation.mutate()}
                disabled={upgradeMutation.isPending}
                data-testid="button-confirm-upgrade"
              >
                {upgradeMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Processando...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Upgrade para {nextConfig.label}
                  </>
                )}
              </Button>
            </DialogFooter>
          </>
        ) : (
          <div className="py-12 text-center space-y-6">
            <div className="flex justify-center">
              <div className="relative">
                <Loader2 className="w-16 h-16 text-primary animate-spin" />
                <Sparkles className="w-8 h-8 text-primary absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
              </div>
            </div>
            <div className="space-y-2">
              <h3 className="text-xl font-semibold">Consultando Especialistas...</h3>
              <p className="text-muted-foreground">
                Tempo estimado: {nextConfig.time}
              </p>
              <p className="text-sm text-muted-foreground">
                Gerando {nextConfig.modules - currentConfig.modules} novos módulos de análise profunda
              </p>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
