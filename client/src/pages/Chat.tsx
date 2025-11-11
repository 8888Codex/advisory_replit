import { useState, useEffect } from "react";
import { useRoute, useLocation } from "wouter";
import { useQuery, useMutation } from "@tanstack/react-query";
import { queryClient, apiRequestJson } from "@/lib/queryClient";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AnimatedPage } from "@/components/AnimatedPage";
import { ArrowLeft, Send, Sparkles, Loader2 } from "lucide-react";
import { ChatMessage } from "@/components/ChatMessage";
import { useToast } from "@/hooks/use-toast";
import { motion } from "framer-motion";
import type { Expert, Conversation, Message, UserPersona } from "@shared/schema";
import { ChatLoadingSkeleton } from "@/components/skeletons/ChatMessageSkeleton";
import { PulseLoader } from "@/components/PulseLoader";
import { PersonaContextBadge } from "@/components/PersonaContextBadge";

export default function Chat() {
  const [location, params] = useRoute("/chat/:id");
  const [, setLocation] = useLocation();
  const { toast } = useToast();
  const expertId = params?.id || "";
  
  // Check for conversationId in URL query string (for resuming conversations)
  const urlParams = new URLSearchParams(window.location.search);
  const resumeConversationId = urlParams.get('conversationId');
  
  const [conversationId, setConversationId] = useState<string | null>(resumeConversationId);
  const [input, setInput] = useState("");

  const { data: expert, isLoading: expertLoading } = useQuery<Expert>({
    queryKey: ["/api/experts", expertId],
    enabled: !!expertId,
  });

  const { data: messages = [], isLoading: messagesLoading } = useQuery<Message[]>({
    queryKey: ["/api/conversations", conversationId, "messages"],
    enabled: !!conversationId,
  });

  const { data: persona } = useQuery<UserPersona | null>({
    queryKey: ["/api/persona/current"],
  });

  const createConversationMutation = useMutation({
    mutationFn: async (data: { expertId: string; title: string }) => {
      return await apiRequestJson<Conversation>("/api/conversations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
    },
    onSuccess: (conversation) => {
      setConversationId(conversation.id);
    },
    onError: (error) => {
      console.error("[Chat] Error creating conversation:", error);
      toast({
        variant: "destructive",
        title: "Erro ao criar conversa",
        description: error instanceof Error ? error.message : "Não foi possível iniciar a conversa com o especialista.",
      });
    },
  });

  const sendMessageMutation = useMutation({
    mutationFn: async (data: { conversationId: string; content: string }) => {
      return await apiRequestJson<{ userMessage: Message; assistantMessage: Message }>(
        `/api/conversations/${data.conversationId}/messages`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content: data.content }),
        }
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/conversations", conversationId, "messages"] });
      setInput("");
    },
    onError: () => {
      toast({
        variant: "destructive",
        title: "Erro ao enviar mensagem",
        description: "Não foi possível processar sua mensagem. Tente novamente.",
      });
    },
  });

  useEffect(() => {
    // Only create new conversation if:
    // 1. Expert is loaded
    // 2. No conversationId exists (not resuming)
    // 3. Not already creating
    if (expert && !conversationId && !createConversationMutation.isPending) {
      createConversationMutation.mutate({
        expertId: expert.id,
        title: `Conversa com ${expert.name}`,
      });
    }
  }, [expert, conversationId, createConversationMutation.isPending]);

  const handleSend = () => {
    if (!input.trim() || !conversationId) return;
    sendMessageMutation.mutate({ conversationId, content: input });
  };

  // Fetch personalized suggested questions
  const { data: suggestedQuestionsData } = useQuery<{
    expertId: string;
    expertName: string;
    questions: string[];
    personalized: boolean;
  }>({
    queryKey: ["/api/experts", expertId, "suggested-questions"],
    enabled: !!expertId,
  });

  const handleSuggestedQuestion = (question: string) => {
    setInput(question);
  };

  const suggestedQuestions = suggestedQuestionsData?.questions || [];

  if (expertLoading) {
    return (
      <AnimatedPage>
        <div className="h-[calc(100vh-4rem)] flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </AnimatedPage>
    );
  }

  if (!expert) {
    return (
      <AnimatedPage>
        <div className="h-[calc(100vh-4rem)] flex items-center justify-center">
          <p className="text-muted-foreground">Especialista não encontrado</p>
        </div>
      </AnimatedPage>
    );
  }

  const initials = expert.name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  return (
    <AnimatedPage>
      <div className="flex flex-col h-screen">
      <div className="flex-shrink-0 border-b bg-card">
        <div className="container mx-auto px-4 p-3 sm:p-4">
          <div className="flex items-center gap-3 sm:gap-4">
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={() => setLocation("/experts")}
              data-testid="button-back"
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <Avatar className="h-10 w-10 sm:h-12 sm:w-12 ring-2 ring-accent/20">
              <AvatarImage src={expert.avatar || undefined} alt={expert.name} />
              <AvatarFallback>{initials}</AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h2 className="text-base sm:text-lg font-semibold truncate">{expert.name}</h2>
                <PersonaContextBadge persona={persona || null} compact />
              </div>
              <p className="text-xs sm:text-sm text-muted-foreground truncate">{expert.title}</p>
            </div>
            <div className="hidden md:flex gap-2">
              {expert.expertise.slice(0, 3).map((skill, index) => (
                <Badge key={index} variant="secondary" className="text-xs">
                  {skill}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3 sm:p-4 md:p-6 pb-6 space-y-4 min-h-0">
        {messagesLoading ? (
          <ChatLoadingSkeleton />
        ) : (
          <>
            <ChatMessage
              message={{
                id: "welcome",
                role: "assistant",
                content: `Olá! Sou ${expert.name}, ${expert.title}. Como posso ajudá-lo hoje com seus desafios estratégicos?`,
                timestamp: new Date(),
              }}
              expertName={expert.name}
              expertAvatar={expert.avatar || undefined}
            />
            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                message={{
                  id: message.id,
                  role: message.role as "user" | "assistant",
                  content: message.content,
                  timestamp: message.createdAt,
                }}
                expertName={expert.name}
                expertAvatar={expert.avatar || undefined}
              />
            ))}
            {sendMessageMutation.isPending && (
              <motion.div 
                className="flex gap-3"
                initial={{ opacity: 0, x: -20, y: 10 }}
                animate={{ opacity: 1, x: 0, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <motion.div
                  animate={{ 
                    scale: [1, 1.05, 1],
                  }}
                  transition={{ 
                    duration: 2,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                >
                  <Avatar className="h-8 w-8 flex-shrink-0 ring-2 ring-accent/20">
                    <AvatarImage src={expert.avatar || undefined} alt={expert.name} />
                    <AvatarFallback className="text-xs">{initials}</AvatarFallback>
                  </Avatar>
                </motion.div>
                <motion.div 
                  className="flex items-center gap-2 px-4 py-3 bg-card border rounded-xl"
                  animate={{ 
                    boxShadow: [
                      "0 0 0 0 rgba(var(--primary), 0)",
                      "0 0 0 4px rgba(var(--primary), 0.1)",
                      "0 0 0 0 rgba(var(--primary), 0)"
                    ]
                  }}
                  transition={{ 
                    duration: 2,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                >
                  <PulseLoader size="sm" text="Pensando..." />
                </motion.div>
              </motion.div>
            )}
          </>
        )}
      </div>

      <div className="flex-shrink-0">
        {suggestedQuestions.length > 0 && messages.length === 0 && !sendMessageMutation.isPending && (
          <motion.div 
            className="px-3 sm:px-4 md:px-6 pb-3 sm:pb-4 border-t"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <motion.div 
              className="flex items-center gap-2 mb-3 pt-3 sm:pt-4"
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: 0.1 }}
            >
              <Sparkles className="h-4 w-4 text-accent" />
              <span className="text-xs sm:text-sm font-medium text-muted-foreground">
                Perguntas Sugeridas
                {suggestedQuestionsData?.personalized && (
                  <span className="ml-2 text-xs text-accent hidden sm:inline">(Personalizadas para você)</span>
                )}
              </span>
            </motion.div>
            <div className="flex flex-wrap gap-2">
              {suggestedQuestions.map((question, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, scale: 0.8, y: 10 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  transition={{ 
                    duration: 0.3, 
                    delay: 0.2 + index * 0.05,
                    ease: [0.25, 0.1, 0.25, 1]
                  }}
                >
                  <Badge
                    variant="outline"
                    className="cursor-pointer hover-elevate active-elevate-2 py-2 px-2 sm:px-3 text-xs"
                    onClick={() => handleSuggestedQuestion(question)}
                    data-testid={`badge-suggestion-${index}`}
                  >
                    {question}
                  </Badge>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        <div className="border-t bg-card p-3 sm:p-4">
          <div className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !sendMessageMutation.isPending && handleSend()}
              placeholder="Digite sua pergunta estratégica..."
              className="flex-1 h-12 text-sm sm:text-base"
              disabled={sendMessageMutation.isPending}
              data-testid="input-chat-message"
            />
            <Button 
              onClick={handleSend} 
              size="icon" 
              disabled={sendMessageMutation.isPending || !input.trim()}
              className="h-12 w-12"
              data-testid="button-send-message"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
      </div>
    </AnimatedPage>
  );
}
