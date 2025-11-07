import { useQuery, useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import { AdminLayout } from '@/components/AdminLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { apiRequest, queryClient } from '@/lib/queryClient';
import { Crown, User, ShieldCheck } from 'lucide-react';

interface User {
  id: string;
  username: string;
  email: string;
  role: 'user' | 'admin' | 'superadmin';
  availableInvites: number;
  createdAt: string;
}

export default function AdminUsers() {
  const { toast } = useToast();
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [selectedRole, setSelectedRole] = useState<string>('');

  const { data: users, isLoading } = useQuery<User[]>({
    queryKey: ['/api/admin/users'],
  });

  const updateRoleMutation = useMutation({
    mutationFn: async ({ userId, role }: { userId: string; role: string }) => {
      const response = await apiRequest(`/api/admin/users/${userId}/role`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role }),
      });
      if (!response.ok) throw new Error('Failed to update role');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/admin/users'] });
      toast({
        title: 'Role atualizado',
        description: 'O role do usuário foi atualizado com sucesso.',
      });
      setSelectedUserId(null);
      setSelectedRole('');
    },
    onError: () => {
      toast({
        title: 'Erro',
        description: 'Não foi possível atualizar o role do usuário.',
        variant: 'destructive',
      });
    },
  });

  const handleUpdateRole = (userId: string) => {
    if (!selectedRole) return;
    updateRoleMutation.mutate({ userId, role: selectedRole });
  };

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'superadmin':
        return <Crown className="h-3 w-3" />;
      case 'admin':
        return <ShieldCheck className="h-3 w-3" />;
      default:
        return <User className="h-3 w-3" />;
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'superadmin':
        return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
      case 'admin':
        return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
      default:
        return 'bg-gray-500/10 text-gray-500 border-gray-500/20';
    }
  };

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
          <h1 className="text-3xl font-bold" data-testid="text-users-title">Usuários</h1>
          <p className="text-muted-foreground">Gerencie usuários e permissões</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Lista de Usuários</CardTitle>
            <CardDescription>Total de {users?.length || 0} usuários cadastrados</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {users?.map((user) => (
                <div
                  key={user.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover-elevate"
                  data-testid={`card-user-${user.id}`}
                >
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold" data-testid={`text-username-${user.id}`}>
                        {user.username}
                      </h3>
                      <Badge variant="outline" className={getRoleColor(user.role)}>
                        <span className="flex items-center gap-1">
                          {getRoleIcon(user.role)}
                          {user.role}
                        </span>
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground" data-testid={`text-email-${user.id}`}>
                      {user.email}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {user.availableInvites} convites disponíveis
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    {selectedUserId === user.id ? (
                      <>
                        <Select value={selectedRole} onValueChange={setSelectedRole}>
                          <SelectTrigger className="w-[140px]" data-testid={`select-role-${user.id}`}>
                            <SelectValue placeholder="Escolha role" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="user">User</SelectItem>
                            <SelectItem value="admin">Admin</SelectItem>
                            <SelectItem value="superadmin">Superadmin</SelectItem>
                          </SelectContent>
                        </Select>
                        <Button
                          size="sm"
                          onClick={() => handleUpdateRole(user.id)}
                          disabled={updateRoleMutation.isPending}
                          data-testid={`button-save-role-${user.id}`}
                        >
                          Salvar
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            setSelectedUserId(null);
                            setSelectedRole('');
                          }}
                          data-testid={`button-cancel-role-${user.id}`}
                        >
                          Cancelar
                        </Button>
                      </>
                    ) : (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setSelectedUserId(user.id);
                          setSelectedRole(user.role);
                        }}
                        data-testid={`button-edit-role-${user.id}`}
                      >
                        Editar Role
                      </Button>
                    )}
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
