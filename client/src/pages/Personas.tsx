import { useQuery, useMutation } from "@tanstack/react-query";
import { queryClient, apiRequest } from "@/lib/queryClient";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, Plus, Trash2, CheckCircle2, Clock, AlertCircle, Building2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Link } from "wouter";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { useState } from "react";

interface UserPersona {
  id: string;
  userId: string;
  companyName: string;
  industry: string;
  companySize: string;
  targetAudience: string;
  primaryGoal: string;
  mainChallenge: string;
  enrichmentLevel: "quick" | "strategic" | "complete";
  enrichmentStatus: "pending" | "processing" | "completed" | "failed";
  researchCompleteness: number;
  createdAt: string;
  lastEnrichedAt: string | null;
}

export default function Personas() {
  const { toast } = useToast();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [personaToDelete, setPersonaToDelete] = useState<string | null>(null);

  const { data: personas = [], isLoading } = useQuery<UserPersona[]>({
    queryKey: ["/api/persona/list"],
  });

  const { data: currentUser } = useQuery<{ activePersonaId?: string }>({
    queryKey: ["/api/auth/me"],
  });

  const setActiveMutation = useMutation({
    mutationFn: async (personaId: string) => {
      return apiRequest("/api/persona/set-active", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ personaId }),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/auth/me"] });
      queryClient.invalidateQueries({ queryKey: ["/api/persona/current"] });
      toast({
        title: "Persona ativada",
        description: "Essa persona será usada nas suas consultas",
      });
    },
    onError: () => {
      toast({
        title: "Erro ao ativar persona",
        description: "Tente novamente",
        variant: "destructive",
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (personaId: string) => {
      return apiRequest(`/api/persona/${personaId}`, {
        method: "DELETE",
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/persona/list"] });
      queryClient.invalidateQueries({ queryKey: ["/api/auth/me"] });
      toast({
        title: "Persona excluída",
        description: "A persona foi removida com sucesso",
      });
      setDeleteDialogOpen(false);
      setPersonaToDelete(null);
    },
    onError: (error: any) => {
      toast({
        title: "Erro ao excluir persona",
        description: error.message || "Tente novamente",
        variant: "destructive",
      });
      setDeleteDialogOpen(false);
      setPersonaToDelete(null);
    },
  });

  const handleDelete = (personaId: string) => {
    setPersonaToDelete(personaId);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (personaToDelete) {
      deleteMutation.mutate(personaToDelete);
    }
  };

  const getStatusBadge = (status: UserPersona["enrichmentStatus"]) => {
    switch (status) {
      case "completed":
        return (
          <Badge variant="default" className="gap-1">
            <CheckCircle2 className="w-3 h-3" />
            Completo
          </Badge>
        );
      case "processing":
        return (
          <Badge variant="secondary" className="gap-1">
            <Loader2 className="w-3 h-3 animate-spin" />
            Processando
          </Badge>
        );
      case "failed":
        return (
          <Badge variant="destructive" className="gap-1">
            <AlertCircle className="w-3 h-3" />
            Falhou
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className="gap-1">
            <Clock className="w-3 h-3" />
            Pendente
          </Badge>
        );
    }
  };

  const getEnrichmentLevelLabel = (level: string) => {
    switch (level) {
      case "quick":
        return "Rápido";
      case "strategic":
        return "Estratégico";
      case "complete":
        return "Completo";
      default:
        return level;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="container max-w-6xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Minhas Personas</h1>
          <p className="text-muted-foreground mt-1">
            Gerencie suas personas de negócio e seus dados enriquecidos
          </p>
        </div>
        <Link href="/onboarding">
          <Button data-testid="button-create-persona" className="gap-2">
            <Plus className="w-4 h-4" />
            Nova Persona
          </Button>
        </Link>
      </div>

      {personas.length === 0 ? (
        <Card className="p-12">
          <div className="flex flex-col items-center justify-center text-center space-y-4">
            <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
              <Building2 className="w-8 h-8 text-muted-foreground" />
            </div>
            <div className="space-y-2">
              <h3 className="text-xl font-semibold">Nenhuma persona criada</h3>
              <p className="text-muted-foreground max-w-md">
                Crie sua primeira persona para começar a receber insights personalizados dos nossos especialistas
              </p>
            </div>
            <Link href="/onboarding">
              <Button data-testid="button-create-first-persona" className="gap-2">
                <Plus className="w-4 h-4" />
                Criar Primeira Persona
              </Button>
            </Link>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {personas.map((persona) => {
            const isActive = currentUser?.activePersonaId === persona.id;
            const canDelete = persona.enrichmentStatus !== "processing";

            return (
              <Card
                key={persona.id}
                data-testid={`card-persona-${persona.id}`}
                className="p-6 space-y-4 hover-elevate"
              >
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-semibold text-lg leading-tight">{persona.companyName}</h3>
                    {isActive && (
                      <Badge variant="default" className="shrink-0">
                        Ativa
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">{persona.industry}</p>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Status</span>
                    {getStatusBadge(persona.enrichmentStatus)}
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Nível</span>
                    <span className="font-medium">{getEnrichmentLevelLabel(persona.enrichmentLevel)}</span>
                  </div>
                  {persona.enrichmentStatus === "completed" && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Completude</span>
                      <span className="font-medium">{persona.researchCompleteness}%</span>
                    </div>
                  )}
                </div>

                <div className="flex gap-2 pt-2">
                  <Link href={`/personas/${persona.id}`} className="flex-1">
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full"
                      data-testid={`button-view-${persona.id}`}
                    >
                      Ver Detalhes
                    </Button>
                  </Link>
                  {!isActive && (
                    <Button
                      variant="default"
                      size="sm"
                      onClick={() => setActiveMutation.mutate(persona.id)}
                      disabled={setActiveMutation.isPending}
                      data-testid={`button-activate-${persona.id}`}
                    >
                      {setActiveMutation.isPending ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        "Ativar"
                      )}
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDelete(persona.id)}
                    disabled={!canDelete || deleteMutation.isPending}
                    data-testid={`button-delete-${persona.id}`}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir persona?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta ação não pode ser desfeita. Todos os dados enriquecidos serão permanentemente removidos.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="button-cancel-delete">Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              className="bg-destructive text-destructive-foreground hover-elevate"
              data-testid="button-confirm-delete"
            >
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
