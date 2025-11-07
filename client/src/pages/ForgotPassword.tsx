import { useState } from 'react';
import { Link } from 'wouter';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { KeyRound, ArrowLeft, Mail } from 'lucide-react';
import { apiRequest } from '@/lib/queryClient';

export default function ForgotPassword() {
  const { toast } = useToast();
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [emailSent, setEmailSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email) {
      toast({
        title: 'Email obrigatório',
        description: 'Por favor, informe seu email',
        variant: 'destructive',
      });
      return;
    }

    setIsLoading(true);

    try {
      await apiRequest('/api/auth/request-reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });

      setEmailSent(true);
      toast({
        title: 'Email enviado',
        description: 'Verifique sua caixa de entrada para instruções de redefinição',
      });
    } catch (error) {
      toast({
        title: 'Erro',
        description: error instanceof Error ? error.message : 'Não foi possível enviar o email',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (emailSent) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4 sm:px-6 py-8 sm:py-12">
        <div className="w-full max-w-md">
          <div className="text-center mb-6 sm:mb-8">
            <div className="flex justify-center mb-3 sm:mb-4">
              <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-accent/10 flex items-center justify-center">
                <Mail className="w-7 h-7 sm:w-8 sm:h-8 text-accent" />
              </div>
            </div>
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-semibold tracking-tight mb-2">Email Enviado</h1>
            <p className="text-sm sm:text-base text-muted-foreground">Verifique sua caixa de entrada</p>
          </div>

          <div className="mb-4 sm:mb-6 p-4 sm:p-6 rounded-2xl bg-accent/5 border border-accent/20">
            <p className="text-xs sm:text-sm text-foreground mb-3 sm:mb-4">
              Enviamos instruções de redefinição de senha para <strong>{email}</strong>
            </p>
            <p className="text-xs sm:text-sm text-muted-foreground">
              O link expira em 1 hora. Se você não receber o email, verifique sua pasta de spam ou tente novamente.
            </p>
          </div>

          <div className="space-y-3 sm:space-y-4">
            <Link href="/login">
              <Button
                variant="outline"
                className="w-full rounded-xl h-12"
                data-testid="button-back-to-login"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Voltar para o login
              </Button>
            </Link>
            <Button
              variant="ghost"
              className="w-full rounded-xl h-12"
              onClick={() => {
                setEmailSent(false);
                setEmail('');
              }}
              data-testid="button-try-again"
            >
              Enviar novamente
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 sm:px-6 py-8 sm:py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-6 sm:mb-8">
          <div className="flex justify-center mb-3 sm:mb-4">
            <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-accent/10 flex items-center justify-center">
              <KeyRound className="w-7 h-7 sm:w-8 sm:h-8 text-accent" />
            </div>
          </div>
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-semibold tracking-tight mb-2">Esqueceu a Senha?</h1>
          <p className="text-sm sm:text-base text-muted-foreground">Sem problema, vamos te ajudar a recuperá-la</p>
        </div>

        <div className="mb-4 sm:mb-6 p-3 sm:p-4 rounded-xl bg-muted/50">
          <p className="text-xs sm:text-sm text-muted-foreground">
            Digite seu email e enviaremos instruções para redefinir sua senha
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-6">
          <div className="space-y-2">
            <Label htmlFor="email" className="text-sm sm:text-base">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="seu@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={isLoading}
              className="rounded-xl h-12"
              data-testid="input-email"
            />
          </div>

          <Button
            type="submit"
            className="w-full rounded-xl h-12 sm:h-14 text-base sm:text-lg"
            disabled={isLoading}
            data-testid="button-send-reset"
          >
            {isLoading ? 'Enviando...' : 'Enviar instruções'}
          </Button>
        </form>

        <div className="mt-6 sm:mt-8 text-center">
          <Link href="/login">
            <Button
              variant="ghost"
              className="text-xs sm:text-sm h-auto py-2"
              data-testid="link-back-to-login"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Voltar para o login
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
