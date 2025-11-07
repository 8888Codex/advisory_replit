import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { queryClient, apiRequest } from "@/lib/queryClient";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Loader2, Download, Trash2, Edit } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface Persona {
  id: string;
  userId: string;
  name: string;
  researchMode: "quick" | "strategic";
  demographics: Record<string, any>;
  psychographics: Record<string, any>;
  painPoints: string[];
  goals: string[];
  values: string[];
  contentPreferences: Record<string, any>;
  communities: string[];
  behavioralPatterns: Record<string, any>;
  researchData: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export default function Personas() {
  const { toast } = useToast();
  const [mode, setMode] = useState<"quick" | "strategic">("quick");
  const [targetDescription, setTargetDescription] = useState("");
  const [industry, setIndustry] = useState("");
  const [additionalContext, setAdditionalContext] = useState("");
  const [selectedPersona, setSelectedPersona] = useState<Persona | null>(null);

  // Fetch personas
  const { data: personas = [], isLoading: loadingPersonas } = useQuery<Persona[]>({
    queryKey: ["/api/personas"],
  });

  // Create persona mutation
  const createPersonaMutation = useMutation({
    mutationFn: async (data: {
      mode: "quick" | "strategic";
      targetDescription: string;
      industry?: string;
      additionalContext?: string;
    }) => {
      const response = await apiRequest("/api/personas", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/personas"] });
      toast({
        title: "Persona criada!",
        description: "Sua persona foi gerada com sucesso.",
      });
      // Reset form
      setTargetDescription("");
      setIndustry("");
      setAdditionalContext("");
    },
    onError: (error: any) => {
      toast({
        title: "Erro ao criar persona",
        description: error.message || "Tente novamente mais tarde.",
        variant: "destructive",
      });
    },
  });

  // Delete persona mutation
  const deletePersonaMutation = useMutation({
    mutationFn: async (personaId: string) => {
      await apiRequest(`/api/personas/${personaId}`, {
        method: "DELETE",
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/personas"] });
      setSelectedPersona(null);
      toast({
        title: "Persona deletada",
        description: "A persona foi removida com sucesso.",
      });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!targetDescription.trim()) {
      toast({
        title: "Campo obrigatório",
        description: "Descreva seu público-alvo.",
        variant: "destructive",
      });
      return;
    }

    createPersonaMutation.mutate({
      mode,
      targetDescription,
      industry: industry || undefined,
      additionalContext: additionalContext || undefined,
    });
  };

  const handleDownload = async (persona: Persona) => {
    try {
      const response = await fetch(`/api/personas/${persona.id}/download`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `persona_${persona.id}.json`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      toast({
        title: "Erro ao baixar",
        description: "Não foi possível baixar a persona.",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="container mx-auto py-8 max-w-7xl px-4">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold mb-2">Persona Builder</h1>
        <p className="text-muted-foreground">
          Crie personas detalhadas usando pesquisa estratégica em comunidades do Reddit
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Form Column */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Nova Persona</CardTitle>
              <CardDescription>
                Pesquisa {mode === "quick" ? "rápida (1-2 min)" : "estratégica (5-10 min)"}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Mode Selection */}
                <div className="space-y-2">
                  <Label>Modo de Pesquisa</Label>
                  <RadioGroup
                    value={mode}
                    onValueChange={(value) => setMode(value as "quick" | "strategic")}
                    data-testid="radio-mode"
                  >
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="quick" id="quick" data-testid="radio-quick" />
                      <Label htmlFor="quick" className="font-normal cursor-pointer">
                        Rápida (1-2 min)
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="strategic" id="strategic" data-testid="radio-strategic" />
                      <Label htmlFor="strategic" className="font-normal cursor-pointer">
                        Estratégica (5-10 min)
                      </Label>
                    </div>
                  </RadioGroup>
                </div>

                {/* Target Description */}
                <div className="space-y-2">
                  <Label htmlFor="target">Público-Alvo *</Label>
                  <Textarea
                    id="target"
                    data-testid="input-target"
                    placeholder="Ex: Empreendedores de e-commerce no Brasil"
                    value={targetDescription}
                    onChange={(e) => setTargetDescription(e.target.value)}
                    rows={3}
                  />
                </div>

                {/* Industry */}
                <div className="space-y-2">
                  <Label htmlFor="industry">Indústria (opcional)</Label>
                  <Input
                    id="industry"
                    data-testid="input-industry"
                    placeholder="Ex: E-commerce, SaaS, Marketing"
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                  />
                </div>

                {/* Additional Context (Strategic only) */}
                {mode === "strategic" && (
                  <div className="space-y-2">
                    <Label htmlFor="context">Contexto Adicional</Label>
                    <Textarea
                      id="context"
                      data-testid="input-context"
                      placeholder="Informações adicionais que podem ajudar na pesquisa..."
                      value={additionalContext}
                      onChange={(e) => setAdditionalContext(e.target.value)}
                      rows={3}
                    />
                  </div>
                )}

                <Button
                  type="submit"
                  data-testid="button-create-persona"
                  className="w-full"
                  disabled={createPersonaMutation.isPending}
                >
                  {createPersonaMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      {mode === "quick" ? "Pesquisando..." : "Analisando..."}
                    </>
                  ) : (
                    "Criar Persona"
                  )}
                </Button>

                {createPersonaMutation.isPending && (
                  <p className="text-sm text-muted-foreground text-center">
                    {mode === "quick"
                      ? "Pesquisando comunidades e extraindo insights..."
                      : "Conduzindo análise profunda em múltiplas frentes..."}
                  </p>
                )}
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Personas List + Details */}
        <div className="lg:col-span-2 space-y-4">
          {loadingPersonas ? (
            <Card>
              <CardContent className="py-8 text-center">
                <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" />
                <p className="text-muted-foreground">Carregando personas...</p>
              </CardContent>
            </Card>
          ) : personas.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-muted-foreground">
                  Nenhuma persona criada ainda. Use o formulário ao lado para começar.
                </p>
              </CardContent>
            </Card>
          ) : (
            <>
              {/* Personas Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {personas.map((persona) => (
                  <Card
                    key={persona.id}
                    className={`cursor-pointer transition hover-elevate ${
                      selectedPersona?.id === persona.id ? "ring-2 ring-primary" : ""
                    }`}
                    onClick={() => setSelectedPersona(persona)}
                    data-testid={`card-persona-${persona.id}`}
                  >
                    <CardHeader>
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <CardTitle className="text-base truncate">
                            {persona.name}
                          </CardTitle>
                          <CardDescription className="text-xs">
                            {persona.researchMode === "quick" ? "Rápida" : "Estratégica"}
                            {" · "}
                            {new Date(persona.createdAt).toLocaleDateString("pt-BR")}
                          </CardDescription>
                        </div>
                        <div className="flex gap-1">
                          <Button
                            size="icon"
                            variant="ghost"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDownload(persona);
                            }}
                            data-testid={`button-download-${persona.id}`}
                          >
                            <Download className="h-4 w-4" />
                          </Button>
                          <Button
                            size="icon"
                            variant="ghost"
                            onClick={(e) => {
                              e.stopPropagation();
                              deletePersonaMutation.mutate(persona.id);
                            }}
                            data-testid={`button-delete-${persona.id}`}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2 text-sm">
                        <div>
                          <span className="text-muted-foreground">Pain Points:</span>{" "}
                          {persona.painPoints.length}
                        </div>
                        <div>
                          <span className="text-muted-foreground">Goals:</span>{" "}
                          {persona.goals.length}
                        </div>
                        <div>
                          <span className="text-muted-foreground">Communities:</span>{" "}
                          {persona.communities.length}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Selected Persona Details */}
              {selectedPersona && (
                <Card data-testid="card-persona-details">
                  <CardHeader>
                    <CardTitle>{selectedPersona.name}</CardTitle>
                    <CardDescription>
                      Criada em {new Date(selectedPersona.createdAt).toLocaleDateString("pt-BR")} ·{" "}
                      Modo {selectedPersona.researchMode === "quick" ? "Rápido" : "Estratégico"}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {/* Demographics */}
                    {selectedPersona.demographics && Object.keys(selectedPersona.demographics).length > 0 && (
                      <div>
                        <h3 className="font-semibold mb-2">Demografia</h3>
                        <div className="bg-muted/50 p-4 rounded-md space-y-1 text-sm">
                          {Object.entries(selectedPersona.demographics).map(([key, value]) => (
                            <div key={key}>
                              <span className="text-muted-foreground capitalize">
                                {key.replace(/([A-Z])/g, " $1").trim()}:
                              </span>{" "}
                              {String(value)}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Pain Points */}
                    {selectedPersona.painPoints.length > 0 && (
                      <div>
                        <h3 className="font-semibold mb-2">Pain Points</h3>
                        <ul className="list-disc list-inside space-y-1 text-sm">
                          {selectedPersona.painPoints.map((point, idx) => (
                            <li key={idx} className="text-muted-foreground">
                              {point}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Goals */}
                    {selectedPersona.goals.length > 0 && (
                      <div>
                        <h3 className="font-semibold mb-2">Objetivos</h3>
                        <ul className="list-disc list-inside space-y-1 text-sm">
                          {selectedPersona.goals.map((goal, idx) => (
                            <li key={idx} className="text-muted-foreground">
                              {goal}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Values */}
                    {selectedPersona.values.length > 0 && (
                      <div>
                        <h3 className="font-semibold mb-2">Valores</h3>
                        <div className="flex flex-wrap gap-2">
                          {selectedPersona.values.map((value, idx) => (
                            <span
                              key={idx}
                              className="bg-muted px-3 py-1 rounded-full text-sm"
                            >
                              {value}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Communities */}
                    {selectedPersona.communities.length > 0 && (
                      <div>
                        <h3 className="font-semibold mb-2">Comunidades Reddit</h3>
                        <div className="flex flex-wrap gap-2">
                          {selectedPersona.communities.map((community, idx) => (
                            <span
                              key={idx}
                              className="bg-muted px-3 py-1 rounded-full text-sm font-mono"
                            >
                              {community}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Behavioral Patterns (Strategic only) */}
                    {selectedPersona.researchMode === "strategic" &&
                      selectedPersona.behavioralPatterns &&
                      Object.keys(selectedPersona.behavioralPatterns).length > 0 && (
                        <div>
                          <h3 className="font-semibold mb-2">Padrões Comportamentais</h3>
                          <div className="bg-muted/50 p-4 rounded-md space-y-2 text-sm">
                            {Object.entries(selectedPersona.behavioralPatterns).map(
                              ([key, value]) => (
                                <div key={key}>
                                  <span className="font-medium capitalize">
                                    {key.replace(/([A-Z])/g, " $1").trim()}:
                                  </span>
                                  <div className="text-muted-foreground mt-1">
                                    {Array.isArray(value)
                                      ? value.join(", ")
                                      : String(value)}
                                  </div>
                                </div>
                              )
                            )}
                          </div>
                        </div>
                      )}

                    {/* Content Preferences (Strategic only) */}
                    {selectedPersona.researchMode === "strategic" &&
                      selectedPersona.contentPreferences &&
                      Object.keys(selectedPersona.contentPreferences).length > 0 && (
                        <div>
                          <h3 className="font-semibold mb-2">Preferências de Conteúdo</h3>
                          <div className="bg-muted/50 p-4 rounded-md space-y-2 text-sm">
                            {Object.entries(selectedPersona.contentPreferences).map(
                              ([key, value]) => (
                                <div key={key}>
                                  <span className="font-medium capitalize">
                                    {key.replace(/([A-Z])/g, " $1").trim()}:
                                  </span>
                                  <div className="text-muted-foreground mt-1">
                                    {Array.isArray(value)
                                      ? value.join(", ")
                                      : String(value)}
                                  </div>
                                </div>
                              )
                            )}
                          </div>
                        </div>
                      )}
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
