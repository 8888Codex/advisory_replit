import { useAuth } from '@/contexts/AuthContext';
import { useQuery, useMutation } from '@tanstack/react-query';
import { queryClient, apiRequest } from '@/lib/queryClient';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { 
  Crown, 
  Users, 
  Database, 
  TrendingUp, 
  Download, 
  Settings as SettingsIcon,
  Shield,
  Activity,
  Trash2,
  UserPlus
} from 'lucide-react';
import { useState } from 'react';

interface GlobalMetrics {
  totalUsers: number;
  totalAdmins: number;
  totalSuperAdmins: number;
  totalPersonas: number;
  totalExperts: number;
  totalConversations: number;
  totalCouncilAnalyses: number;
  totalCouncilMessages: number;
  systemHealthScore: number;
  avgEnrichmentLevel: string;
}

interface PersonaRow {
  id: string;
  user_id: string;
  company_name: string;
  industry: string;
  enrichment_level: string;
  created_at: string;
  username: string;
  email: string;
}

interface TopExpert {
  expert_name: string;
  consultations: number;
  last_consulted: string;
}

export default function SuperAdminDashboard() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [selectedUserId, setSelectedUserId] = useState('');
  const [inviteAmount, setInviteAmount] = useState(5);
  const [exportUserId, setExportUserId] = useState('');

  // Queries
  const { data: metrics, isLoading: metricsLoading } = useQuery<GlobalMetrics>({
    queryKey: ['/api/superadmin/metrics'],
    enabled: user?.role === 'superadmin',
  });

  const { data: allPersonas = [], isLoading: personasLoading } = useQuery<PersonaRow[]>({
    queryKey: ['/api/superadmin/personas'],
    enabled: user?.role === 'superadmin',
  });

  const { data: topExperts = [], isLoading: expertsLoading } = useQuery<TopExpert[]>({
    queryKey: ['/api/superadmin/analytics/top-experts'],
    enabled: user?.role === 'superadmin',
  });

  // Mutations
  const deletePersonaMutation = useMutation({
    mutationFn: async (personaId: string) => {
      const response = await apiRequest(`/api/superadmin/personas/${personaId}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error('Erro ao deletar persona');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/superadmin/personas'] });
      queryClient.invalidateQueries({ queryKey: ['/api/superadmin/metrics'] });
      toast({
        title: 'Persona deletada',
        description: 'Persona removida com sucesso',
      });
    },
    onError: () => {
      toast({
        title: 'Erro',
        description: 'Não foi possível deletar a persona',
        variant: 'destructive',
      });
    },
  });

  const addInvitesMutation = useMutation({
    mutationFn: async (data: { userId: string; amount: number }) => {
      const response = await apiRequest('/api/superadmin/invites/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erro ao adicionar convites');
      }
      return response.json();
    },
    onSuccess: () => {
      setSelectedUserId('');
      setInviteAmount(5);
      toast({
        title: 'Convites adicionados',
        description: 'Convites foram creditados ao usuário',
      });
    },
    onError: (error) => {
      toast({
        title: 'Erro',
        description: error instanceof Error ? error.message : 'Tente novamente',
        variant: 'destructive',
      });
    },
  });

  const exportDataMutation = useMutation({
    mutationFn: async (userId: string) => {
      const response = await apiRequest(`/api/superadmin/export/user/${userId}`, {
        method: 'GET',
      });
      if (!response.ok) {
        throw new Error('Erro ao exportar dados');
      }
      return response.json();
    },
    onSuccess: (data) => {
      // Download as JSON file
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `user_export_${exportUserId}_${Date.now()}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      setExportUserId('');
      toast({
        title: 'Dados exportados',
        description: 'Download iniciado com sucesso',
      });
    },
    onError: () => {
      toast({
        title: 'Erro',
        description: 'Não foi possível exportar os dados',
        variant: 'destructive',
      });
    },
  });

  // Verify superadmin access
  if (user?.role !== 'superadmin') {
    return (
      <div className="container max-w-4xl mx-auto px-4 py-16 text-center">
        <Shield className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
        <h1 className="text-2xl font-bold mb-2">Acesso Negado</h1>
        <p className="text-muted-foreground">Apenas SuperAdmins podem acessar esta área.</p>
      </div>
    );
  }

  return (
    <div className="container max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-lg bg-gradient-to-br from-yellow-500/10 to-yellow-600/20">
            <Crown className="w-8 h-8 text-yellow-500" />
          </div>
          <h1 className="text-4xl font-bold">SuperAdmin Control Panel</h1>
        </div>
        <p className="text-muted-foreground">
          Gerenciamento avançado e métricas globais do sistema
        </p>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="metrics" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5 lg:w-auto lg:inline-grid">
          <TabsTrigger value="metrics">
            <TrendingUp className="w-4 h-4 mr-2" />
            Métricas
          </TabsTrigger>
          <TabsTrigger value="personas">
            <Database className="w-4 h-4 mr-2" />
            Personas
          </TabsTrigger>
          <TabsTrigger value="analytics">
            <Activity className="w-4 h-4 mr-2" />
            Analytics
          </TabsTrigger>
          <TabsTrigger value="invites">
            <UserPlus className="w-4 h-4 mr-2" />
            Convites
          </TabsTrigger>
          <TabsTrigger value="export">
            <Download className="w-4 h-4 mr-2" />
            Export
          </TabsTrigger>
        </TabsList>

        {/* TAB: Métricas Globais */}
        <TabsContent value="metrics" className="space-y-6">
          {metricsLoading ? (
            <div className="text-center py-12">Carregando métricas...</div>
          ) : metrics ? (
            <>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardDescription>Total de Usuários</CardDescription>
                    <CardTitle className="text-3xl">{metrics.totalUsers}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Users className="w-3 h-3" />
                      Plataforma completa
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardDescription>Admins</CardDescription>
                    <CardTitle className="text-3xl">{metrics.totalAdmins}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-xs text-muted-foreground">
                      {metrics.totalSuperAdmins} SuperAdmins
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardDescription>Personas Criadas</CardDescription>
                    <CardTitle className="text-3xl">{metrics.totalPersonas}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Badge variant="outline" className="capitalize">
                      Avg: {metrics.avgEnrichmentLevel}
                    </Badge>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardDescription>Experts Customizados</CardDescription>
                    <CardTitle className="text-3xl">{metrics.totalExperts}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-xs text-muted-foreground">
                      + 18 Seed Clones
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                <Card>
                  <CardHeader className="pb-2">
                    <CardDescription>Conversas 1:1</CardDescription>
                    <CardTitle className="text-2xl">{metrics.totalConversations}</CardTitle>
                  </CardHeader>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardDescription>Análises do Conselho</CardDescription>
                    <CardTitle className="text-2xl">{metrics.totalCouncilAnalyses}</CardTitle>
                  </CardHeader>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardDescription>Mensagens do Conselho</CardDescription>
                    <CardTitle className="text-2xl">{metrics.totalCouncilMessages}</CardTitle>
                  </CardHeader>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="w-5 h-5 text-green-500" />
                    System Health
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-4">
                    <div className="flex-1 bg-secondary rounded-full h-4 overflow-hidden">
                      <div 
                        className="bg-gradient-to-r from-green-500 to-green-600 h-full transition-all"
                        style={{ width: `${metrics.systemHealthScore}%` }}
                      />
                    </div>
                    <span className="text-2xl font-bold text-green-500">
                      {metrics.systemHealthScore}%
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground mt-2">
                    Sistema operando normalmente
                  </p>
                </CardContent>
              </Card>
            </>
          ) : null}
        </TabsContent>

        {/* TAB: Gerenciar Personas */}
        <TabsContent value="personas" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Todas as Personas do Sistema</CardTitle>
              <CardDescription>
                Visualize e gerencie personas de todos os usuários
              </CardDescription>
            </CardHeader>
            <CardContent>
              {personasLoading ? (
                <div className="text-center py-8">Carregando personas...</div>
              ) : allPersonas.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  Nenhuma persona encontrada
                </div>
              ) : (
                <div className="space-y-3">
                  {allPersonas.map((persona) => (
                    <div
                      key={persona.id}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/5 transition-colors"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-1">
                          <h3 className="font-semibold">{persona.company_name}</h3>
                          <Badge variant="outline" className="capitalize">
                            {persona.enrichment_level}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Users className="w-3 h-3" />
                            {persona.username} ({persona.email})
                          </span>
                          <span>•</span>
                          <span>{persona.industry}</span>
                          <span>•</span>
                          <span>{new Date(persona.created_at).toLocaleDateString('pt-BR')}</span>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          if (confirm(`Deletar persona "${persona.company_name}"?`)) {
                            deletePersonaMutation.mutate(persona.id);
                          }
                        }}
                        disabled={deletePersonaMutation.isPending}
                      >
                        <Trash2 className="w-4 h-4 text-destructive" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* TAB: Analytics Global */}
        <TabsContent value="analytics" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Top 20 Experts Mais Consultados</CardTitle>
              <CardDescription>
                Experts com maior número de consultas (todos os usuários)
              </CardDescription>
            </CardHeader>
            <CardContent>
              {expertsLoading ? (
                <div className="text-center py-8">Carregando analytics...</div>
              ) : topExperts.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  Nenhum dado de consultas ainda
                </div>
              ) : (
                <div className="space-y-2">
                  {topExperts.map((expert, index) => (
                    <div
                      key={expert.expert_name}
                      className="flex items-center justify-between p-3 border rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-accent/10 text-accent font-bold text-sm">
                          {index + 1}
                        </div>
                        <div>
                          <h4 className="font-medium">{expert.expert_name}</h4>
                          <p className="text-xs text-muted-foreground">
                            Última consulta: {new Date(expert.last_consulted).toLocaleDateString('pt-BR')}
                          </p>
                        </div>
                      </div>
                      <Badge variant="secondary">
                        {expert.consultations} consultas
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* TAB: Convites em Massa */}
        <TabsContent value="invites" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Adicionar Convites para Usuário</CardTitle>
              <CardDescription>
                Credite convites extras para usuários específicos
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (!selectedUserId || inviteAmount <= 0) {
                    toast({
                      title: 'Campos obrigatórios',
                      description: 'Preencha User ID e quantidade',
                      variant: 'destructive',
                    });
                    return;
                  }
                  addInvitesMutation.mutate({
                    userId: selectedUserId,
                    amount: inviteAmount,
                  });
                }}
                className="space-y-4"
              >
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    User ID (UUID)
                  </label>
                  <Input
                    type="text"
                    placeholder="48bb3e53-bfca-4298-bab5-1627ca216739"
                    value={selectedUserId}
                    onChange={(e) => setSelectedUserId(e.target.value)}
                    disabled={addInvitesMutation.isPending}
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Quantidade de Convites
                  </label>
                  <Input
                    type="number"
                    min="1"
                    max="100"
                    value={inviteAmount}
                    onChange={(e) => setInviteAmount(parseInt(e.target.value) || 1)}
                    disabled={addInvitesMutation.isPending}
                  />
                </div>

                <Button
                  type="submit"
                  disabled={addInvitesMutation.isPending}
                  className="w-full sm:w-auto"
                >
                  <UserPlus className="w-4 h-4 mr-2" />
                  {addInvitesMutation.isPending ? 'Adicionando...' : 'Adicionar Convites'}
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        {/* TAB: Export de Dados */}
        <TabsContent value="export" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Export de Dados do Usuário (GDPR)</CardTitle>
              <CardDescription>
                Exporte todos os dados de um usuário específico em formato JSON
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (!exportUserId) {
                    toast({
                      title: 'User ID obrigatório',
                      description: 'Informe o ID do usuário para exportar',
                      variant: 'destructive',
                    });
                    return;
                  }
                  exportDataMutation.mutate(exportUserId);
                }}
                className="space-y-4"
              >
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    User ID (UUID)
                  </label>
                  <Input
                    type="text"
                    placeholder="48bb3e53-bfca-4298-bab5-1627ca216739"
                    value={exportUserId}
                    onChange={(e) => setExportUserId(e.target.value)}
                    disabled={exportDataMutation.isPending}
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Inclui: usuário, personas, conversas e análises do conselho
                  </p>
                </div>

                <Button
                  type="submit"
                  disabled={exportDataMutation.isPending}
                  className="w-full sm:w-auto"
                >
                  <Download className="w-4 h-4 mr-2" />
                  {exportDataMutation.isPending ? 'Exportando...' : 'Exportar Dados (JSON)'}
                </Button>
              </form>
            </CardContent>
          </Card>

          <Card className="bg-yellow-500/5 border-yellow-500/20">
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Shield className="w-4 h-4" />
                GDPR Compliance
              </CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-muted-foreground">
              <p>
                Esta funcionalidade permite o export completo de dados para atender solicitações de
                usuários conforme GDPR e LGPD. O arquivo JSON contém todas as informações
                armazenadas do usuário.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

