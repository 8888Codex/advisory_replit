import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useLocation } from "wouter";
import { AnimatedPage } from "@/components/AnimatedPage";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { MessageSquare, Clock, ChevronRight, Loader2, Trash2, AlertCircle } from "lucide-react";
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

interface ConversationWithDetails {
  id: string;
  expertId: string;
  expertName: string;
  expertAvatar: string | null;
  expertCategory: string;
  title: string;
  messageCount: number;
  lastMessage: string | null;
  createdAt: string;
  updatedAt: string;
}

export default function ConversationHistory() {
  const [, setLocation] = useLocation();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [conversationToDelete, setConversationToDelete] = useState<string | null>(null);
  const [clearAllDialogOpen, setClearAllDialogOpen] = useState(false);

  const { data: conversations = [], isLoading } = useQuery<ConversationWithDetails[]>({
    queryKey: ["/api/conversations/history/user"],
  });

  // Delete single conversation mutation
  const deleteMutation = useMutation({
    mutationFn: async (conversationId: string) => {
      const response = await fetch(`/api/conversations/${conversationId}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erro ao deletar conversa');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/conversations/history/user"] });
      toast({
        title: "Conversa deletada",
        description: "A conversa foi removida com sucesso.",
      });
      setDeleteDialogOpen(false);
      setConversationToDelete(null);
    },
    onError: (error: Error) => {
      toast({
        variant: "destructive",
        title: "Erro ao deletar",
        description: error.message,
      });
    },
  });

  // Clear all conversations mutation
  const clearAllMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/conversations/user/clear-all', {
        method: 'DELETE',
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erro ao limpar histórico');
      }
      return response.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["/api/conversations/history/user"] });
      toast({
        title: "Histórico limpo",
        description: `${data.deletedCount} conversa(s) removida(s) com sucesso.`,
      });
      setClearAllDialogOpen(false);
    },
    onError: (error: Error) => {
      toast({
        variant: "destructive",
        title: "Erro ao limpar histórico",
        description: error.message,
      });
    },
  });

  const handleDeleteClick = (e: React.MouseEvent, conversationId: string) => {
    e.stopPropagation(); // Prevent opening conversation
    setConversationToDelete(conversationId);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = () => {
    if (conversationToDelete) {
      deleteMutation.mutate(conversationToDelete);
    }
  };

  const handleClearAll = () => {
    clearAllMutation.mutate();
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      marketing: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
      growth: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
      content: "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300",
      social: "bg-pink-100 text-pink-700 dark:bg-pink-900 dark:text-pink-300",
      seo: "bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300",
      direct_response: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
      positioning: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-300",
      creative: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300",
      product: "bg-teal-100 text-teal-700 dark:bg-teal-900 dark:text-teal-300",
      viral: "bg-fuchsia-100 text-fuchsia-700 dark:bg-fuchsia-900 dark:text-fuchsia-300",
    };
    return colors[category] || "bg-gray-100 text-gray-700";
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "agora mesmo";
    if (diffMins < 60) return `há ${diffMins} min`;
    if (diffHours < 24) return `há ${diffHours}h`;
    if (diffDays < 7) return `há ${diffDays}d`;
    return date.toLocaleDateString("pt-BR");
  };

  if (isLoading) {
    return (
      <AnimatedPage>
        <div className="container max-w-5xl mx-auto px-4 py-8">
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        </div>
      </AnimatedPage>
    );
  }

  return (
    <AnimatedPage>
      <div className="container max-w-5xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8 flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Histórico de Conversas</h1>
            <p className="text-muted-foreground">
              Retome suas conversas anteriores com os experts
            </p>
          </div>
          {conversations.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setClearAllDialogOpen(true)}
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Limpar Tudo
            </Button>
          )}
        </div>

        {/* Conversations List */}
        {conversations.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <MessageSquare className="h-12 w-12 text-muted-foreground/30 mb-4" />
              <h3 className="text-lg font-semibold mb-2">Nenhuma conversa ainda</h3>
              <p className="text-muted-foreground text-center mb-6">
                Comece conversando com um expert para criar seu histórico
              </p>
              <Button onClick={() => setLocation("/experts")}>
                Ver Experts
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {conversations.map((conversation) => (
              <Card
                key={conversation.id}
                className="hover:shadow-lg transition-shadow cursor-pointer group"
                onClick={() => setLocation(`/chat/${conversation.expertId}?conversationId=${conversation.id}`)}
              >
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    {/* Expert Avatar */}
                    <div className="flex-shrink-0">
                      {conversation.expertAvatar ? (
                        <img
                          src={conversation.expertAvatar}
                          alt={conversation.expertName}
                          className="w-14 h-14 rounded-full object-cover"
                        />
                      ) : (
                        <div className="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center">
                          <span className="text-xl font-bold text-primary">
                            {conversation.expertName.charAt(0)}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Conversation Details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold text-lg truncate">
                          {conversation.expertName}
                        </h3>
                        <Badge
                          variant="secondary"
                          className={getCategoryColor(conversation.expertCategory)}
                        >
                          {conversation.expertCategory}
                        </Badge>
                      </div>

                      <h4 className="text-sm font-medium text-muted-foreground mb-2">
                        {conversation.title}
                      </h4>

                      {/* Last Message Preview */}
                      {conversation.lastMessage && (
                        <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                          {conversation.lastMessage}
                        </p>
                      )}

                      {/* Metadata */}
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <MessageSquare className="h-3 w-3" />
                          <span>{conversation.messageCount} mensagens</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          <span>{formatDate(conversation.updatedAt)}</span>
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex-shrink-0 self-center flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={(e) => handleDeleteClick(e, conversation.id)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity text-destructive hover:text-destructive hover:bg-destructive/10"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                      <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                        <ChevronRight className="h-5 w-5 text-muted-foreground" />
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Footer Stats */}
        {conversations.length > 0 && (
          <div className="mt-8 text-center text-sm text-muted-foreground">
            {conversations.length} conversa{conversations.length !== 1 ? "s" : ""} no total
          </div>
        )}

        {/* Delete Confirmation Dialog */}
        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Deletar conversa?</AlertDialogTitle>
              <AlertDialogDescription>
                Esta ação não pode ser desfeita. A conversa e todas as mensagens serão permanentemente removidas.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel onClick={() => setConversationToDelete(null)}>
                Cancelar
              </AlertDialogCancel>
              <AlertDialogAction
                onClick={handleConfirmDelete}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              >
                Deletar
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        {/* Clear All Confirmation Dialog */}
        <AlertDialog open={clearAllDialogOpen} onOpenChange={setClearAllDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle className="flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-destructive" />
                Limpar todo o histórico?
              </AlertDialogTitle>
              <AlertDialogDescription>
                Esta ação não pode ser desfeita. Todas as suas {conversations.length} conversas e mensagens serão permanentemente removidas.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancelar</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleClearAll}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              >
                Limpar Tudo
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </AnimatedPage>
  );
}

