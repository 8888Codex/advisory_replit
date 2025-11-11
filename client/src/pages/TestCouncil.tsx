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
import { Loader2, Users, Sparkles, TrendingUp, Zap, Star, Lightbulb, MessageSquare, Brain } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useCouncilStream } from "@/hooks/useCouncilStream";
import { useDebounce } from "@/hooks/useDebounce";
import { CouncilAnimation } from "@/components/council/CouncilAnimation";
import { motion } from "framer-motion";
import { AIEnhanceButton } from "@/components/AIEnhanceButton";

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
  
  // Load preselected experts from localStorage (from Experts page)
  useEffect(() => {
    const preselected = localStorage.getItem('preselectedExperts');
    const preselectedProblem = localStorage.getItem('preselectedProblem');
    
    if (preselected) {
      try {
        const expertIds = JSON.parse(preselected);
        if (Array.isArray(expertIds) && expertIds.length > 0) {
          setSelectedExperts(expertIds);
          localStorage.removeItem('preselectedExperts'); // Clean up
        }
      } catch (e) {
        console.error('Failed to parse preselected experts:', e);
      }
    }
    
    if (preselectedProblem) {
      setProblem(preselectedProblem);
      localStorage.removeItem('preselectedProblem'); // Clean up
    }
  }, []);

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
    <div className="container mx-auto py-8 px-4 sm:px-6 max-w-6xl">
      {/* Premium Hero Section */}
      <motion.div 
        className="mb-10 relative overflow-hidden rounded-3xl bg-gradient-to-br from-primary/20 via-accent/10 to-primary/20 p-6 sm:p-8 border border-primary/20"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
      >
        {/* Background pattern */}
        <div className="absolute inset-0 bg-grid-pattern opacity-10" />
        
        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-3 sm:gap-4">
            <motion.div
              className="p-3 sm:p-4 rounded-2xl bg-gradient-to-br from-primary to-accent shadow-xl shadow-primary/30"
              animate={{ rotate: [0, 5, -5, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
            >
              <Users className="h-6 w-6 sm:h-8 sm:w-8 text-white" />
            </motion.div>
            
            <div>
              <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-1 sm:mb-2 text-gradient-primary">
                Conselho Estratégico
              </h1>
              <p className="text-muted-foreground text-xs sm:text-sm md:text-base">
                18 Lendas do Marketing analisando seu desafio em tempo real
              </p>
            </div>
          </div>
          
          <motion.div
            className="flex items-center gap-2 w-full md:w-auto justify-end"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
          >
            <Badge className="bg-gradient-to-r from-accent to-primary text-white px-3 sm:px-4 py-1.5 sm:py-2 shadow-lg shadow-accent/30 animate-pulse-subtle text-xs sm:text-sm">
              <Sparkles className="h-3 w-3 sm:h-4 sm:w-4 mr-1.5 sm:mr-2" />
              {selectedExperts.length} Expert{selectedExperts.length !== 1 ? 's' : ''} Selecionado{selectedExperts.length !== 1 ? 's' : ''}
            </Badge>
          </motion.div>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr,400px] gap-6">
        <div className="space-y-6">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.1, ease: [0.25, 0.1, 0.25, 1] }}
          >
            <Card className="rounded-2xl overflow-hidden border-primary/20 hover:border-primary/40 transition-all shadow-lg hover:shadow-xl">
              <div className="relative overflow-hidden">
                {/* Decorative gradient */}
                <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-primary/10 to-transparent rounded-full blur-3xl" />
                
                <CardHeader className="relative z-10">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-xl bg-primary/10 ring-2 ring-primary/20">
                        <Lightbulb className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <CardTitle className="font-semibold text-lg">Seu Desafio de Negócio</CardTitle>
                        <CardDescription>
                          Descreva o problema estratégico que você gostaria que o conselho analisasse
                        </CardDescription>
                      </div>
                    </div>
                    <AIEnhanceButton
                      currentText={problem}
                      fieldType="challenge"
                      context={{}}
                      onEnhanced={(enhanced) => setProblem(enhanced)}
                      disabled={isAnalyzing}
                    />
                  </div>
                </CardHeader>
                <CardContent className="relative z-10">
                  <Textarea
                    placeholder="Exemplo: Estamos lançando uma marca de moda sustentável para a Geração Z. Como devemos nos posicionar contra gigantes do fast fashion mantendo valores autênticos?"
                    value={problem}
                    onChange={(e) => setProblem(e.target.value)}
                    className="min-h-[150px] text-base backdrop-blur-sm bg-background/50 border-2 border-border/50 focus:border-primary/50 transition-all"
                    disabled={analyzeMutation.isPending}
                    data-testid="input-problem"
                  />
                  {problem.trim().length > 0 && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="mt-2 flex items-center gap-2"
                    >
                      <div className="text-xs text-muted-foreground flex items-center gap-1">
                        <span className={problem.trim().length >= 10 ? "text-primary" : "text-muted-foreground"}>
                          {problem.trim().length} caracteres
                        </span>
                        {problem.trim().length >= 10 && (
                          <Badge variant="outline" className="text-xs px-2 py-0 bg-primary/10 text-primary border-primary/30">
                            ✓ Pronto
                          </Badge>
                        )}
                      </div>
                    </motion.div>
                  )}
                </CardContent>
              </div>
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
            <Card className="rounded-2xl glass-premium-strong">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-xl bg-accent/10 ring-2 ring-accent/20">
                      <Users className="h-5 w-5 text-accent" />
                    </div>
                    <div>
                      <CardTitle className="font-semibold">Selecionar Especialistas</CardTitle>
                      <CardDescription>
                        Escolha quais lendas do marketing consultar
                      </CardDescription>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleSelectAll}
                    disabled={loadingExperts || analyzeMutation.isPending}
                    data-testid="button-select-all"
                    className="hover-scale-sm"
                  >
                    {selectedExperts.length === experts.length ? "Desmarcar Todos" : "Selecionar Todos"}
                  </Button>
                </div>
                
                {/* Progress bar */}
                {selectedExperts.length > 0 && (
                  <motion.div
                    initial={{ scaleX: 0 }}
                    animate={{ scaleX: 1 }}
                    className="mt-3 h-1 bg-gradient-to-r from-accent to-primary rounded-full origin-left"
                    style={{ width: `${(selectedExperts.length / experts.length) * 100}%` }}
                  />
                )}
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
                      
                      const isSelected = selectedExperts.includes(expert.id);
                      
                      return (
                        <Tooltip key={expert.id}>
                          <TooltipTrigger asChild>
                            <motion.div
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ duration: 0.3, delay: index * 0.05, ease: [0.25, 0.1, 0.25, 1] }}
                              whileHover={{ y: -4, scale: 1.02 }}
                              className={`group relative flex items-start space-x-3 p-4 rounded-xl border-2 cursor-pointer transition-all overflow-hidden ${
                                isRecommended ? 'border-accent/40 bg-gradient-to-br from-accent/5 to-transparent shadow-colored' : 
                                isSelected ? 'border-primary/40 bg-primary/5' : 
                                'border-border hover:border-accent/30 hover:shadow-lg'
                              }`}
                              onClick={() => handleToggleExpert(expert.id)}
                              data-testid={`expert-card-${expert.id}`}
                            >
                              {/* Selected gradient overlay */}
                              {isSelected && (
                                <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-accent/10 pointer-events-none" />
                              )}
                              
                              {/* Recommended glow */}
                              {isRecommended && (
                                <div className="absolute inset-0 bg-gradient-to-br from-accent/5 to-transparent opacity-50 group-hover:opacity-100 transition-opacity pointer-events-none" />
                              )}
                              
                              <Checkbox
                                checked={isSelected}
                                disabled={analyzeMutation.isPending}
                                data-testid={`checkbox-expert-${expert.id}`}
                                className="mt-1 z-10"
                              />
                              
                              {/* Avatar with conditional gradient */}
                              <div className="relative inline-block shrink-0">
                                {isSelected && (
                                  <div className="absolute inset-0 rounded-full bg-gradient-to-br from-accent to-primary opacity-75 blur-sm group-hover:opacity-100 transition-opacity" />
                                )}
                                <Avatar className={`relative h-12 w-12 transition-all ${
                                  isSelected ? 'ring-2 ring-accent/40 shadow-md shadow-accent/30' : 'ring-2 ring-accent/20'
                                }`}>
                                  <AvatarImage src={expert.avatar} alt={expert.name} className="object-cover" />
                                  <AvatarFallback className="text-xs font-semibold bg-accent/10 text-accent">
                                    {expert.name.split(' ').map(n => n[0]).join('').substring(0, 2)}
                                  </AvatarFallback>
                                </Avatar>
                              </div>
                              
                              <div className="flex-1 min-w-0 relative z-10">
                                <div className="flex items-center gap-2 mb-1">
                                  <Label className="font-semibold cursor-pointer">
                                    {expert.name}
                                  </Label>
                                  {isRecommended && (
                                    <motion.div
                                      initial={{ scale: 0 }}
                                      animate={{ scale: 1 }}
                                      transition={{ type: "spring", stiffness: 300 }}
                                    >
                                      <Badge className="text-xs px-2 py-0.5 bg-gradient-to-r from-accent to-primary text-white shadow-md shadow-accent/40">
                                        Recomendado
                                      </Badge>
                                    </motion.div>
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
                                <Badge variant="secondary" className="mt-2 text-xs">
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
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Button
              onClick={handleSubmit}
              disabled={
                !problem.trim() ||
                selectedExperts.length === 0 ||
                isAnalyzing
              }
              className="w-full h-14 rounded-xl bg-gradient-to-r from-primary to-accent hover:shadow-xl hover:shadow-primary/30 transition-all text-base font-semibold relative overflow-hidden group"
              size="lg"
              data-testid="button-analyze"
            >
              {!isAnalyzing && (
                <div className="absolute inset-0 shimmer" />
              )}
              <span className="relative z-10 flex items-center justify-center">
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
              </span>
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

        {/* Show results - fixed sidebar */}
        <div className="space-y-6 lg:sticky lg:top-8 lg:self-start">
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
                    <motion.div
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ duration: 0.4, type: "spring" }}
                    >
                      <Card className="rounded-2xl overflow-hidden border-2 border-primary/30 bg-gradient-to-br from-primary/10 via-card to-accent/10 shadow-xl shadow-primary/20">
                        <div className="relative">
                          {/* Decorative elements */}
                          <div className="absolute top-0 right-0 w-48 h-48 bg-gradient-to-br from-primary/20 to-transparent rounded-full blur-3xl" />
                          <div className="absolute bottom-0 left-0 w-32 h-32 bg-gradient-to-tr from-accent/20 to-transparent rounded-full blur-2xl" />
                          
                          <CardHeader className="pb-4 relative z-10">
                            <div className="flex items-center gap-3">
                              <motion.div
                                className="p-3 rounded-xl bg-gradient-to-br from-primary to-accent shadow-lg"
                                animate={{ rotate: [0, 5, -5, 0] }}
                                transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                              >
                                <Users className="w-6 h-6 text-white" />
                              </motion.div>
                              <div>
                                <CardTitle className="text-lg font-bold flex items-center gap-2">
                                  🎯 Consenso do Conselho
                                </CardTitle>
                                <CardDescription className="text-xs">
                                  Síntese estratégica de {analysis.contributions.length} lenda{analysis.contributions.length !== 1 ? 's' : ''} do marketing
                                </CardDescription>
                              </div>
                            </div>
                          </CardHeader>
                          <CardContent className="relative z-10">
                            <div className="bg-card/50 backdrop-blur-sm rounded-xl p-4 border border-primary/20">
                              <p className="text-sm text-foreground whitespace-pre-wrap leading-relaxed">
                                {analysis.consensus}
                              </p>
                            </div>
                          </CardContent>
                        </div>
                      </Card>
                    </motion.div>

                    <div className="space-y-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Sparkles className="h-5 w-5 text-accent" />
                        <h3 className="font-semibold text-base">Contribuições dos Especialistas</h3>
                      </div>
                      {analysis.contributions.map((contrib: { expertName: string; keyInsights: string[]; recommendations: string[] }, idx: number) => (
                        <motion.div
                          key={idx}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: idx * 0.1 }}
                          whileHover={{ x: 4 }}
                        >
                          <Card className="rounded-xl hover:shadow-lg hover:border-accent/30 transition-all group">
                            <CardHeader className="pb-3">
                              <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-accent/10 ring-1 ring-accent/20 group-hover:ring-accent/40 transition-all">
                                  <Brain className="h-4 w-4 text-accent" />
                                </div>
                                <CardTitle className="text-base font-semibold">
                                  {contrib.expertName}
                                </CardTitle>
                              </div>
                            </CardHeader>
                            <CardContent className="space-y-3">
                              {contrib.keyInsights.length > 0 && (
                                <div className="bg-muted/30 rounded-lg p-3">
                                  <p className="text-sm font-medium mb-2 flex items-center gap-2">
                                    <Lightbulb className="h-4 w-4 text-accent" />
                                    Principais Insights:
                                  </p>
                                  <ul className="text-sm text-muted-foreground space-y-2">
                                    {contrib.keyInsights.map((insight: string, i: number) => (
                                      <motion.li
                                        key={i}
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: i * 0.05 }}
                                        className="flex gap-2 items-start"
                                      >
                                        <span className="text-accent mt-0.5">•</span>
                                        <span>{insight}</span>
                                      </motion.li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                              {contrib.recommendations.length > 0 && (
                                <div className="bg-primary/5 rounded-lg p-3 border border-primary/20">
                                  <p className="text-sm font-medium mb-2 flex items-center gap-2">
                                    <TrendingUp className="h-4 w-4 text-primary" />
                                    Recomendações:
                                  </p>
                                  <ul className="text-sm text-muted-foreground space-y-2">
                                    {contrib.recommendations.map((rec: string, i: number) => (
                                      <motion.li
                                        key={i}
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: i * 0.05 }}
                                        className="flex gap-2 items-start"
                                      >
                                        <span className="text-primary mt-0.5">→</span>
                                        <span>{rec}</span>
                                      </motion.li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </CardContent>
                          </Card>
                        </motion.div>
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

      {/* CouncilAnimation Overlay */}
      {useStreaming && streamState.isStreaming && (
        <motion.div
          className="fixed inset-0 z-50 bg-background/95 backdrop-blur-sm overflow-y-auto"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <div className="container max-w-6xl mx-auto py-8 px-4 sm:px-6">
            <CouncilAnimation
              expertStatuses={streamState.expertStatusArray}
              activityFeed={streamState.activityFeed}
              isStreaming={streamState.isStreaming}
            />
          </div>
        </motion.div>
      )}
    </div>
  );
}
