import { useState } from 'react';
import { useLocation, Link } from 'wouter';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { UserPlus, Info } from 'lucide-react';

export default function Register() {
  const [, setLocation] = useLocation();
  const { register } = useAuth();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    inviteCode: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (formData.password !== formData.confirmPassword) {
      toast({
        title: 'Erro de validação',
        description: 'As senhas não coincidem',
        variant: 'destructive',
      });
      return;
    }

    if (formData.password.length < 6) {
      toast({
        title: 'Erro de validação',
        description: 'A senha deve ter pelo menos 6 caracteres',
        variant: 'destructive',
      });
      return;
    }

    setIsLoading(true);

    try {
      await register(formData.username, formData.email, formData.password, formData.inviteCode);
      toast({
        title: 'Conta criada',
        description: 'Bem-vindo ao Conselho! Você recebeu 5 códigos de convite.',
      });
      setLocation('/home');
    } catch (error) {
      toast({
        title: 'Erro no registro',
        description: error instanceof Error ? error.message : 'Não foi possível criar a conta',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 rounded-2xl bg-accent/10 flex items-center justify-center">
              <UserPlus className="w-8 h-8 text-accent" />
            </div>
          </div>
          <h1 className="text-4xl font-semibold tracking-tight mb-2">Criar Conta</h1>
          <p className="text-muted-foreground">Junte-se ao Conselho de Especialistas</p>
        </div>

        <div className="mb-6 p-4 rounded-xl bg-accent/5 border border-accent/20">
          <div className="flex gap-3">
            <Info className="w-5 h-5 text-accent shrink-0 mt-0.5" />
            <div className="text-sm">
              <p className="font-medium text-foreground mb-1">Sistema de convites</p>
              <p className="text-muted-foreground">
                É necessário um código de convite para criar uma conta. Ao se registrar, você receberá 5 códigos para convidar outras pessoas.
              </p>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="username">Nome de usuário</Label>
            <Input
              id="username"
              type="text"
              placeholder="seunome"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              required
              disabled={isLoading}
              className="rounded-xl"
              data-testid="input-username"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="seu@email.com"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
              disabled={isLoading}
              className="rounded-xl"
              data-testid="input-email"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Senha</Label>
            <Input
              id="password"
              type="password"
              placeholder="Mínimo 6 caracteres"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
              disabled={isLoading}
              className="rounded-xl"
              data-testid="input-password"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Confirmar senha</Label>
            <Input
              id="confirmPassword"
              type="password"
              placeholder="Digite a senha novamente"
              value={formData.confirmPassword}
              onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
              required
              disabled={isLoading}
              className="rounded-xl"
              data-testid="input-confirm-password"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="inviteCode">Código de convite</Label>
            <Input
              id="inviteCode"
              type="text"
              placeholder="ABC123XYZ"
              value={formData.inviteCode}
              onChange={(e) => setFormData({ ...formData, inviteCode: e.target.value.toUpperCase() })}
              required
              disabled={isLoading}
              className="rounded-xl font-mono tracking-wider"
              data-testid="input-invite-code"
            />
          </div>

          <Button
            type="submit"
            className="w-full rounded-xl"
            disabled={isLoading}
            data-testid="button-register"
          >
            {isLoading ? 'Criando conta...' : 'Criar conta'}
          </Button>
        </form>

        <div className="mt-8 text-center">
          <p className="text-sm text-muted-foreground">
            Já tem uma conta?{' '}
            <Link href="/login" className="text-accent font-medium hover:underline" data-testid="link-login">
              Fazer login
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
