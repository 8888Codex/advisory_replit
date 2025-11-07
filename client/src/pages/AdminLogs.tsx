import { useQuery } from '@tanstack/react-query';
import { AdminLayout } from '@/components/AdminLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { format } from 'date-fns';
import { FileText, User, Key, Shield } from 'lucide-react';

interface AuditLog {
  id: string;
  userId: string;
  action: string;
  resourceType: string;
  resourceId: string | null;
  metadata: Record<string, any> | null;
  ipAddress: string | null;
  createdAt: string;
}

export default function AdminLogs() {
  const { data: logs, isLoading } = useQuery<AuditLog[]>({
    queryKey: ['/api/admin/audit-logs'],
  });

  const getActionIcon = (action: string) => {
    if (action.includes('user')) return <User className="h-3 w-3" />;
    if (action.includes('invite')) return <Key className="h-3 w-3" />;
    if (action.includes('role')) return <Shield className="h-3 w-3" />;
    return <FileText className="h-3 w-3" />;
  };

  const getActionColor = (action: string) => {
    if (action.includes('delete') || action.includes('ban')) {
      return 'bg-red-500/10 text-red-500 border-red-500/20';
    }
    if (action.includes('create')) {
      return 'bg-green-500/10 text-green-500 border-green-500/20';
    }
    if (action.includes('update') || action.includes('change')) {
      return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
    }
    return 'bg-gray-500/10 text-gray-500 border-gray-500/20';
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
          <h1 className="text-3xl font-bold" data-testid="text-logs-title">Logs de Auditoria</h1>
          <p className="text-muted-foreground">Histórico de ações do sistema</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Logs Recentes</CardTitle>
            <CardDescription>Total de {logs?.length || 0} eventos registrados</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {logs && logs.length > 0 ? (
                logs.map((log) => (
                  <div
                    key={log.id}
                    className="flex items-start gap-3 p-3 border rounded-lg hover-elevate"
                    data-testid={`card-log-${log.id}`}
                  >
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className={getActionColor(log.action)}>
                          <span className="flex items-center gap-1">
                            {getActionIcon(log.action)}
                            {log.action}
                          </span>
                        </Badge>
                        <Badge variant="outline">{log.resourceType}</Badge>
                      </div>
                      <div className="text-sm space-y-1">
                        <p className="text-muted-foreground">
                          Usuário: <code className="text-xs">{log.userId.substring(0, 8)}...</code>
                        </p>
                        {log.resourceId && (
                          <p className="text-muted-foreground">
                            Recurso: <code className="text-xs">{log.resourceId.substring(0, 8)}...</code>
                          </p>
                        )}
                        {log.metadata && (
                          <p className="text-muted-foreground">
                            Dados: <code className="text-xs">{JSON.stringify(log.metadata)}</code>
                          </p>
                        )}
                        <p className="text-xs text-muted-foreground">
                          {format(new Date(log.createdAt), 'dd/MM/yyyy HH:mm:ss')}
                          {log.ipAddress && ` • IP: ${log.ipAddress}`}
                        </p>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  Nenhum log de auditoria encontrado.
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </AdminLayout>
  );
}
