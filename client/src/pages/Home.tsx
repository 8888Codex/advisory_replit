import { useEffect } from "react";
import { useLocation, Link } from "wouter";
import { useQuery } from "@tanstack/react-query";
import { AnimatedPage } from "@/components/AnimatedPage";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Sparkles, TrendingUp, Users, MessageSquare, ArrowRight, Star } from "lucide-react";
import { motion } from "framer-motion";

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

  // Check if user has completed onboarding
  useEffect(() => {
    const onboardingComplete = localStorage.getItem("onboarding_complete");
    
    if (!onboardingComplete) {
      setLocation("/onboarding");
    }
  }, [setLocation]);

  const { data: experts = [], isLoading } = useQuery<Expert[]>({
    queryKey: ["/api/experts"],
  });

  // Get top 6 experts for quick access
  const featuredExperts = experts.slice(0, 6);

  return (
    <AnimatedPage>
      <div className="min-h-screen bg-background">
        <div className="container mx-auto px-4 py-12">
          {/* Welcome Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="mb-12"
          >
            <h1 className="text-4xl md:text-5xl font-semibold tracking-tight mb-3">
              Bem-vindo ao O Conselho
            </h1>
            <p className="text-lg text-muted-foreground">
              450+ anos de expertise em marketing esperando por você
            </p>
          </motion.div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-12">
            {/* Quick Actions */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.1 }}
            >
              <Card className="rounded-2xl hover-elevate cursor-pointer" onClick={() => setLocation("/categories")}>
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="p-3 rounded-xl bg-accent/10">
                      <Users className="w-6 h-6 text-accent" />
                    </div>
                    <div>
                      <CardTitle className="text-xl">Explorar Categorias</CardTitle>
                      <CardDescription>15 disciplinas disponíveis</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-4">
                    Navegue por especialistas organizados por disciplina: Marketing, SEO, Growth Hacking e mais.
                  </p>
                  <Button variant="ghost" className="w-full justify-between rounded-xl" data-testid="button-explore-categories">
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
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="p-3 rounded-xl bg-accent/10">
                      <Sparkles className="w-6 h-6 text-accent" />
                    </div>
                    <div>
                      <CardTitle className="text-xl">Conselho Estratégico</CardTitle>
                      <CardDescription>Múltiplos especialistas juntos</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-4">
                    Reúna vários experts para analisar seu desafio de diferentes perspectivas.
                  </p>
                  <Button variant="ghost" className="w-full justify-between rounded-xl" data-testid="button-council-room">
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
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="p-3 rounded-xl bg-accent/10">
                      <TrendingUp className="w-6 h-6 text-accent" />
                    </div>
                    <div>
                      <CardTitle className="text-xl">Persona Builder</CardTitle>
                      <CardDescription>Análise profunda de audiência</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-4">
                    Crie perfis enriquecidos com dados reais do YouTube e insights estratégicos.
                  </p>
                  <Button variant="ghost" className="w-full justify-between rounded-xl" data-testid="button-persona-builder">
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
            className="mb-8"
          >
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-semibold mb-1">Especialistas em Destaque</h2>
                <p className="text-muted-foreground">Acesso rápido aos principais experts</p>
              </div>
              <Link href="/categories">
                <Button variant="outline" className="rounded-xl gap-2" data-testid="link-view-all-experts">
                  Ver todos os 18
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
            </div>

            {isLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[...Array(6)].map((_, i) => (
                  <Card key={i} className="rounded-2xl">
                    <CardContent className="p-6">
                      <div className="animate-pulse">
                        <div className="w-12 h-12 bg-muted rounded-full mb-4" />
                        <div className="h-4 bg-muted rounded w-3/4 mb-2" />
                        <div className="h-3 bg-muted rounded w-1/2" />
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {featuredExperts.map((expert, index) => (
                  <motion.div
                    key={expert.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: 0.1 * index }}
                  >
                    <Card
                      className="rounded-2xl hover-elevate cursor-pointer transition-all"
                      onClick={() => setLocation(`/chat/${expert.id}`)}
                      data-testid={`card-expert-${expert.id}`}
                    >
                      <CardContent className="p-6">
                        <div className="flex items-start gap-4 mb-4">
                          <Avatar className="w-14 h-14 ring-2 ring-border">
                            <AvatarImage src={expert.avatar} alt={expert.name} />
                            <AvatarFallback className="bg-accent/10 text-accent font-semibold">
                              {expert.name.split(" ").map(n => n[0]).join("").slice(0, 2)}
                            </AvatarFallback>
                          </Avatar>
                          <div className="flex-1">
                            <h3 className="font-semibold text-lg mb-1">{expert.name}</h3>
                            <p className="text-sm text-muted-foreground line-clamp-2">{expert.title}</p>
                          </div>
                        </div>
                        
                        <Badge variant="secondary" className="mb-3 rounded-lg">
                          {expert.category}
                        </Badge>

                        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
                          <Star className="w-4 h-4 fill-accent text-accent" />
                          <span>{expert.expertise.length}+ especialidades</span>
                        </div>

                        <Button
                          variant="ghost"
                          className="w-full rounded-xl gap-2"
                          data-testid={`button-chat-${expert.id}`}
                        >
                          <MessageSquare className="w-4 h-4" />
                          Iniciar conversa
                        </Button>
                      </CardContent>
                    </Card>
                  </motion.div>
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
              <CardContent className="p-8">
                <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold mb-2">Acompanhe sua Evolução</h3>
                    <p className="text-muted-foreground">
                      Veja suas estatísticas de uso, experts mais consultados e recomendações personalizadas.
                    </p>
                  </div>
                  <Button
                    onClick={() => setLocation("/analytics")}
                    className="rounded-xl bg-accent hover:bg-accent text-white gap-2 px-6"
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
