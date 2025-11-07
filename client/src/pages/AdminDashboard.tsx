import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, TicketCheck, Crown, Activity } from 'lucide-react';
import { AdminLayout } from '@/components/AdminLayout';

interface Stats {
  totalUsers: number;
  totalAdmins: number;
  totalInvites: number;
  usedInvites: number;
}

export default function AdminDashboard() {
  const { data: stats, isLoading } = useQuery<Stats>({
    queryKey: ['/api/admin/stats'],
  });

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
          <h1 className="text-3xl font-bold" data-testid="text-admin-title">Dashboard</h1>
          <p className="text-muted-foreground">Visão geral do sistema</p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card data-testid="card-stat-users">
            <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total de Usuários</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold" data-testid="text-total-users">
                {stats?.totalUsers || 0}
              </div>
            </CardContent>
          </Card>

          <Card data-testid="card-stat-admins">
            <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Administradores</CardTitle>
              <Crown className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold" data-testid="text-total-admins">
                {stats?.totalAdmins || 0}
              </div>
            </CardContent>
          </Card>

          <Card data-testid="card-stat-invites">
            <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Convites Criados</CardTitle>
              <TicketCheck className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold" data-testid="text-total-invites">
                {stats?.totalInvites || 0}
              </div>
            </CardContent>
          </Card>

          <Card data-testid="card-stat-used-invites">
            <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Convites Usados</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold" data-testid="text-used-invites">
                {stats?.usedInvites || 0}
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Bem-vindo ao Painel de Administração</CardTitle>
            <CardDescription>
              Gerencie usuários, convites e visualize analytics do sistema.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <p className="text-sm text-muted-foreground">
              Use o menu lateral para navegar entre as diferentes seções do painel.
            </p>
          </CardContent>
        </Card>
      </div>
    </AdminLayout>
  );
}
