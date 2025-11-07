import { useState, useEffect, useRef } from "react";
import { useParams } from "wouter";
import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, Send, Sparkles, Brain, Search, Users } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { motion, AnimatePresence } from "framer-motion";
import type { UserPersona } from "@shared/schema";
import { PersonaContextBadge } from "@/components/PersonaContextBadge";

// Helper: Detect if expert mentions colleague names
function detectColleagueMentions(content: string, allExpertNames: string[], currentExpert: string): string[] {
  const mentioned: string[] = [];
  const lowerContent = content.toLowerCase();
  
  for (const name of allExpertNames) {
    if (name === currentExpert) continue; // Don't count self-mentions
    
    // Check for first name or full name mentions
    const firstName = name.split(' ')[0];
    const patterns = [
      name.toLowerCase(),
      firstName.toLowerCase()
    ];
    
    if (patterns.some(p => lowerContent.includes(p))) {
      mentioned.push(name);
    }
  }
  
  return mentioned;
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
  citations: string[];
}

interface StreamContribution {
  expertName: string;
  content: string;
  order: number;
  isResearching?: boolean;
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  contributions?: StreamContribution[];
  createdAt: string;
}

export default function CouncilRoom() {
  const params = useParams() as { sessionId: string };
  const sessionId = params.sessionId;
  
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContributions, setStreamingContributions] = useState<StreamContribution[]>([]);
  const [streamingSynthesis, setStreamingSynthesis] = useState("");
  const [currentExpert, setCurrentExpert] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  
  // Load initial analysis
  const { data: analysis, isLoading: loadingAnalysis } = useQuery<CouncilAnalysis>({
    queryKey: ["/api/council/analyses", sessionId],
    queryFn: async () => {
      const response = await apiRequest(`/api/council/analyses/${sessionId}`);
      return response.json();
    },
  });
  
  // Load chat history
  const { data: history = [], isLoading: loadingHistory, refetch: refetchHistory } = useQuery<ChatMessage[]>({
    queryKey: ["/api/council/chat", sessionId, "messages"],
    queryFn: async () => {
      const response = await apiRequest(`/api/council/chat/${sessionId}/messages`);
      return response.json();
    },
  });

  // Load user persona for context display
  const { data: persona } = useQuery<UserPersona | null>({
    queryKey: ["/api/persona/current"],
  });
  
  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContributions]);
  
  // Sync history with local messages
  useEffect(() => {
    if (history.length > 0) {
      setMessages(history);
    }
  }, [history]);
  
  const handleSendMessage = async () => {
    if (!question.trim() || isStreaming) return;
    
    // Add user message optimistically
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: question.trim(),
      createdAt: new Date().toISOString(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setQuestion("");
    setIsStreaming(true);
    setStreamingContributions([]);
    setStreamingSynthesis("");
    setCurrentExpert(null);
    
    // Start SSE stream
    const eventSource = new EventSource(
      `/api/council/chat/${sessionId}/stream?message=${encodeURIComponent(question.trim())}`
    );
    
    eventSourceRef.current = eventSource;
    
    eventSource.addEventListener("user_message", (event) => {
      const data = JSON.parse(event.data);
    });
    
    eventSource.addEventListener("expert_thinking", (event) => {
      const data = JSON.parse(event.data);
      setCurrentExpert(data.expertName);
    });
    
    eventSource.addEventListener("contribution", (event) => {
      const data = JSON.parse(event.data);
      setStreamingContributions(prev => [
        ...prev,
        {
          expertName: data.expertName,
          content: data.content,
          order: data.order,
        },
      ]);
      setCurrentExpert(null);
    });
    
    eventSource.addEventListener("synthesizing", () => {
      setCurrentExpert("Sintetizando consenso...");
    });
    
    eventSource.addEventListener("synthesis", (event) => {
      const data = JSON.parse(event.data);
      setStreamingSynthesis(data.content);
      setCurrentExpert(null);
    });
    
    eventSource.addEventListener("complete", () => {
      eventSource.close();
      setIsStreaming(false);
      
      // Refetch history to get saved messages
      refetchHistory();
      
      // Clear streaming state
      setStreamingContributions([]);
      setStreamingSynthesis("");
    });
    
    eventSource.addEventListener("error", (event) => {
      console.error("SSE Error:", event);
      eventSource.close();
      setIsStreaming(false);
      setCurrentExpert(null);
    });
    
    eventSource.onerror = () => {
      eventSource.close();
      setIsStreaming(false);
    };
  };
  
  const expertAvatars = analysis?.contributions.map(c => ({
    name: c.expertName,
    avatar: `/api/experts/${c.expertId}/avatar`,
  })) || [];
  
  const getExpertInitials = (name: string) => {
    return name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2);
  };
  
  if (loadingAnalysis) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }
  
  if (!analysis) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle>Sessão não encontrada</CardTitle>
            <CardDescription>
              Não foi possível carregar a análise do conselho.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }
  
  return (
    <motion.div 
      className="flex flex-col h-screen"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.24, ease: [0.16, 1, 0.3, 1] }}
    >
      {/* Header with Expert Avatars */}
      <motion.div 
        className="border-b bg-card/50 backdrop-blur-sm"
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.26, delay: 0.05, ease: [0.16, 1, 0.3, 1] }}
      >
        <div className="container max-w-6xl mx-auto px-4 p-3 sm:p-4">
          <div className="flex items-center justify-between gap-3 sm:gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 sm:gap-3 flex-wrap">
                <h1 className="text-lg sm:text-xl md:text-2xl font-semibold flex items-center gap-2">
                  <Brain className="h-5 w-5 sm:h-6 sm:w-6 text-primary" />
                  <span className="hidden sm:inline">Sala do Conselho</span>
                  <span className="sm:hidden">Conselho</span>
                </h1>
                <PersonaContextBadge persona={persona || null} />
              </div>
              <p className="text-xs sm:text-sm text-muted-foreground mt-1 hidden sm:block">
                Continue a conversa com os especialistas
              </p>
            </div>
            
            {/* Expert Avatars - Horizontal scroll on mobile */}
            <div className="flex items-center gap-1.5 sm:gap-2 overflow-x-auto max-w-[40%] sm:max-w-none scrollbar-hide">
              {expertAvatars.map((expert, idx) => (
                <motion.div
                  key={idx}
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ duration: 0.24, delay: 0.1 + idx * 0.035, ease: [0.34, 1.56, 0.64, 1] }}
                  className={`relative transition-all duration-200 flex-shrink-0 ${
                    currentExpert === expert.name ? "ring-2 ring-primary ring-offset-2 scale-110" : "scale-100"
                  }`}
                  data-testid={`avatar-${expert.name.toLowerCase().replace(/\s+/g, "-")}`}
                >
                  <Avatar className="h-8 w-8 sm:h-10 sm:w-10">
                    <AvatarImage src={expert.avatar} alt={expert.name} />
                    <AvatarFallback className="text-xs">{getExpertInitials(expert.name)}</AvatarFallback>
                  </Avatar>
                  {currentExpert === expert.name && (
                    <motion.div 
                      className="absolute -bottom-1 -right-1 bg-primary rounded-full p-1"
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ duration: 0.18, ease: "backOut" }}
                    >
                      <Loader2 className="h-2.5 w-2.5 sm:h-3 sm:w-3 animate-spin text-primary-foreground" />
                    </motion.div>
                  )}
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </motion.div>
      
      {/* Messages Area */}
      <ScrollArea className="flex-1">
        <div className="container max-w-4xl mx-auto px-3 sm:px-4 py-4 sm:py-6 space-y-4 sm:space-y-6">
          {/* Initial Analysis Summary */}
          <Card className="border-primary/20 bg-primary/5" data-testid="card-initial-analysis">
            <CardHeader className="p-4 sm:p-5 md:p-6">
              <CardTitle className="flex items-center gap-2 text-base sm:text-lg">
                <Sparkles className="h-4 w-4 sm:h-5 sm:w-5 text-primary" />
                Análise Inicial
              </CardTitle>
              <CardDescription className="text-xs sm:text-sm">
                {analysis.problem}
              </CardDescription>
            </CardHeader>
            <CardContent className="p-4 sm:p-5 md:p-6 pt-0">
              <div className="prose prose-sm dark:prose-invert max-w-none text-sm sm:text-base">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {analysis.consensus}
                </ReactMarkdown>
              </div>
            </CardContent>
          </Card>
          
          <Separator />
          
          {/* Chat Messages */}
          {messages.map((msg, idx) => (
            <div key={msg.id || idx} data-testid={`message-${msg.role}-${idx}`}>
              {msg.role === "user" ? (
                <div className="flex justify-end">
                  <Card className="max-w-2xl bg-muted">
                    <CardContent className="pt-4">
                      <p className="text-foreground">{msg.content}</p>
                    </CardContent>
                  </Card>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Expert Contributions */}
                  {msg.contributions?.map((contrib, cIdx) => {
                    const allExpertNames = msg.contributions?.map(c => c.expertName) || [];
                    const mentionedColleagues = detectColleagueMentions(contrib.content, allExpertNames, contrib.expertName);
                    
                    return (
                      <motion.div
                        key={cIdx}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ 
                          duration: 0.26, 
                          delay: cIdx * 0.06,
                          ease: [0.16, 1, 0.3, 1]
                        }}
                        data-testid={`contribution-${contrib.expertName.toLowerCase().replace(/\s+/g, "-")}`}
                      >
                        <Card>
                          <CardHeader>
                            <div className="flex items-center gap-2 flex-wrap">
                              <Badge variant="secondary">{contrib.expertName}</Badge>
                              {mentionedColleagues.length > 0 && (
                                <Badge variant="outline" className="text-xs gap-1">
                                  <Users className="w-3 h-3" />
                                  Dialoga com {mentionedColleagues.length === 1 ? mentionedColleagues[0].split(' ')[0] : `${mentionedColleagues.length} colegas`}
                                </Badge>
                              )}
                            </div>
                          </CardHeader>
                          <CardContent>
                            <div className="prose prose-sm dark:prose-invert max-w-none text-foreground">
                              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {contrib.content}
                              </ReactMarkdown>
                            </div>
                          </CardContent>
                        </Card>
                      </motion.div>
                    );
                  })}
                  
                  {/* Synthesis - Enhanced Visual */}
                  <Card className="border-primary/30 bg-primary/10" data-testid="card-synthesis">
                    <CardHeader>
                      <CardTitle className="text-base flex items-center gap-2">
                        <Users className="w-5 h-5 text-primary" />
                        🎯 Consenso da Mesa
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="prose prose-sm dark:prose-invert max-w-none text-foreground">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}
            </div>
          ))}
          
          {/* Streaming Contributions */}
          <AnimatePresence>
            {streamingContributions.map((contrib, idx) => {
              const allStreamingNames = streamingContributions.map(c => c.expertName);
              const mentionedColleagues = detectColleagueMentions(contrib.content, allStreamingNames, contrib.expertName);
              
              return (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ 
                    duration: 0.26,
                    ease: [0.16, 1, 0.3, 1]
                  }}
                  data-testid={`streaming-contribution-${idx}`}
                >
                  <Card>
                    <CardHeader>
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge variant="secondary">{contrib.expertName}</Badge>
                        {mentionedColleagues.length > 0 && (
                          <Badge variant="outline" className="text-xs gap-1">
                            <Users className="w-3 h-3" />
                            Dialoga com {mentionedColleagues.length === 1 ? mentionedColleagues[0].split(' ')[0] : `${mentionedColleagues.length} colegas`}
                          </Badge>
                        )}
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="prose prose-sm dark:prose-invert max-w-none text-foreground">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {contrib.content}
                        </ReactMarkdown>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
            
            {streamingSynthesis && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                data-testid="streaming-synthesis"
              >
                <Card className="border-primary/30 bg-primary/10">
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <Users className="w-5 h-5 text-primary" />
                      🎯 Consenso da Mesa
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="prose prose-sm dark:prose-invert max-w-none text-foreground">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {streamingSynthesis}
                      </ReactMarkdown>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}
            
            {currentExpert && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.3 }}
                data-testid="expert-thinking-indicator"
              >
                <Card className="border-primary/30 bg-primary/5">
                  <CardContent className="py-3">
                    <div className="flex items-center gap-3">
                      {currentExpert.includes("Sintetizando") ? (
                        <Brain className="h-5 w-5 text-primary animate-pulse" />
                      ) : (
                        <Search className="h-5 w-5 text-primary animate-pulse" />
                      )}
                      <div className="flex items-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin text-primary" />
                        <span className="text-sm font-medium text-foreground">
                          {currentExpert.includes("Sintetizando") 
                            ? currentExpert 
                            : `${currentExpert} pesquisando e analisando...`
                          }
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>
          
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>
      
      {/* Input Area */}
      <div className="border-t bg-card/50 backdrop-blur-sm">
        <div className="container max-w-4xl mx-auto px-3 sm:px-4 py-3 sm:py-4">
          <div className="flex gap-2">
            <Textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Faça uma pergunta ao conselho..."
              className="min-h-[56px] sm:min-h-[60px] resize-none text-sm sm:text-base"
              disabled={isStreaming}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              data-testid="input-question"
            />
            <Button
              onClick={handleSendMessage}
              disabled={!question.trim() || isStreaming}
              size="icon"
              className="h-[56px] w-[56px] sm:h-[60px] sm:w-[60px]"
              data-testid="button-send"
            >
              {isStreaming ? (
                <Loader2 className="h-4 w-4 sm:h-5 sm:w-5 animate-spin" />
              ) : (
                <Send className="h-4 w-4 sm:h-5 sm:w-5" />
              )}
            </Button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
