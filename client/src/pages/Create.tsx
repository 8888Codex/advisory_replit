import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useLocation } from "wouter";
import { apiRequestJson } from "@/lib/queryClient";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { AnimatedPage } from "@/components/AnimatedPage";
import { Sparkles, Loader2, Brain, Search, Wand2, Check, MessageSquare, Send, Image } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import type { Expert } from "@shared/schema";
import { motion, AnimatePresence } from "framer-motion";

type CloneStep = "idle" | "researching" | "analyzing" | "synthesizing" | "avatar-generation" | "generating-samples" | "complete";

interface TestMessage {
  role: "user" | "assistant";
  content: string;
}

interface SampleConversation {
  question: string;
  answer: string;
  wordCount: number;
}

export default function Create() {
  const [, setLocation] = useLocation();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  // Auto-clone form state
  const [targetName, setTargetName] = useState("");
  const [context, setContext] = useState("");
  const [cloneStep, setCloneStep] = useState<CloneStep>("idle");
  const [generatedExpert, setGeneratedExpert] = useState<any | null>(null); // ExpertCreate data, not persisted yet
  
  // Sample conversations state (Disney Effect #1)
  const [sampleConversations, setSampleConversations] = useState<SampleConversation[]>([]);
  const [generatingSamples, setGeneratingSamples] = useState(false);
  
  // Test chat state
  const [showTestChat, setShowTestChat] = useState(false);
  const [testMessages, setTestMessages] = useState<TestMessage[]>([]);
  const [testInput, setTestInput] = useState("");

  const autoCloneMutation = useMutation({
    mutationFn: async (data: { targetName: string; context?: string }) => {
      // Disney Effect #2: Use SSE streaming for real-time progress
      return new Promise((resolve, reject) => {
        const eventSource = new EventSource(
          `/api/experts/auto-clone-stream?targetName=${encodeURIComponent(data.targetName)}&context=${encodeURIComponent(data.context || "")}`
        );
        
        let expertData: any = null;
        
        eventSource.addEventListener("step-start", (e) => {
          const eventData = JSON.parse(e.data);
          setCloneStep(eventData.step);
        });
        
        eventSource.addEventListener("step-progress", (e) => {
          const eventData = JSON.parse(e.data);
          // Could show detailed progress here in future
          console.log("[SSE]", eventData.message);
        });
        
        eventSource.addEventListener("step-complete", (e) => {
          const eventData = JSON.parse(e.data);
          console.log("[SSE] ✅", eventData.message);
        });
        
        eventSource.addEventListener("expert-complete", (e) => {
          const eventData = JSON.parse(e.data);
          expertData = eventData.expert;
          eventSource.close();
          resolve(expertData);
        });
        
        eventSource.addEventListener("error", (e: any) => {
          const eventData = e.data ? JSON.parse(e.data) : { message: "Unknown error" };
          eventSource.close();
          reject(new Error(eventData.message || "Erro durante clonagem"));
        });
        
        eventSource.onerror = () => {
          eventSource.close();
          reject(new Error("Conexão perdida com servidor"));
        };
      });
    },
    onSuccess: async (expertData) => {
      setGeneratedExpert(expertData);
      
      // Disney Effect #1: Generate sample conversations automatically
      setCloneStep("generating-samples");
      setGeneratingSamples(true);
      
      try {
        const samplesData = await apiRequestJson<{ samples: SampleConversation[] }>("/api/experts/generate-samples", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            systemPrompt: expertData.systemPrompt,
            expertName: expertData.name,
            userChallenge: context.trim() || ""
          }),
        });
        
        setSampleConversations(samplesData.samples);
        setCloneStep("complete");
        
        toast({
          title: "Clone Cognitivo Completo",
          description: `${expertData.name} está pronto! Veja os exemplos de conversa abaixo.`,
        });
      } catch (error) {
        console.error("Error generating samples:", error);
        setCloneStep("complete");
        
        toast({
          title: "Clone Criado",
          description: `${expertData.name} foi criado, mas não foi possível gerar amostras.`,
        });
      } finally {
        setGeneratingSamples(false);
      }
    },
    onError: (error: any) => {
      setCloneStep("idle");
      
      const errorMessage = error?.message || "Tente novamente mais tarde.";
      
      toast({
        title: "Erro ao criar clone",
        description: errorMessage,
        variant: "destructive",
      });
    },
  });

  const handleAutoClone = (e: React.FormEvent) => {
    e.preventDefault();
    autoCloneMutation.mutate({ 
      targetName, 
      context: context.trim() || undefined 
    });
  };

  const saveExpertMutation = useMutation({
    mutationFn: async (expertData: any) => {
      return await apiRequestJson<Expert>("/api/experts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(expertData),
      });
    },
    onSuccess: (expert) => {
      queryClient.invalidateQueries({ queryKey: ["/api/experts"] });
      setLocation("/");
      toast({
        title: "Especialista Salvo",
        description: `${expert.name} está pronto para consultas.`,
      });
    },
    onError: () => {
      toast({
        title: "Erro ao salvar",
        description: "Não foi possível salvar o especialista.",
        variant: "destructive",
      });
    },
  });

  const handleSaveExpert = () => {
    if (generatedExpert) {
      saveExpertMutation.mutate(generatedExpert);
    }
  };

  const handleRegenerate = () => {
    setGeneratedExpert(null);
    setCloneStep("idle");
    setSampleConversations([]);
    setShowTestChat(false);
    setTestMessages([]);
    autoCloneMutation.reset();
  };

  const testChatMutation = useMutation({
    mutationFn: async (message: string) => {
      if (!generatedExpert) throw new Error("No expert to test");
      
      // For testing, we'll use Claude directly with the generated system prompt
      // This avoids persisting temporary conversations
      const response = await apiRequestJson<{ response: string }>("/api/experts/test-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          systemPrompt: generatedExpert.systemPrompt,
          message: message,
          history: testMessages
        }),
      });
      
      return response.response;
    },
    onSuccess: (response) => {
      setTestMessages((prev) => [
        ...prev,
        { role: "assistant", content: response }
      ]);
    },
    onError: () => {
      toast({
        title: "Erro no chat de teste",
        description: "Tente novamente.",
        variant: "destructive",
      });
    },
  });

  const handleTestSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!testInput.trim()) return;
    
    const userMessage = testInput.trim();
    setTestMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setTestInput("");
    testChatMutation.mutate(userMessage);
  };

  const initials = generatedExpert
    ? generatedExpert.name
        .split(" ")
        .map((n: string) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "??";

  const getStepIcon = (step: CloneStep) => {
    switch (step) {
      case "researching":
        return <Search className="h-4 w-4" />;
      case "analyzing":
        return <Brain className="h-4 w-4" />;
      case "synthesizing":
        return <Wand2 className="h-4 w-4" />;
      case "avatar-generation":
        return <Image className="h-4 w-4" />;
      case "generating-samples":
        return <MessageSquare className="h-4 w-4" />;
      case "complete":
        return <Check className="h-4 w-4" />;
      default:
        return null;
    }
  };

  const getStepText = (step: CloneStep) => {
    switch (step) {
      case "researching":
        return "Pesquisando biografia, filosofia e métodos...";
      case "analyzing":
        return "Analisando padrões cognitivos e expertise...";
      case "synthesizing":
        return "Sintetizando clone de alta fidelidade...";
      case "avatar-generation":
        return "🎨 Gerando avatar profissional...";
      case "generating-samples":
        return "✨ Gerando amostras de conversa para preview...";
      case "complete":
        return "Clone cognitivo pronto!";
      default:
        return "";
    }
  };

  const isProcessing = ["researching", "analyzing", "synthesizing", "avatar-generation", "generating-samples"].includes(cloneStep);

  return (
    <AnimatedPage>
      <div className="min-h-screen py-12">
      <div className="container mx-auto px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="mb-8">
            <div className="inline-flex items-center gap-2 rounded-full bg-muted px-4 py-1.5 text-sm mb-4">
              <Sparkles className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">Clonagem Cognitiva Automática</span>
            </div>
            <h1 className="text-4xl font-semibold mb-3 tracking-tight">Criar Seu Especialista</h1>
            <p className="text-muted-foreground max-w-2xl leading-relaxed">
              Digite o nome de quem você quer clonar. Nosso sistema pesquisa automaticamente 
              e cria um clone cognitivo de alta fidelidade usando Framework EXTRACT.
            </p>
          </div>

          {!generatedExpert && (
            <Card className="p-8 rounded-2xl">
              <form onSubmit={handleAutoClone} className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="targetName" className="text-sm font-medium">Quem você quer clonar?</Label>
                  <Input
                    id="targetName"
                    value={targetName}
                    onChange={(e) => setTargetName(e.target.value)}
                    placeholder="Ex: Steve Jobs, Elon Musk, Warren Buffett..."
                    required
                    disabled={isProcessing}
                    data-testid="input-target-name"
                    className="text-base"
                  />
                  <p className="text-sm text-muted-foreground">
                    Pode ser qualquer pessoa pública com informação disponível online
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="context" className="text-sm font-medium">Contexto Adicional (Opcional)</Label>
                  <Textarea
                    id="context"
                    value={context}
                    onChange={(e) => setContext(e.target.value)}
                    placeholder="Ex: fundador da Apple, foco em design e inovação..."
                    rows={3}
                    disabled={isProcessing}
                    data-testid="input-context"
                    className="resize-none"
                  />
                  <p className="text-sm text-muted-foreground">
                    Adicione contexto para refinar a pesquisa
                  </p>
                </div>

                {/* Disney Effect #2: Real-time animated progress */}
                <AnimatePresence mode="wait">
                  {isProcessing && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      transition={{ duration: 0.3 }}
                    >
                      <Card className="p-6 rounded-2xl bg-gradient-to-br from-accent/5 via-background to-background border-accent/20">
                        <div className="flex items-center gap-4 mb-4">
                          <motion.div
                            className="text-accent flex-shrink-0"
                            animate={{ rotate: cloneStep === "synthesizing" ? 360 : 0 }}
                            transition={{ duration: 2, repeat: cloneStep === "synthesizing" ? Infinity : 0, ease: "linear" }}
                          >
                            {getStepIcon(cloneStep)}
                          </motion.div>
                          <div className="flex-1 min-w-0">
                            <motion.p
                              key={cloneStep}
                              initial={{ opacity: 0, x: -10 }}
                              animate={{ opacity: 1, x: 0 }}
                              className="text-sm font-semibold mb-2"
                            >
                              {getStepText(cloneStep)}
                            </motion.p>
                            <div className="w-full bg-background rounded-full h-2 overflow-hidden">
                              <motion.div
                                className="bg-accent h-2 rounded-full"
                                initial={{ width: "0%" }}
                                animate={{
                                  width: cloneStep === "researching" ? "20%" :
                                         cloneStep === "analyzing" ? "40%" :
                                         cloneStep === "synthesizing" ? "60%" :
                                         cloneStep === "avatar-generation" ? "80%" :
                                         cloneStep === "generating-samples" ? "95%" : "0%"
                                }}
                                transition={{ duration: 0.5, ease: "easeOut" }}
                              />
                            </div>
                          </div>
                        </div>
                        
                        {/* Individual step indicators */}
                        <div className="grid grid-cols-5 gap-2 mt-4">
                          {["researching", "analyzing", "synthesizing", "avatar-generation", "generating-samples"].map((step, index) => {
                            const stepNumber = index + 1;
                            const isActive = cloneStep === step;
                            const isComplete = 
                              (step === "researching" && ["analyzing", "synthesizing", "avatar-generation", "generating-samples", "complete"].includes(cloneStep)) ||
                              (step === "analyzing" && ["synthesizing", "avatar-generation", "generating-samples", "complete"].includes(cloneStep)) ||
                              (step === "synthesizing" && ["avatar-generation", "generating-samples", "complete"].includes(cloneStep)) ||
                              (step === "avatar-generation" && ["generating-samples", "complete"].includes(cloneStep)) ||
                              (step === "generating-samples" && cloneStep === "complete");
                            
                            return (
                              <motion.div
                                key={step}
                                className={`text-xs p-2 rounded-xl text-center transition-colors ${
                                  isActive ? "bg-accent text-accent-foreground font-semibold" :
                                  isComplete ? "bg-muted/50 text-muted-foreground line-through" :
                                  "bg-muted/30 text-muted-foreground"
                                }`}
                                initial={{ scale: 0.9, opacity: 0 }}
                                animate={{ scale: isActive ? 1.05 : 1, opacity: 1 }}
                                transition={{ delay: index * 0.1 }}
                              >
                                {step === "researching" && "🔍 Pesquisa"}
                                {step === "analyzing" && "🧠 Análise"}
                                {step === "synthesizing" && "✨ Síntese"}
                                {step === "avatar-generation" && "🎨 Avatar"}
                                {step === "generating-samples" && "💬 Amostras"}
                              </motion.div>
                            );
                          })}
                        </div>
                      </Card>
                    </motion.div>
                  )}
                </AnimatePresence>

                <Button 
                  type="submit" 
                  className="w-full gap-2" 
                  size="lg" 
                  disabled={isProcessing}
                  data-testid="button-auto-clone"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Criando Clone Cognitivo...
                    </>
                  ) : (
                    <>
                      <Brain className="h-4 w-4" />
                      Criar Clone Automático
                    </>
                  )}
                </Button>
              </form>
            </Card>
          )}

          {generatedExpert && cloneStep === "complete" && (
            <div className="space-y-6">
              <Card className="p-8 rounded-2xl hover-elevate transition-all duration-200">
                <div className="flex items-center gap-2 text-muted-foreground mb-6">
                  <Check className="h-5 w-5" />
                  <h3 className="text-lg font-medium">Clone Cognitivo Gerado com Sucesso!</h3>
                </div>

                <div className="space-y-6">
                  <div className="flex items-start gap-6">
                    <Avatar className="h-24 w-24 ring-1 ring-border/50">
                      {generatedExpert.avatar && (
                        <AvatarImage 
                          src={`/attached_assets/${generatedExpert.avatar}`} 
                          alt={generatedExpert.name}
                          className="object-cover"
                        />
                      )}
                      <AvatarFallback className="text-xl font-medium">{initials}</AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-2xl font-semibold mb-2 tracking-tight">{generatedExpert.name}</h3>
                      <p className="text-muted-foreground mb-4 leading-relaxed">{generatedExpert.title}</p>
                      
                      {generatedExpert.expertise && generatedExpert.expertise.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                          {generatedExpert.expertise.map((skill: string, index: number) => (
                            <Badge key={index} variant="secondary" className="font-normal">
                              {skill}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {generatedExpert.bio}
                  </p>

                  <details className="group">
                    <summary className="cursor-pointer text-sm font-medium text-foreground hover-elevate active-elevate-2 p-4 rounded-xl transition-all duration-200">
                      Ver System Prompt EXTRACT Completo
                    </summary>
                    <Card className="mt-3 p-6 bg-muted/30 rounded-2xl">
                      <pre className="text-xs whitespace-pre-wrap font-mono overflow-x-auto leading-relaxed">
                        {generatedExpert.systemPrompt}
                      </pre>
                    </Card>
                  </details>
                </div>
              </Card>

              {/* Disney Effect #1: Sample Conversations */}
              {sampleConversations.length > 0 && (
                <Card className="p-8 rounded-2xl bg-gradient-to-br from-accent/5 via-background to-background">
                  <div className="flex items-center gap-2 mb-6">
                    <Sparkles className="h-5 w-5 text-accent" />
                    <h3 className="text-lg font-semibold">Veja {generatedExpert.name} em Ação</h3>
                  </div>
                  <p className="text-sm text-muted-foreground mb-6 leading-relaxed">
                    Exemplos reais de como este especialista pensa e se comunica:
                  </p>
                  
                  <div className="space-y-4">
                    {sampleConversations.map((sample, index) => (
                      <div 
                        key={index} 
                        className="rounded-2xl border border-border/50 overflow-hidden hover-elevate transition-all duration-200"
                        data-testid={`sample-conversation-${index}`}
                      >
                        <div className="bg-muted/50 px-4 py-3 border-b border-border/50">
                          <p className="text-sm font-medium text-foreground flex items-center gap-2">
                            <MessageSquare className="h-4 w-4 text-muted-foreground" />
                            {sample.question}
                          </p>
                        </div>
                        <div className="p-4 bg-background">
                          <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                            {sample.answer}
                          </p>
                          <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border/50">
                            <Badge variant="secondary" className="text-xs font-normal">
                              {sample.wordCount} palavras
                            </Badge>
                            <Badge variant="secondary" className="text-xs font-normal">
                              Amostra {index + 1}/3
                            </Badge>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  <div className="mt-6 p-4 rounded-xl bg-accent/10 border border-accent/20">
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      ✨ <strong className="text-foreground">Efeito Disney:</strong> Estas respostas foram geradas automaticamente 
                      usando o sistema cognitivo do especialista. Você está vendo a autenticidade em tempo real!
                    </p>
                  </div>
                </Card>
              )}

              <Card className="p-6 rounded-2xl">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-2">
                    <MessageSquare className="h-5 w-5 text-muted-foreground" />
                    <h3 className="text-lg font-medium">Testar Clone</h3>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowTestChat(!showTestChat)}
                    data-testid="button-toggle-test-chat"
                  >
                    {showTestChat ? "Ocultar" : "Mostrar"} Chat
                  </Button>
                </div>

                {showTestChat && (
                  <div className="space-y-4">
                    <div className="border border-border/50 rounded-2xl p-4 space-y-3 min-h-[200px] max-h-[400px] overflow-y-auto">
                      {testMessages.length === 0 ? (
                        <p className="text-sm text-muted-foreground text-center py-12 leading-relaxed">
                          Faça uma pergunta para testar a personalidade do clone
                        </p>
                      ) : (
                        testMessages.map((msg, index) => (
                          <div
                            key={index}
                            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                          >
                            <div
                              className={`max-w-[80%] rounded-2xl p-4 transition-all duration-200 ${
                                msg.role === "user"
                                  ? "bg-accent text-accent-foreground"
                                  : "bg-muted"
                              }`}
                            >
                              <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                            </div>
                          </div>
                        ))
                      )}
                      {testChatMutation.isPending && (
                        <div className="flex justify-start">
                          <div className="bg-muted rounded-2xl p-4">
                            <Loader2 className="h-4 w-4 animate-spin" />
                          </div>
                        </div>
                      )}
                    </div>

                    <form onSubmit={handleTestSend} className="flex gap-3">
                      <Input
                        value={testInput}
                        onChange={(e) => setTestInput(e.target.value)}
                        placeholder="Digite sua pergunta..."
                        disabled={testChatMutation.isPending}
                        data-testid="input-test-message"
                        className="flex-1"
                      />
                      <Button
                        type="submit"
                        size="icon"
                        disabled={testChatMutation.isPending || !testInput.trim()}
                        data-testid="button-send-test-message"
                      >
                        <Send className="h-4 w-4" />
                      </Button>
                    </form>
                  </div>
                )}
              </Card>

              <div className="flex gap-4">
                <Button 
                  onClick={handleSaveExpert}
                  size="lg"
                  className="flex-1 gap-2"
                  disabled={saveExpertMutation.isPending}
                  data-testid="button-save-expert"
                >
                  {saveExpertMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Salvando...
                    </>
                  ) : (
                    <>
                      <Check className="h-4 w-4" />
                      Salvar Especialista
                    </>
                  )}
                </Button>
                <Button 
                  onClick={handleRegenerate}
                  variant="outline"
                  size="lg"
                  className="gap-2"
                  data-testid="button-regenerate"
                >
                  <Wand2 className="h-4 w-4" />
                  Regenerar
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
    </AnimatedPage>
  );
}
