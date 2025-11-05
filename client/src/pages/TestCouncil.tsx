import { useState, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useLocation } from "wouter";
import { apiRequest } from "@/lib/queryClient";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Switch } from "@/components/ui/switch";
import { Loader2, Users, Sparkles, TrendingUp, Zap, Star, Lightbulb, MessageSquare } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useCouncilStream } from "@/hooks/useCouncilStream";
import { useDebounce } from "@/hooks/useDebounce";
import { CouncilAnimation } from "@/components/council/CouncilAnimation";
import { motion } from "framer-motion";

interface Expert {
  id: string;
  name: string;
  tagline: string;
  specialty: string;
  avatar?: string;
}

interface ExpertRecommendation {
  expertId: string;
  expertName: string;
  relevanceScore: number;  // 1-5 stars
  justification: string;
}

interface CouncilAnalysis {
  id: string;
  problem: string;
  contributions: Array<{
    expertId: string;
    expertName: string;
    analysis: string;
    keyInsights: string[];
    recommendations: string[];
  }>;
  consensus: string;
}

export default function TestCouncil() {
  const [, setLocation] = useLocation();
  const [problem, setProblem] = useState("");
  const [selectedExperts, setSelectedExperts] = useState<string[]>([]);
  const [useStreaming, setUseStreaming] = useState(true); // Auto-enable for 2+ experts

  const { data: experts = [], isLoading: loadingExperts } = useQuery<Expert[]>({
    queryKey: ["/api/experts"],
  });

  // Debounce problem input for recommendations (800ms delay)
  const debouncedProblem = useDebounce(problem, 800);

  // Get expert recommendations based on problem
  const { data: recommendationsData, isLoading: loadingRecommendations } = useQuery<{ recommendations: ExpertRecommendation[] }>({
    queryKey: ["/api/recommend-experts", debouncedProblem],
    queryFn: async () => {
      if (!debouncedProblem.trim() || debouncedProblem.trim().length < 10) {
        return { recommendations: [] };
      }
      
      const response = await apiRequest("/api/recommend-experts", {
        method: "POST",
        body: JSON.stringify({ problem: debouncedProblem }),
        headers: { "Content-Type": "application/json" },
      });
      return response.json();
    },
    enabled: debouncedProblem.trim().length >= 10,
  });

  const recommendations = recommendationsData?.recommendations || [];

  // SSE Streaming hook
  const [streamingEnabled, setStreamingEnabled] = useState(false);
  const streamState = useCouncilStream({
    problem: problem.trim(),
    expertIds: selectedExperts,
    enabled: streamingEnabled,
  });

  // Traditional mutation (non-streaming)
  const analyzeMutation = useMutation({
    mutationFn: async (data: { problem: string; expertIds: string[] }) => {
      const response = await apiRequest("/api/council/analyze", {
        method: "POST",
        body: JSON.stringify(data),
        headers: { "Content-Type": "application/json" },
      });
      return response.json();
    },
  });

  // Start streaming when enabled
  useEffect(() => {
    if (streamingEnabled && !streamState.isStreaming && !streamState.finalAnalysis) {
      streamState.startStreaming();
    }
  }, [streamingEnabled]);

  const handleToggleExpert = (expertId: string) => {
    setSelectedExperts((prev) =>
      prev.includes(expertId)
        ? prev.filter((id) => id !== expertId)
        : [...prev, expertId]
    );
  };

  const handleSelectAll = () => {
    if (selectedExperts.length === experts.length) {
      setSelectedExperts([]);
    } else {
      setSelectedExperts(experts.map((e) => e.id));
    }
  };

  const handleApplySuggestions = () => {
    const recommendedIds = recommendations.map(r => r.expertId);
    setSelectedExperts(recommendedIds);
  };

  const handleSubmit = async () => {
    if (!problem.trim()) return;
    if (selectedExperts.length === 0) return;

    if (useStreaming) {
      // Use SSE streaming
      setStreamingEnabled(true);
    } else {
      // Use traditional mutation
      analyzeMutation.mutate({
        problem: problem.trim(),
        expertIds: selectedExperts,
      });
    }
  };

  const analysis = streamState.finalAnalysis || (analyzeMutation.data as CouncilAnalysis | undefined);
  const isAnalyzing = useStreaming ? streamState.isStreaming : analyzeMutation.isPending;

  return (
    <div className="container mx-auto py-8 px-4 max-w-7xl">
      <motion.div 
        className="mb-8"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
      >
        <h1 className="text-4xl font-semibold mb-2 flex items-center gap-3">
          <Users className="h-10 w-10 text-muted-foreground" />
          Teste de Análise do Conselho
        </h1>
        <p className="text-muted-foreground">
          Teste a funcionalidade do conselho de IA com lendas do marketing
        </p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.1, ease: [0.25, 0.1, 0.25, 1] }}
          >
            <Card className="rounded-2xl">
              <CardHeader>
                <CardTitle className="font-semibold">Seu Desafio de Negócio</CardTitle>
                <CardDescription>
                  Descreva o problema que você gostaria que o conselho analisasse
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Textarea
                  placeholder="Exemplo: Estamos lançando uma marca de moda sustentável para a Geração Z. Como devemos nos posicionar contra gigantes do fast fashion mantendo valores autênticos?"
                  value={problem}
                  onChange={(e) => setProblem(e.target.value)}
                  className="min-h-[150px] text-base"
                  disabled={analyzeMutation.isPending}
                  data-testid="input-problem"
                />
              </CardContent>
            </Card>
          </motion.div>

          {/* AI Recommendations Section */}
          {loadingRecommendations && debouncedProblem.trim().length >= 10 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
            >
              <Card className="border-accent/20 bg-muted/30 rounded-2xl">
                <CardContent className="pt-6 pb-6">
                  <div className="flex items-center gap-3">
                    <Loader2 className="h-5 w-5 animate-spin text-accent" />
                    <p className="text-sm text-muted-foreground">
                      Analisando seu problema para recomendar especialistas...
                    </p>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {recommendations.length > 0 && !loadingRecommendations && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
            >
              <Card className="border-accent/20 bg-muted/30 rounded-2xl">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Lightbulb className="h-5 w-5 text-accent" />
                      <CardTitle className="text-lg font-semibold">Sugestões da IA</CardTitle>
                    </div>
                    <Button
                      variant="default"
                      size="sm"
                      onClick={handleApplySuggestions}
                      disabled={analyzeMutation.isPending || loadingRecommendations}
                      data-testid="button-apply-suggestions"
                    >
                      Usar Sugestões ({recommendations.length})
                    </Button>
                  </div>
                  <CardDescription>
                    Recomendamos estes especialistas com base no seu problema
                  </CardDescription>
                </CardHeader>
              </Card>
            </motion.div>
          )}

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.2, ease: [0.25, 0.1, 0.25, 1] }}
          >
            <Card className="rounded-2xl">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="font-semibold">Selecionar Especialistas</CardTitle>
                    <CardDescription>
                      Escolha quais lendas do marketing consultar ({selectedExperts.length}{" "}
                      selecionado{selectedExperts.length !== 1 ? 's' : ''})
                    </CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleSelectAll}
                    disabled={loadingExperts || analyzeMutation.isPending}
                    data-testid="button-select-all"
                  >
                    {selectedExperts.length === experts.length ? "Desmarcar Todos" : "Selecionar Todos"}
                  </Button>
                </div>
              </CardHeader>
            <CardContent>
              {loadingExperts ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : (
                <TooltipProvider>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {experts.map((expert, index) => {
                      const recommendation = recommendations.find(r => r.expertId === expert.id);
                      const isRecommended = !!recommendation;
                      
                      return (
                        <Tooltip key={expert.id}>
                          <TooltipTrigger asChild>
                            <motion.div
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ duration: 0.3, delay: index * 0.05, ease: [0.25, 0.1, 0.25, 1] }}
                              className={`flex items-start space-x-3 p-3 rounded-xl border hover-elevate active-elevate-2 cursor-pointer transition-all ${
                                isRecommended ? 'border-accent/30 bg-muted/40' : ''
                              }`}
                              onClick={() => handleToggleExpert(expert.id)}
                              data-testid={`expert-card-${expert.id}`}
                            >
                              <Checkbox
                                checked={selectedExperts.includes(expert.id)}
                                disabled={analyzeMutation.isPending}
                                data-testid={`checkbox-expert-${expert.id}`}
                              />
                              <Avatar className="h-10 w-10 flex-shrink-0 ring-2 ring-accent/20">
                                <AvatarImage src={expert.avatar} alt={expert.name} className="object-cover" />
                                <AvatarFallback className="text-xs font-semibold">
                                  {expert.name.split(' ').map(n => n[0]).join('').substring(0, 2)}
                                </AvatarFallback>
                              </Avatar>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                  <Label className="font-semibold cursor-pointer">
                                    {expert.name}
                                  </Label>
                                  {isRecommended && (
                                    <Badge variant="secondary" className="text-xs px-1.5 py-0">
                                      Recomendado
                                    </Badge>
                                  )}
                                </div>
                                {isRecommended && recommendation && (
                                  <div className="flex items-center gap-0.5 mb-1">
                                    {Array.from({ length: 5 }).map((_, i) => (
                                      <Star
                                        key={i}
                                        className={`h-3 w-3 ${
                                          i < recommendation.relevanceScore
                                            ? 'fill-accent text-accent'
                                            : 'text-muted-foreground/30'
                                        }`}
                                      />
                                    ))}
                                  </div>
                                )}
                                <p className="text-sm text-muted-foreground line-clamp-2">
                                  {expert.tagline}
                                </p>
                                <Badge variant="secondary" className="mt-1 text-xs">
                                  {expert.specialty}
                                </Badge>
                              </div>
                            </motion.div>
                          </TooltipTrigger>
                          {isRecommended && recommendation && (
                            <TooltipContent className="max-w-xs">
                              <p className="text-sm">{recommendation.justification}</p>
                            </TooltipContent>
                          )}
                        </Tooltip>
                      );
                    })}
                  </div>
                </TooltipProvider>
              )}
            </CardContent>
            </Card>
          </motion.div>

          {/* Streaming Toggle */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
          >
            <Card className="rounded-2xl">
            <CardContent className="pt-6 pb-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="streaming-mode" className="flex items-center gap-2 cursor-pointer font-semibold">
                    <Zap className="h-4 w-4 text-accent" />
                    Modo Streaming ao Vivo
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    Veja os especialistas trabalhando em tempo real
                  </p>
                </div>
                <Switch
                  id="streaming-mode"
                  checked={useStreaming}
                  onCheckedChange={setUseStreaming}
                  disabled={isAnalyzing}
                  data-testid="switch-streaming"
                />
              </div>
            </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
          >
            <Button
              onClick={handleSubmit}
            disabled={
              !problem.trim() ||
              selectedExperts.length === 0 ||
              isAnalyzing
            }
            className="w-full"
            size="lg"
            data-testid="button-analyze"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Analisando... (pode levar 1-3 minutos)
              </>
            ) : (
              <>
                {useStreaming ? <Zap className="mr-2 h-5 w-5" /> : <Sparkles className="mr-2 h-5 w-5" />}
                Consultar Conselho ({selectedExperts.length} especialista{selectedExperts.length !== 1 ? 's' : ''})
              </>
            )}
            </Button>
          </motion.div>

          {analyzeMutation.isError && (
            <Card className="border-destructive">
              <CardContent className="pt-6">
                <p className="text-destructive">
                  ❌ Erro: {(analyzeMutation.error as Error).message}
                </p>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Show CouncilAnimation when streaming */}
        {useStreaming && (streamState.isStreaming || streamState.expertStatusArray.length > 0) && (
          <div className="lg:col-span-3">
            <CouncilAnimation
              expertStatuses={streamState.expertStatusArray}
              activityFeed={streamState.activityFeed}
              isStreaming={streamState.isStreaming}
            />
          </div>
        )}

        {/* Show results (for both streaming and non-streaming after completion) */}
        <div className={`lg:col-span-1 ${useStreaming && (streamState.isStreaming || !streamState.finalAnalysis) ? "hidden" : ""}`}>
          {analysis ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
            >
              <Card className="rounded-2xl">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 font-semibold">
                  <TrendingUp className="h-5 w-5 text-accent" />
                  Insights do Conselho
                </CardTitle>
                <CardDescription>
                  Análise de {analysis.contributions.length} especialista{analysis.contributions.length !== 1 ? 's' : ''}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[600px] pr-4">
                  <div className="space-y-6">
                    <Card className="border-primary/30 bg-primary/10 rounded-xl">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-base flex items-center gap-2">
                          <Users className="w-5 h-5 text-primary" />
                          🎯 Consenso da Mesa
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-foreground whitespace-pre-wrap">
                          {analysis.consensus}
                        </p>
                      </CardContent>
                    </Card>

                    <div className="space-y-4">
                      <h3 className="font-semibold">💡 Contribuições dos Especialistas</h3>
                      {analysis.contributions.map((contrib: { expertName: string; keyInsights: string[]; recommendations: string[] }, idx: number) => (
                        <Card key={idx} className="rounded-xl">
                          <CardHeader className="pb-3">
                            <CardTitle className="text-base font-semibold">
                              {contrib.expertName}
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="space-y-3">
                            {contrib.keyInsights.length > 0 && (
                              <div>
                                <p className="text-sm font-medium mb-1">Principais Insights:</p>
                                <ul className="text-sm text-muted-foreground space-y-1">
                                  {contrib.keyInsights.map((insight: string, i: number) => (
                                    <li key={i} className="flex gap-2">
                                      <span>•</span>
                                      <span>{insight}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {contrib.recommendations.length > 0 && (
                              <div>
                                <p className="text-sm font-medium mb-1">
                                  Recomendações:
                                </p>
                                <ul className="text-sm text-muted-foreground space-y-1">
                                  {contrib.recommendations.map((rec: string, i: number) => (
                                    <li key={i} className="flex gap-2">
                                      <span>→</span>
                                      <span>{rec}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </div>
                </ScrollArea>
                
                <motion.div 
                  className="pt-4 border-t mt-4"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.24, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
                >
                  <Button
                    onClick={() => setLocation(`/council-room/${analysis.id}`)}
                    className="w-full"
                    variant="default"
                    data-testid="button-enter-council-room"
                  >
                    <MessageSquare className="h-4 w-4 mr-2" />
                    Entrar na Sala do Conselho
                  </Button>
                  <p className="text-xs text-muted-foreground text-center mt-2">
                    Continue a conversa com os especialistas
                  </p>
                </motion.div>
              </CardContent>
            </Card>
            </motion.div>
          ) : (
            <Card className="border-dashed rounded-2xl">
              <CardContent className="pt-6">
                <div className="text-center text-muted-foreground py-12">
                  <Users className="h-12 w-12 mx-auto mb-4 opacity-30" />
                  <p className="text-sm">Envie um problema para ver a análise do conselho</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
