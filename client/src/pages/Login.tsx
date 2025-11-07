import { useState } from 'react';
import { useLocation, Link } from 'wouter';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { LogIn } from 'lucide-react';

export default function Login() {
  const [, setLocation] = useLocation();
  const { login, isRateLimited } = useAuth();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await login(formData.email, formData.password);
      toast({
        title: 'Login realizado',
        description: 'Bem-vindo de volta ao Conselho.',
      });
      setLocation('/home');
    } catch (error) {
      toast({
        title: 'Erro no login',
        description: error instanceof Error ? error.message : 'Credenciais inválidas',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 sm:px-6 py-8 sm:py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-6 sm:mb-8">
          <div className="flex justify-center mb-3 sm:mb-4">
            <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-accent/10 flex items-center justify-center">
              <LogIn className="w-7 h-7 sm:w-8 sm:h-8 text-accent" />
            </div>
          </div>
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-semibold tracking-tight mb-2">Entrar no Conselho</h1>
          <p className="text-sm sm:text-base text-muted-foreground">Acesse seus especialistas em marketing</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-6">
          <div className="space-y-2">
            <Label htmlFor="email" className="text-sm sm:text-base">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="seu@email.com"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
              disabled={isLoading || isRateLimited}
              className="rounded-xl h-12"
              data-testid="input-email"
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between gap-2">
              <Label htmlFor="password" className="text-sm sm:text-base">Senha</Label>
              <Link href="/forgot-password" className="text-xs sm:text-sm text-accent hover:underline whitespace-nowrap" data-testid="link-forgot-password">
                Esqueceu a senha?
              </Link>
            </div>
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
              disabled={isLoading || isRateLimited}
              className="rounded-xl h-12"
              data-testid="input-password"
            />
          </div>

          <Button
            type="submit"
            className="w-full rounded-xl h-12 sm:h-14 text-base sm:text-lg"
            disabled={isLoading || isRateLimited}
            data-testid="button-login"
          >
            {isLoading ? 'Entrando...' : isRateLimited ? 'Aguarde...' : 'Entrar'}
          </Button>
        </form>

        <div className="mt-6 sm:mt-8 text-center">
          <p className="text-xs sm:text-sm text-muted-foreground">
            Não tem uma conta?{' '}
            <Link href="/register" className="text-accent font-medium hover:underline" data-testid="link-register">
              Criar conta
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
