import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useQuery, useMutation } from '@tanstack/react-query';
import { queryClient, apiRequest } from '@/lib/queryClient';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { Ticket, Copy, Check, Plus, User, Calendar } from 'lucide-react';
import { ProtectedRoute } from '@/components/ProtectedRoute';

interface InviteCode {
  code: string;
  createdAt: string;
  usedBy: number | null;
  usedAt: string | null;
}

function SettingsContent() {
  const { user, refreshUser } = useAuth();
  const { toast } = useToast();
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const { data: inviteCodes = [], isLoading } = useQuery<InviteCode[]>({
    queryKey: ['/api/invites/my-codes'],
  });

  const generateMutation = useMutation({
    mutationFn: async () => {
      const response = await apiRequest('/api/invites/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erro ao gerar código');
      }
      return response.json();
    },
    onSuccess: async (data) => {
      // Invalidate invite codes list
      queryClient.invalidateQueries({ queryKey: ['/api/invites/my-codes'] });
      
      // Wait a brief moment for DB commit, then refresh user
      await new Promise(resolve => setTimeout(resolve, 100));
      await refreshUser();
      
      // Copy código automaticamente
      await navigator.clipboard.writeText(data.code);
      setCopiedCode(data.code);
      setTimeout(() => setCopiedCode(null), 3000);
      
      toast({
        title: 'Código gerado',
        description: `Código ${data.code} copiado para a área de transferência`,
      });
    },
    onError: (error) => {
      toast({
        title: 'Erro ao gerar código',
        description: error instanceof Error ? error.message : 'Tente novamente',
        variant: 'destructive',
      });
    },
  });

  const copyToClipboard = async (code: string) => {
    await navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2000);
    toast({
      title: 'Código copiado',
      description: `${code} copiado para a área de transferência`,
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (!user) return null;

  return (
    <div className="container max-w-4xl mx-auto px-6 py-12">
      <div className="mb-8">
        <h1 className="text-4xl font-semibold tracking-tight mb-2">Configurações</h1>
        <p className="text-muted-foreground">Gerencie seus códigos de convite</p>
      </div>

      <div className="space-y-6">
        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Ticket className="w-5 h-5 text-accent" />
              Códigos de Convite
            </CardTitle>
            <CardDescription>
              Você tem <span className="font-medium text-foreground">{user.availableInvites}</span> códigos disponíveis
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              onClick={() => generateMutation.mutate()}
              disabled={user.availableInvites === 0 || generateMutation.isPending}
              className="rounded-xl"
              data-testid="button-generate-invite"
            >
              <Plus className="w-4 h-4 mr-2" />
              {generateMutation.isPending ? 'Gerando...' : 'Gerar Novo Código'}
            </Button>
            {user.availableInvites === 0 && (
              <p className="text-sm text-muted-foreground mt-3">
                Você já utilizou todos os seus códigos de convite.
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle>Meus Códigos</CardTitle>
            <CardDescription>
              {inviteCodes.length === 0 
                ? 'Você ainda não gerou nenhum código'
                : `${inviteCodes.filter(c => !c.usedBy).length} disponíveis, ${inviteCodes.filter(c => c.usedBy).length} usados`
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="w-6 h-6 border-4 border-accent border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : inviteCodes.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Ticket className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>Nenhum código gerado ainda</p>
              </div>
            ) : (
              <div className="space-y-3">
                {inviteCodes.map((invite) => (
                  <div
                    key={invite.code}
                    className="flex items-center justify-between p-4 rounded-xl border bg-card/50 hover-elevate"
                    data-testid={`invite-code-${invite.code}`}
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <code className="text-lg font-mono font-medium">{invite.code}</code>
                        {invite.usedBy ? (
                          <Badge variant="secondary" className="text-xs">
                            Usado
                          </Badge>
                        ) : (
                          <Badge className="text-xs bg-accent/10 text-accent border-accent/20">
                            Disponível
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          Criado {formatDate(invite.createdAt)}
                        </div>
                        {invite.usedBy && invite.usedAt && (
                          <div className="flex items-center gap-1">
                            <User className="w-3 h-3" />
                            Usado {formatDate(invite.usedAt)}
                          </div>
                        )}
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => copyToClipboard(invite.code)}
                      className="rounded-lg shrink-0"
                      data-testid={`button-copy-${invite.code}`}
                    >
                      {copiedCode === invite.code ? (
                        <Check className="w-4 h-4 text-green-500" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function Settings() {
  return (
    <ProtectedRoute>
      <SettingsContent />
    </ProtectedRoute>
  );
}
