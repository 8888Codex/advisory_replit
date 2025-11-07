import { useEffect } from "react";
import { useLocation, Link } from "wouter";
import { useQuery } from "@tanstack/react-query";
import { AnimatedPage } from "@/components/AnimatedPage";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Sparkles, TrendingUp, Users, ArrowRight } from "lucide-react";
import { motion } from "framer-motion";
import { useOnboardingComplete } from "@/hooks/use-onboarding-complete";
import { ExpertCard, type Expert as ExpertCardType } from "@/components/ExpertCard";

interface Expert {
  id: number;
  name: string;
  title: string;
  avatar?: string;
  category: string;
  expertise: string[];
}

export default function Home() {
  const [, setLocation] = useLocation();
  const { isComplete, isLoading: isLoadingOnboarding } = useOnboardingComplete();

  // Check if user has completed onboarding (now from PostgreSQL)
  useEffect(() => {
    if (!isLoadingOnboarding && !isComplete) {
      setLocation("/onboarding");
    }
  }, [isComplete, isLoadingOnboarding, setLocation]);

  const { data: experts = [], isLoading } = useQuery<Expert[]>({
    queryKey: ["/api/experts"],
  });

  // Get top 6 experts for quick access
  const featuredExperts = experts.slice(0, 6);

  // Convert local Expert type to ExpertCard type
  const convertToExpertCard = (expert: Expert): ExpertCardType => ({
    id: String(expert.id),
    name: expert.name,
    title: expert.title,
    expertise: expert.expertise,
    bio: "", // Bio will be hidden if empty (handled by ExpertCard)
    avatar: expert.avatar || null,
    category: expert.category,
  });

  return (
    <AnimatedPage>
      <div className="min-h-screen bg-background">
        <div className="container mx-auto px-4 py-8 sm:py-10 md:py-12">
          {/* Welcome Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="mb-8 sm:mb-10 md:mb-12"
          >
            <h1 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-semibold tracking-tight mb-2 sm:mb-3">
              Bem-vindo ao O Conselho
            </h1>
            <p className="text-sm sm:text-base md:text-lg text-muted-foreground">
              450+ anos de expertise em marketing esperando por você
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 mb-8 sm:mb-10 md:mb-12">
            {/* Quick Actions */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.1 }}
            >
              <Card className="rounded-2xl hover-elevate cursor-pointer" onClick={() => setLocation("/categories")}>
                <CardHeader className="p-4 sm:p-5 md:p-6">
                  <div className="flex items-center gap-2 sm:gap-3">
                    <div className="p-2 sm:p-3 rounded-xl bg-purple-50 dark:bg-purple-950 shrink-0">
                      <Users className="w-5 h-5 sm:w-6 sm:h-6 text-purple-500" />
                    </div>
                    <div>
                      <CardTitle className="text-base sm:text-lg md:text-xl">Explorar Categorias</CardTitle>
                      <CardDescription className="text-xs sm:text-sm">15 disciplinas disponíveis</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-4 sm:p-5 md:p-6 pt-0">
                  <p className="text-xs sm:text-sm text-muted-foreground mb-3 sm:mb-4">
                    Navegue por especialistas organizados por disciplina: Marketing, SEO, Growth Hacking e mais.
                  </p>
                  <Button variant="ghost" className="w-full justify-between rounded-xl h-10 sm:h-auto" data-testid="button-explore-categories">
                    Ver todas
                    <ArrowRight className="w-4 h-4" />
                  </Button>
                </CardContent>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.2 }}
            >
              <Card className="rounded-2xl hover-elevate cursor-pointer" onClick={() => setLocation("/test-council")}>
                <CardHeader className="p-4 sm:p-5 md:p-6">
                  <div className="flex items-center gap-2 sm:gap-3">
                    <div className="p-2 sm:p-3 rounded-xl bg-amber-50 dark:bg-amber-950 shrink-0">
                      <Sparkles className="w-5 h-5 sm:w-6 sm:h-6 text-amber-500" />
                    </div>
                    <div>
                      <CardTitle className="text-base sm:text-lg md:text-xl">Conselho Estratégico</CardTitle>
                      <CardDescription className="text-xs sm:text-sm">Múltiplos especialistas juntos</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-4 sm:p-5 md:p-6 pt-0">
                  <p className="text-xs sm:text-sm text-muted-foreground mb-3 sm:mb-4">
                    Reúna vários experts para analisar seu desafio de diferentes perspectivas.
                  </p>
                  <Button variant="ghost" className="w-full justify-between rounded-xl h-10 sm:h-auto" data-testid="button-council-room">
                    Iniciar sessão
                    <ArrowRight className="w-4 h-4" />
                  </Button>
                </CardContent>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.3 }}
            >
              <Card className="rounded-2xl hover-elevate cursor-pointer" onClick={() => setLocation("/personas")}>
                <CardHeader className="p-4 sm:p-5 md:p-6">
                  <div className="flex items-center gap-2 sm:gap-3">
                    <div className="p-2 sm:p-3 rounded-xl bg-blue-50 dark:bg-blue-950 shrink-0">
                      <TrendingUp className="w-5 h-5 sm:w-6 sm:h-6 text-blue-500" />
                    </div>
                    <div>
                      <CardTitle className="text-base sm:text-lg md:text-xl">Persona Builder</CardTitle>
                      <CardDescription className="text-xs sm:text-sm">Análise profunda de audiência</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="p-4 sm:p-5 md:p-6 pt-0">
                  <p className="text-xs sm:text-sm text-muted-foreground mb-3 sm:mb-4">
                    Crie perfis enriquecidos com dados reais do YouTube e insights estratégicos.
                  </p>
                  <Button variant="ghost" className="w-full justify-between rounded-xl h-10 sm:h-auto" data-testid="button-persona-builder">
                    Criar persona
                    <ArrowRight className="w-4 h-4" />
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* Featured Experts */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.4 }}
            className="mb-6 sm:mb-8"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4 mb-4 sm:mb-6">
              <div>
                <h2 className="text-xl sm:text-2xl font-semibold mb-1">Especialistas em Destaque</h2>
                <p className="text-sm sm:text-base text-muted-foreground">Acesso rápido aos principais experts</p>
              </div>
              <Link href="/categories">
                <Button variant="outline" className="rounded-xl gap-2 h-10 sm:h-auto w-full sm:w-auto" data-testid="link-view-all-experts">
                  Ver todos os 18
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
            </div>

            {isLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
                {[...Array(6)].map((_, i) => (
                  <Card key={i} className="rounded-2xl">
                    <CardContent className="p-4 sm:p-5 md:p-6">
                      <div className="animate-pulse">
                        <div className="w-10 h-10 sm:w-12 sm:h-12 bg-muted rounded-full mb-3 sm:mb-4" />
                        <div className="h-3 sm:h-4 bg-muted rounded w-3/4 mb-2" />
                        <div className="h-2 sm:h-3 bg-muted rounded w-1/2" />
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
                {featuredExperts.map((expert, index) => (
                  <ExpertCard
                    key={expert.id}
                    expert={convertToExpertCard(expert)}
                    variant="rich"
                    index={index}
                    onChat={() => setLocation(`/chat/${expert.id}`)}
                  />
                ))}
              </div>
            )}
          </motion.div>

          {/* Analytics Teaser */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.5 }}
          >
            <Card className="rounded-2xl border-accent/20 bg-accent/5">
              <CardContent className="p-4 sm:p-6 md:p-8">
                <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 sm:gap-6">
                  <div className="flex-1">
                    <h3 className="text-base sm:text-lg md:text-xl font-semibold mb-1 sm:mb-2">Acompanhe sua Evolução</h3>
                    <p className="text-xs sm:text-sm md:text-base text-muted-foreground">
                      Veja suas estatísticas de uso, experts mais consultados e recomendações personalizadas.
                    </p>
                  </div>
                  <Button
                    onClick={() => setLocation("/analytics")}
                    className="rounded-xl bg-accent hover:bg-accent text-white gap-2 px-4 sm:px-6 h-10 sm:h-auto w-full md:w-auto text-sm sm:text-base"
                    data-testid="button-analytics"
                  >
                    Ver Analytics
                    <TrendingUp className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </AnimatedPage>
  );
}
