import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useQuery, useMutation } from '@tanstack/react-query';
import { queryClient, apiRequest } from '@/lib/queryClient';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';
import { Ticket, Copy, Check, Plus, User, Calendar, Shield, CheckCircle2, XCircle, Lock, Target, Sparkles } from 'lucide-react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Link } from 'wouter';
import { extractPersonaSummary } from '@/lib/textUtils';
import type { UserPersona } from '@shared/schema';

interface InviteCode {
  code: string;
  createdAt: string;
  usedBy: number | null;
  usedAt: string | null;
}

interface AuditLog {
  id: string;
  userId: string | null;
  action: string;
  success: boolean;
  ipAddress: string | null;
  userAgent: string | null;
  metadata: Record<string, any> | null;
  timestamp: string;
}

function SettingsContent() {
  const { user, refreshUser } = useAuth();
  const { toast } = useToast();
  const [copiedCode, setCopiedCode] = useState<string | null>(null);
  
  // Password change states
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  
  // Avatar upload states
  const [avatarFile, setAvatarFile] = useState<File | null>(null);

  const { data: inviteCodes = [], isLoading } = useQuery<InviteCode[]>({
    queryKey: ['/api/invites/my-codes'],
  });

  const { data: auditLogs = [], isLoading: logsLoading } = useQuery<AuditLog[]>({
    queryKey: ['/api/audit/logs'],
  });
  
  // Fetch active persona
  const { data: persona } = useQuery<UserPersona | null>({
    queryKey: ['/api/persona/current'],
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
  
  // Change Password Mutation
  const changePasswordMutation = useMutation({
    mutationFn: async (passwords: { currentPassword: string; newPassword: string }) => {
      const response = await apiRequest('/api/auth/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(passwords),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erro ao atualizar senha');
      }
      return response.json();
    },
    onSuccess: () => {
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      toast({
        title: 'Senha atualizada',
        description: 'Sua senha foi alterada com sucesso',
      });
    },
    onError: (error) => {
      toast({
        title: 'Erro ao atualizar senha',
        description: error instanceof Error ? error.message : 'Tente novamente',
        variant: 'destructive',
      });
    },
  });
  
  // Avatar Upload Mutation
  const uploadAvatarMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await apiRequest('/api/upload/user-avatar', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erro ao fazer upload');
      }
      return response.json();
    },
    onSuccess: async () => {
      await refreshUser();
      setAvatarFile(null);
      toast({
        title: 'Avatar atualizado',
        description: 'Sua foto de perfil foi atualizada com sucesso'
      });
    },
    onError: (error) => {
      toast({
        title: 'Erro no upload',
        description: error instanceof Error ? error.message : 'Tente novamente',
        variant: 'destructive'
      });
    }
  });
  
  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    if (!file.type.startsWith('image/')) {
      toast({
        title: 'Arquivo inválido',
        description: 'Selecione uma imagem (JPG, PNG, WEBP)',
        variant: 'destructive'
      });
      return;
    }
    
    if (file.size > 5 * 1024 * 1024) {
      toast({
        title: 'Arquivo muito grande',
        description: 'Máximo 5MB',
        variant: 'destructive'
      });
      return;
    }
    
    setAvatarFile(file);
    uploadAvatarMutation.mutate(file);
  };

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
  
  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate passwords match
    if (newPassword !== confirmPassword) {
      toast({
        title: 'Senhas não conferem',
        description: 'A nova senha e a confirmação devem ser iguais',
        variant: 'destructive',
      });
      return;
    }
    
    // Submit password change
    changePasswordMutation.mutate({
      currentPassword,
      newPassword,
    });
  };

  if (!user) return null;
  
  // Get user initials for avatar
  const userInitials = user.username.slice(0, 2).toUpperCase();

  return (
    <div className="container max-w-5xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
      <div className="mb-6 sm:mb-8">
        <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight mb-2">Configurações</h1>
        <p className="text-sm sm:text-base text-muted-foreground">Gerencie seu perfil e preferências</p>
      </div>

      <div className="space-y-6">
        {/* Profile Section */}
        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg sm:text-xl">
              <User className="w-5 h-5 text-accent" />
              Perfil
            </CardTitle>
            <CardDescription>Suas informações pessoais</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col sm:flex-row items-start gap-6">
              {/* Avatar */}
              <div className="shrink-0 mx-auto sm:mx-0 relative group">
                <input
                  type="file"
                  id="avatar-upload"
                  className="hidden"
                  accept="image/*"
                  onChange={handleAvatarChange}
                />
                <label
                  htmlFor="avatar-upload"
                  className="cursor-pointer block"
                >
                  <div className="w-20 h-20 rounded-full bg-gradient-to-br from-accent/10 to-accent/20 flex items-center justify-center ring-2 ring-accent/30 group-hover:ring-accent/50 transition-all relative overflow-hidden">
                    {user.avatarUrl ? (
                      <img 
                        src={user.avatarUrl} 
                        alt={user.username}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <span className="text-2xl font-bold text-accent">{userInitials}</span>
                    )}
                    
                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <span className="text-white text-xs font-medium">
                        {uploadAvatarMutation.isPending ? 'Enviando...' : 'Alterar'}
                      </span>
                    </div>
                  </div>
                </label>
                
                {uploadAvatarMutation.isPending && (
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div className="w-6 h-6 border-4 border-accent border-t-transparent rounded-full animate-spin"></div>
                  </div>
                )}
              </div>
              
              {/* User Info */}
              <div className="flex-1 space-y-4 w-full">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Nome de Usuário</label>
                    <p className="text-base font-medium mt-1">{user.username}</p>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Email</label>
                    <p className="text-base font-medium mt-1">{user.email}</p>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Membro desde</label>
                    <p className="text-base flex items-center gap-2 mt-1">
                      <Calendar className="w-4 h-4 text-muted-foreground" />
                      {user.createdAt ? formatDate(user.createdAt) : 'Não disponível'}
                    </p>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Função</label>
                    <div className="mt-1">
                      <Badge variant="outline" className="capitalize">
                        {user.role}
                      </Badge>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Active Persona Card */}
        <Card className="rounded-2xl bg-gradient-to-br from-accent/5 to-accent/10 border-accent/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg sm:text-xl">
              <Target className="w-5 h-5 text-accent" />
              Sua Persona Ativa
            </CardTitle>
            <CardDescription>Contexto estratégico para consultas com especialistas</CardDescription>
          </CardHeader>
          <CardContent>
            {persona ? (
              <div className="space-y-4">
                <div>
                  <h3 className="font-semibold text-lg">{persona.companyName || persona.industry || 'Sua Persona'}</h3>
                  <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
                    {persona.targetAudience ? extractPersonaSummary(persona.targetAudience, 150) : 'Sem descrição'}
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline" className="capitalize">
                    <Sparkles className="w-3 h-3 mr-1" />
                    {persona.enrichmentLevel || 'quick'} enrichment
                  </Badge>
                  {persona.industry && (
                    <Badge variant="outline">
                      {persona.industry}
                    </Badge>
                  )}
                </div>
                <Link href={`/personas/${persona.id}`}>
                  <Button variant="outline" className="w-full sm:w-auto">
                    Ver Persona Completa →
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="text-center py-6">
                <Target className="w-12 h-12 mx-auto mb-3 text-muted-foreground opacity-50" />
                <p className="text-muted-foreground mb-4">Você ainda não tem uma persona ativa</p>
                <Link href="/onboarding">
                  <Button className="w-full sm:w-auto">
                    <Sparkles className="w-4 h-4 mr-2" />
                    Criar Persona
                  </Button>
                </Link>
              </div>
            )}
          </CardContent>
        </Card>
        
        {/* Security / Change Password Section */}
        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg sm:text-xl">
              <Lock className="w-5 h-5 text-accent" />
              Segurança
            </CardTitle>
            <CardDescription>
              Altere sua senha para manter sua conta segura
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleChangePassword} className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Senha Atual</label>
                <Input 
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="Digite sua senha atual"
                  required
                  disabled={changePasswordMutation.isPending}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Nova Senha</label>
                <Input 
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Mínimo 6 caracteres"
                  minLength={6}
                  required
                  disabled={changePasswordMutation.isPending}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Confirmar Nova Senha</label>
                <Input 
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Digite novamente"
                  required
                  disabled={changePasswordMutation.isPending}
                />
              </div>
              <Button 
                type="submit" 
                disabled={changePasswordMutation.isPending}
                className="w-full sm:w-auto rounded-xl"
              >
                <Lock className="w-4 h-4 mr-2" />
                {changePasswordMutation.isPending ? 'Atualizando...' : 'Atualizar Senha'}
              </Button>
            </form>
          </CardContent>
        </Card>
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

        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-accent" />
              Histórico de Segurança
            </CardTitle>
            <CardDescription>
              Atividades recentes de autenticação na sua conta
            </CardDescription>
          </CardHeader>
          <CardContent>
            {logsLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="w-6 h-6 border-4 border-accent border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : auditLogs.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Shield className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>Nenhuma atividade registrada ainda</p>
              </div>
            ) : (
              <div className="space-y-3">
                {auditLogs.slice(0, 10).map((log) => {
                  const actionLabels: Record<string, string> = {
                    login: 'Login',
                    register: 'Registro',
                    logout: 'Logout',
                    password_reset_request: 'Solicitação de Reset',
                    password_reset_complete: 'Senha Redefinida'
                  };
                  
                  return (
                    <div
                      key={log.id}
                      className="flex items-start gap-4 p-4 rounded-xl border bg-card/50"
                      data-testid={`audit-log-${log.id}`}
                    >
                      <div className="shrink-0 mt-0.5">
                        {log.success ? (
                          <CheckCircle2 className="w-5 h-5 text-green-500" />
                        ) : (
                          <XCircle className="w-5 h-5 text-red-500" />
                        )}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium">
                            {actionLabels[log.action] || log.action}
                          </span>
                          <Badge variant={log.success ? "default" : "destructive"} className="text-xs">
                            {log.success ? 'Sucesso' : 'Falha'}
                          </Badge>
                        </div>
                        
                        <div className="space-y-1 text-xs text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {formatDate(log.timestamp)}
                          </div>
                          
                          {log.ipAddress && (
                            <div className="truncate">
                              IP: {log.ipAddress}
                            </div>
                          )}
                          
                          {log.metadata?.email && (
                            <div className="truncate">
                              Email: {log.metadata.email}
                            </div>
                          )}
                          
                          {!log.success && log.metadata?.error && (
                            <div className="text-red-500 text-xs mt-1">
                              {log.metadata.error}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
            
            {auditLogs.length > 10 && (
              <p className="text-xs text-muted-foreground text-center mt-4">
                Mostrando as 10 atividades mais recentes
              </p>
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
