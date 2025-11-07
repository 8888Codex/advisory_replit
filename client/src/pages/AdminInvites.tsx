import { useQuery, useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import { AdminLayout } from '@/components/AdminLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { apiRequest, queryClient } from '@/lib/queryClient';
import { Plus, CheckCircle2, XCircle } from 'lucide-react';
import { format } from 'date-fns';

interface InviteCode {
  id: string;
  code: string;
  creatorId: string;
  usedBy: string | null;
  usedAt: string | null;
  createdAt: string;
}

export default function AdminInvites() {
  const { toast } = useToast();
  const [newCode, setNewCode] = useState('');

  const { data: invites, isLoading } = useQuery<InviteCode[]>({
    queryKey: ['/api/admin/invites'],
  });

  const createInviteMutation = useMutation({
    mutationFn: async (code: string) => {
      const response = await apiRequest('/api/admin/invites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      });
      if (!response.ok) throw new Error('Failed to create invite');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/admin/invites'] });
      toast({
        title: 'Convite criado',
        description: 'O código de convite foi criado com sucesso.',
      });
      setNewCode('');
    },
    onError: () => {
      toast({
        title: 'Erro',
        description: 'Não foi possível criar o código de convite.',
        variant: 'destructive',
      });
    },
  });

  const handleCreateInvite = () => {
    if (!newCode || newCode.length > 16) {
      toast({
        title: 'Código inválido',
        description: 'O código deve ter entre 1 e 16 caracteres.',
        variant: 'destructive',
      });
      return;
    }
    createInviteMutation.mutate(newCode);
  };

  const usedCount = invites?.filter((inv) => inv.usedBy).length || 0;
  const availableCount = (invites?.length || 0) - usedCount;

  if (isLoading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin"></div>
        </div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold" data-testid="text-invites-title">Convites</h1>
          <p className="text-muted-foreground">Gerencie códigos de convite</p>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total de Convites</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold" data-testid="text-total-invites">
                {invites?.length || 0}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Disponíveis</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-500" data-testid="text-available-invites">
                {availableCount}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Usados</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-500" data-testid="text-used-invites">
                {usedCount}
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Criar Novo Convite</CardTitle>
            <CardDescription>Código deve ter entre 1 e 16 caracteres</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              <Input
                placeholder="Digite o código do convite"
                value={newCode}
                onChange={(e) => setNewCode(e.target.value)}
                maxLength={16}
                data-testid="input-invite-code"
              />
              <Button
                onClick={handleCreateInvite}
                disabled={createInviteMutation.isPending || !newCode}
                data-testid="button-create-invite"
              >
                <Plus className="h-4 w-4 mr-2" />
                Criar
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Lista de Convites</CardTitle>
            <CardDescription>Todos os códigos de convite criados</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {invites?.map((invite) => (
                <div
                  key={invite.id}
                  className="flex items-center justify-between p-3 border rounded-lg hover-elevate"
                  data-testid={`card-invite-${invite.id}`}
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <code className="font-mono font-semibold" data-testid={`text-code-${invite.id}`}>
                        {invite.code}
                      </code>
                      {invite.usedBy ? (
                        <Badge variant="outline" className="bg-blue-500/10 text-blue-500 border-blue-500/20">
                          <CheckCircle2 className="h-3 w-3 mr-1" />
                          Usado
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="bg-green-500/10 text-green-500 border-green-500/20">
                          <XCircle className="h-3 w-3 mr-1" />
                          Disponível
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Criado em {format(new Date(invite.createdAt), 'dd/MM/yyyy HH:mm')}
                      {invite.usedAt && ` • Usado em ${format(new Date(invite.usedAt), 'dd/MM/yyyy HH:mm')}`}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </AdminLayout>
  );
}
