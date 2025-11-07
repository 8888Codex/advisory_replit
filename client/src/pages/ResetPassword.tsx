import { useState, useEffect } from 'react';
import { useLocation, Link } from 'wouter';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { KeyRound, Check } from 'lucide-react';
import { apiRequest } from '@/lib/queryClient';

export default function ResetPassword() {
  const [, navigate] = useLocation();
  const { toast } = useToast();
  const [token, setToken] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isVerifying, setIsVerifying] = useState(true);
  const [tokenValid, setTokenValid] = useState(false);
  const [resetComplete, setResetComplete] = useState(false);

  useEffect(() => {
    // Extract token from URL query params
    const params = new URLSearchParams(window.location.search);
    const urlToken = params.get('token');

    if (!urlToken) {
      toast({
        title: 'Link inválido',
        description: 'Token de redefinição não encontrado',
        variant: 'destructive',
      });
      navigate('/forgot-password');
      return;
    }

    setToken(urlToken);
    verifyToken(urlToken);
  }, []);

  const verifyToken = async (tokenToVerify: string) => {
    setIsVerifying(true);

    try {
      const response: { valid: boolean; email?: string } = await apiRequest('/api/auth/verify-reset-token', {
        method: 'POST',
        data: { token: tokenToVerify }
      });

      if (response.valid) {
        setTokenValid(true);
        setEmail(response.email || '');
      }
    } catch (error) {
      toast({
        title: 'Link inválido',
        description: error instanceof Error ? error.message : 'Este link expirou ou é inválido',
        variant: 'destructive',
      });
      setTimeout(() => navigate('/forgot-password'), 3000);
    } finally {
      setIsVerifying(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      toast({
        title: 'Erro de validação',
        description: 'As senhas não coincidem',
        variant: 'destructive',
      });
      return;
    }

    if (password.length < 6) {
      toast({
        title: 'Erro de validação',
        description: 'A senha deve ter pelo menos 6 caracteres',
        variant: 'destructive',
      });
      return;
    }

    setIsLoading(true);

    try {
      await apiRequest('/api/auth/reset-password', {
        method: 'POST',
        data: {
          token,
          newPassword: password
        }
      });

      setResetComplete(true);
      toast({
        title: 'Senha redefinida',
        description: 'Sua senha foi atualizada com sucesso',
      });

      // Redirect to login after 2 seconds
      setTimeout(() => navigate('/login'), 2000);
    } catch (error) {
      toast({
        title: 'Erro',
        description: error instanceof Error ? error.message : 'Não foi possível redefinir a senha',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (isVerifying) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-md text-center">
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 rounded-2xl bg-accent/10 flex items-center justify-center">
              <KeyRound className="w-8 h-8 text-accent animate-pulse" />
            </div>
          </div>
          <h1 className="text-2xl font-semibold tracking-tight mb-2">Verificando link...</h1>
          <p className="text-muted-foreground">Aguarde um momento</p>
        </div>
      </div>
    );
  }

  if (resetComplete) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 rounded-2xl bg-green-50 dark:bg-green-950 flex items-center justify-center">
                <Check className="w-8 h-8 text-green-500" />
              </div>
            </div>
            <h1 className="text-4xl font-semibold tracking-tight mb-2">Senha Redefinida</h1>
            <p className="text-muted-foreground">Sucesso! Redirecionando para o login...</p>
          </div>

          <div className="p-6 rounded-2xl bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-900">
            <p className="text-sm text-green-900 dark:text-green-100">
              Sua senha foi atualizada com sucesso. Você já pode fazer login com sua nova senha.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!tokenValid) {
    return null;
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 rounded-2xl bg-accent/10 flex items-center justify-center">
              <KeyRound className="w-8 h-8 text-accent" />
            </div>
          </div>
          <h1 className="text-4xl font-semibold tracking-tight mb-2">Nova Senha</h1>
          <p className="text-muted-foreground">Defina uma nova senha para sua conta</p>
        </div>

        {email && (
          <div className="mb-6 p-4 rounded-xl bg-muted/50">
            <p className="text-sm text-muted-foreground">
              Redefinindo senha para: <strong className="text-foreground">{email}</strong>
            </p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="password">Nova senha</Label>
            <Input
              id="password"
              type="password"
              placeholder="Mínimo 6 caracteres"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={isLoading}
              className="rounded-xl"
              data-testid="input-password"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Confirmar nova senha</Label>
            <Input
              id="confirmPassword"
              type="password"
              placeholder="Digite a senha novamente"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              disabled={isLoading}
              className="rounded-xl"
              data-testid="input-confirm-password"
            />
          </div>

          <Button
            type="submit"
            className="w-full rounded-xl"
            disabled={isLoading}
            data-testid="button-reset-password"
          >
            {isLoading ? 'Redefinindo...' : 'Redefinir senha'}
          </Button>
        </form>

        <div className="mt-8 text-center">
          <Link href="/login">
            <Button
              variant="ghost"
              className="text-sm"
              data-testid="link-back-to-login"
            >
              Voltar para o login
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
