import { useState, useEffect } from "react";
import { useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/contexts/AuthContext";
import { AnimatedPage } from "@/components/AnimatedPage";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  TrendingUp,
  Users,
  Award,
  ChevronRight,
  ChevronLeft,
  MessageSquare,
  Calendar,
  Building2,
  Target,
  DollarSign,
  Package,
  Zap,
  Check,
  X,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import type { Expert } from "@shared/schema";
import { ExpertCard, type Expert as ExpertCardType } from "@/components/ExpertCard";

export default function Landing() {
  const [, setLocation] = useLocation();
  const { user, isLoading: isAuthLoading } = useAuth();
  const [tourIndex, setTourIndex] = useState(0);

  useEffect(() => {
    if (!isAuthLoading && user) {
      setLocation("/home");
    }
  }, [user, isAuthLoading, setLocation]);

  const handleConsult = (expertId: string) => {
    // Redirect to registration page
    setLocation("/register");
  };

  const { data: experts = [], isLoading } = useQuery<Expert[]>({
    queryKey: ["/api/experts"],
  });

  // Filter only seed experts (18 main legends with HIGH_FIDELITY type) and deduplicate by ID
  const marketingLegends = experts
    .filter((e) => e.expertType === "high_fidelity")
    .filter((expert, index, self) => 
      index === self.findIndex((e) => e.id === expert.id)
    );
  const totalYearsExperience = marketingLegends.length * 25;
  const currentExpert = marketingLegends[tourIndex];

  const expertInitials = currentExpert
    ? currentExpert.name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "";

  const impactStats = [
    {
      icon: DollarSign,
      value: "Bilhões",
      label: "Faturados Pelas Lendas",
      description: "Eugene Schwartz: U$1 BI só em copy",
    },
    {
      icon: Calendar,
      value: `${totalYearsExperience}+`,
      label: "Anos de Expertise Real",
      description: "Estratégias testadas desde 1967",
    },
    {
      icon: Users,
      value: "18",
      label: "Mentes Lendárias",
      description: "Não são influencers. São os inventores.",
    },
  ];

  return (
    <AnimatedPage>
      <div className="min-h-screen">
        {/* Hero Section - MATADOR */}
        <section className="relative w-full py-12 sm:py-16 md:py-24 lg:py-32 bg-gradient-to-b from-destructive/5 via-background to-background">
          <div className="container mx-auto px-4">
            <div className="max-w-6xl mx-auto text-center space-y-6 sm:space-y-8 md:space-y-10">
              
              {/* Headline Killer */}
              <motion.h1
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
                className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl xl:text-7xl font-semibold tracking-tight leading-[1.15] px-2"
              >
                <span className="text-destructive">Você Está Queimando Dinheiro</span>
                <br />
                em Marketing.
                <br />
                <span className="text-foreground">Eles Sabem Exatamente Onde.</span>
              </motion.h1>

              {/* Subheadline Agressivo */}
              <motion.p
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.1 }}
                className="text-base sm:text-lg md:text-xl lg:text-2xl text-muted-foreground max-w-4xl mx-auto leading-relaxed font-medium px-2"
              >
                18 mentes que faturaram <span className="text-accent font-semibold">BILHÕES</span> ensinando estratégias que funcionaram em 1967, 1983, 2005 e{" "}
                <span className="text-accent font-semibold">CONTINUAM funcionando hoje</span>.
              </motion.p>

              {/* Nomes das Lendas */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.2 }}
                className="flex flex-wrap justify-center gap-2 sm:gap-3 max-w-4xl mx-auto px-2"
              >
                {["Philip Kotler", "David Ogilvy", "Seth Godin", "Gary Vaynerchuk", "Eugene Schwartz", "Dan Kennedy"].map((name, idx) => (
                  <Badge key={idx} variant="outline" className="px-2 py-1 sm:px-3 sm:py-1.5 md:px-4 md:py-2 text-xs sm:text-sm md:text-base font-medium">
                    {name}
                  </Badge>
                ))}
                <Badge variant="outline" className="px-2 py-1 sm:px-3 sm:py-1.5 md:px-4 md:py-2 text-xs sm:text-sm md:text-base font-medium text-accent">
                  +12 Lendas
                </Badge>
              </motion.div>

              <motion.p
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.25 }}
                className="text-sm sm:text-base md:text-lg lg:text-xl text-muted-foreground px-2"
              >
                Respondendo <span className="text-accent font-semibold">SUAS perguntas</span>. Em português. Agora.
              </motion.p>

              {/* CTA Principal */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.3 }}
                className="pt-4 sm:pt-6"
              >
                <Button
                  size="lg"
                  className="gap-2 h-12 sm:h-14 md:h-16 px-6 sm:px-8 md:px-12 text-base sm:text-lg md:text-xl font-semibold w-full sm:w-auto"
                  onClick={() => setLocation("/register")}
                  data-testid="button-start-now"
                >
                  Parar de Adivinhar. Começar Agora
                  <ChevronRight className="h-4 w-4 sm:h-5 sm:w-5 md:h-6 md:w-6" />
                </Button>
                <p className="text-xs sm:text-sm text-muted-foreground mt-3 px-2">
                  ✓ Grátis ✓ Sem cartão ✓ Respostas em 30 segundos
                </p>
              </motion.div>
            </div>
          </div>
        </section>

        {/* Impact Stats */}
        <section className="w-full py-8 sm:py-12 md:py-16 bg-background">
          <div className="container mx-auto px-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 max-w-5xl mx-auto">
              {impactStats.map((stat, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: 0.2 + index * 0.05 }}
                >
                  <Card className="p-4 sm:p-6 md:p-8 text-center rounded-2xl">
                    <div className="inline-flex items-center justify-center w-12 h-12 sm:w-14 sm:h-14 md:w-16 md:h-16 rounded-full bg-muted mb-3 sm:mb-4">
                      <stat.icon className="h-6 w-6 sm:h-7 sm:w-7 md:h-8 md:w-8 text-muted-foreground" />
                    </div>
                    <div className="text-2xl sm:text-3xl md:text-4xl font-semibold mb-1 sm:mb-2">{stat.value}</div>
                    <h3 className="text-sm sm:text-base md:text-lg font-medium mb-1 sm:mb-2">{stat.label}</h3>
                    <p className="text-xs sm:text-sm text-muted-foreground">{stat.description}</p>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Problem-Agitate Section - DOR DO CLIENTE */}
        <section className="w-full py-10 sm:py-14 md:py-20 bg-destructive/5">
          <div className="container mx-auto px-4">
            <div className="max-w-6xl mx-auto">
              <motion.h2
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-semibold text-center mb-8 sm:mb-10 md:mb-12 px-2"
              >
                VOCÊ JÁ TENTOU:
              </motion.h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6 md:gap-8 mb-10 sm:mb-12 md:mb-16">
                {/* LADO ESQUERDO - Problemas */}
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 }}
                  className="space-y-3 sm:space-y-4 md:space-y-6"
                >
                  <Card className="p-4 sm:p-5 md:p-6 border-destructive/20 bg-destructive/5">
                    <div className="flex items-start gap-3 sm:gap-4">
                      <X className="h-6 w-6 sm:h-7 sm:w-7 md:h-8 md:w-8 text-destructive flex-shrink-0 mt-1" />
                      <div>
                        <h3 className="text-sm sm:text-base md:text-lg font-semibold mb-1 sm:mb-2 text-destructive">Curso de R$ 3.997 que não funcionou</h3>
                        <p className="text-xs sm:text-sm text-destructive/80">Você gastou uma grana, assistiu tudo, testou... e nada mudou.</p>
                      </div>
                    </div>
                  </Card>

                  <Card className="p-4 sm:p-5 md:p-6 border-destructive/20 bg-destructive/5">
                    <div className="flex items-start gap-3 sm:gap-4">
                      <X className="h-6 w-6 sm:h-7 sm:w-7 md:h-8 md:w-8 text-destructive flex-shrink-0 mt-1" />
                      <div>
                        <h3 className="text-sm sm:text-base md:text-lg font-semibold mb-1 sm:mb-2 text-destructive">Agência que prometeu "resultados garantidos"</h3>
                        <p className="text-xs sm:text-sm text-destructive/80">3 meses de contrato, orçamento queimado, apenas "relatórios bonitos".</p>
                      </div>
                    </div>
                  </Card>

                  <Card className="p-4 sm:p-5 md:p-6 border-destructive/20 bg-destructive/5">
                    <div className="flex items-start gap-3 sm:gap-4">
                      <X className="h-6 w-6 sm:h-7 sm:w-7 md:h-8 md:w-8 text-destructive flex-shrink-0 mt-1" />
                      <div>
                        <h3 className="text-sm sm:text-base md:text-lg font-semibold mb-1 sm:mb-2 text-destructive">Guru do Instagram vendendo fórmula mágica</h3>
                        <p className="text-xs sm:text-sm text-destructive/80">"Faça isso e fature 6 dígitos". Spoiler: não funcionou.</p>
                      </div>
                    </div>
                  </Card>

                  <Card className="p-4 sm:p-5 md:p-6 border-destructive/20 bg-destructive/5">
                    <div className="flex items-start gap-3 sm:gap-4">
                      <X className="h-6 w-6 sm:h-7 sm:w-7 md:h-8 md:w-8 text-destructive flex-shrink-0 mt-1" />
                      <div>
                        <h3 className="text-sm sm:text-base md:text-lg font-semibold mb-1 sm:mb-2 text-destructive">Copiar o que a concorrência faz</h3>
                        <p className="text-xs sm:text-sm text-destructive/80">Você tenta replicar, mas nunca alcança os mesmos resultados.</p>
                      </div>
                    </div>
                  </Card>
                </motion.div>

                {/* LADO DIREITO - Solução */}
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 }}
                  className="space-y-3 sm:space-y-4 md:space-y-6"
                >
                  <Card className="p-4 sm:p-5 md:p-6 border-emerald-500/50 bg-emerald-500/5">
                    <div className="flex items-start gap-3 sm:gap-4">
                      <Check className="h-6 w-6 sm:h-7 sm:w-7 md:h-8 md:w-8 text-emerald-500 flex-shrink-0 mt-1" />
                      <div>
                        <h3 className="text-sm sm:text-base md:text-lg font-semibold mb-1 sm:mb-2 text-emerald-600 dark:text-emerald-400">Philip Kotler analisa SEU posicionamento</h3>
                        <p className="text-xs sm:text-sm text-emerald-700/80 dark:text-emerald-300/80">O pai do marketing moderno respondendo VOCÊ diretamente.</p>
                      </div>
                    </div>
                  </Card>

                  <Card className="p-4 sm:p-5 md:p-6 border-emerald-500/50 bg-emerald-500/5">
                    <div className="flex items-start gap-3 sm:gap-4">
                      <Check className="h-6 w-6 sm:h-7 sm:w-7 md:h-8 md:w-8 text-emerald-500 flex-shrink-0 mt-1" />
                      <div>
                        <h3 className="text-sm sm:text-base md:text-lg font-semibold mb-1 sm:mb-2 text-emerald-600 dark:text-emerald-400">Eugene Schwartz valida sua copy</h3>
                        <p className="text-xs sm:text-sm text-emerald-700/80 dark:text-emerald-300/80">O homem que vendeu U$1 BI com palavras corrigindo SEU texto.</p>
                      </div>
                    </div>
                  </Card>

                  <Card className="p-4 sm:p-5 md:p-6 border-emerald-500/50 bg-emerald-500/5">
                    <div className="flex items-start gap-3 sm:gap-4">
                      <Check className="h-6 w-6 sm:h-7 sm:w-7 md:h-8 md:w-8 text-emerald-500 flex-shrink-0 mt-1" />
                      <div>
                        <h3 className="text-sm sm:text-base md:text-lg font-semibold mb-1 sm:mb-2 text-emerald-600 dark:text-emerald-400">Seth Godin testa sua ideia de campanha</h3>
                        <p className="text-xs sm:text-sm text-emerald-700/80 dark:text-emerald-300/80">21 best-sellers. Purple Cow. Tribos. Ele sabe se vai funcionar.</p>
                      </div>
                    </div>
                  </Card>

                  <Card className="p-4 sm:p-5 md:p-6 border-emerald-500/50 bg-emerald-500/5">
                    <div className="flex items-start gap-3 sm:gap-4">
                      <Check className="h-6 w-6 sm:h-7 sm:w-7 md:h-8 md:w-8 text-emerald-500 flex-shrink-0 mt-1" />
                      <div>
                        <h3 className="text-sm sm:text-base md:text-lg font-semibold mb-1 sm:mb-2 text-emerald-600 dark:text-emerald-400">Gary Vaynerchuk revisa seu social media</h3>
                        <p className="text-xs sm:text-sm text-emerald-700/80 dark:text-emerald-300/80">De $3M → $60M com conteúdo. Ele sabe o que viraliza.</p>
                      </div>
                    </div>
                  </Card>
                </motion.div>
              </div>

              {/* Texto de Impacto */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="text-center space-y-4 sm:space-y-6 px-2"
              >
                <p className="text-xl sm:text-2xl md:text-3xl font-semibold">
                  <span className="text-destructive">RESULTADO?</span> Frustração. Dinheiro jogado fora. Nada muda.
                </p>

                <div className="max-w-3xl mx-auto space-y-3 sm:space-y-4 text-sm sm:text-base md:text-lg text-muted-foreground">
                  <p className="font-semibold text-foreground">O PROBLEMA NÃO É VOCÊ.</p>
                  <p>É que você está pedindo conselho pra quem NUNCA fez funcionar de verdade.</p>
                  <p className="text-accent font-semibold text-base sm:text-lg md:text-xl lg:text-2xl">
                    E se você pudesse perguntar diretamente pro cara que INVENTOU o posicionamento? 
                    Pro cara que vendeu U$ 1 bilhão com uma carta de vendas? 
                    Pro cara que criou o conceito de tribo?
                  </p>
                  <p className="text-xl sm:text-2xl md:text-3xl font-bold text-foreground pt-2 sm:pt-4">
                    ELES ESTÃO AQUI. AGORA.
                  </p>
                </div>

                <Button
                  size="lg"
                  className="gap-2 h-12 sm:h-14 px-6 sm:px-8 md:px-10 text-base sm:text-lg mt-6 sm:mt-8"
                  onClick={() => setLocation("/register")}
                  data-testid="button-stop-guessing"
                >
                  Parar de Queimar Dinheiro
                  <ChevronRight className="h-4 w-4 sm:h-5 sm:w-5" />
                </Button>
              </motion.div>
            </div>
          </div>
        </section>

        {/* Timeline de Impacto */}
        <section className="w-full py-10 sm:py-14 md:py-20 bg-muted/20">
          <div className="container mx-auto px-4">
            <div className="text-center mb-8 sm:mb-10 md:mb-12 px-2">
              <motion.h2
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-semibold mb-3 sm:mb-4"
              >
                57 Anos de Inovação em Marketing. Grátis Para Começar.
              </motion.h2>
              <motion.p
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.05 }}
                className="text-sm sm:text-base md:text-lg text-muted-foreground max-w-2xl mx-auto"
              >
                De 1967 até hoje: converse com quem inventou as estratégias que você estuda.
              </motion.p>
            </div>

            <div className="max-w-5xl mx-auto space-y-3 sm:space-y-4 md:space-y-6">
              {[
                {
                  decade: "1967-1980",
                  title: "Fundações do Marketing Moderno",
                  experts: ["Philip Kotler", "Al Ries", "Jack Trout"],
                  impact: "Criaram os conceitos fundamentais: 4Ps, posicionamento, segmentação de mercado",
                },
                {
                  decade: "1980-2000",
                  title: "Era da Marca e Identidade",
                  experts: ["David Ogilvy", "Guy Kawasaki", "Jay Conrad Levinson"],
                  impact: "Revolucionaram branding, evangelismo de marca e guerrilla marketing para pequenas empresas",
                },
                {
                  decade: "2000-2015",
                  title: "Revolução Digital",
                  experts: ["Seth Godin", "Neil Patel", "Tim Ferriss"],
                  impact: "Transformaram marketing com tribos, SEO/growth hacking e produtividade estratégica",
                },
                {
                  decade: "2015-Hoje",
                  title: "Marketing de Conteúdo e Social",
                  experts: ["Gary Vaynerchuk", "Ann Handley", "Rand Fishkin"],
                  impact: "Dominaram conteúdo, mídias sociais e SEO transparente na era da atenção",
                },
              ].map((era, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.08 }}
                >
                  <Card className="p-4 sm:p-5 md:p-6 rounded-2xl">
                    <div className="flex items-start gap-3 sm:gap-4 md:gap-6">
                      <div className="flex-shrink-0 text-center">
                        <Badge variant="secondary" className="rounded-full px-2 py-1 sm:px-3 sm:py-1.5 md:px-4 md:py-1 mb-1 sm:mb-2 text-xs sm:text-sm">
                          {era.decade}
                        </Badge>
                      </div>
                      <div className="flex-1 space-y-1 sm:space-y-2">
                        <h3 className="text-base sm:text-lg md:text-xl font-semibold">{era.title}</h3>
                        <p className="text-xs sm:text-sm text-muted-foreground">
                          <span className="font-medium">Lendas: </span>
                          {era.experts.join(", ")}
                        </p>
                        <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                          {era.impact}
                        </p>
                      </div>
                    </div>
                  </Card>
                </motion.div>
              ))}
            </div>

            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.4 }}
              className="text-center mt-8 sm:mt-10 md:mt-12 px-2"
            >
              <p className="text-sm sm:text-base text-muted-foreground">
                Mais de 50 anos de inovação em marketing, agora em conversas instantâneas
              </p>
            </motion.div>
          </div>
        </section>

        {/* Como Funciona */}
        <section className="w-full py-10 sm:py-14 md:py-20 bg-background">
          <div className="container mx-auto px-4">
            <div className="text-center space-y-3 sm:space-y-4 mb-8 sm:mb-10 md:mb-12 px-2">
              <h2 className="text-2xl sm:text-3xl md:text-4xl font-semibold">
                Como Funciona a Clonagem Cognitiva?
              </h2>
              <p className="text-sm sm:text-base md:text-lg text-muted-foreground max-w-2xl mx-auto">
                3 passos simples separam você das maiores mentes do marketing mundial
              </p>
            </div>

            {/* 3 Steps */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4 md:gap-6 max-w-5xl mx-auto mb-10 sm:mb-12 md:mb-16">
              {[
                {
                  step: "1",
                  icon: Users,
                  title: "Escolha Sua Lenda",
                  description: "Navegue por 18 especialistas. De Philip Kotler a Gary Vaynerchuk.",
                },
                {
                  step: "2",
                  icon: MessageSquare,
                  title: "Faça Sua Pergunta",
                  description: "Descreva seu desafio real. Em português, naturalmente.",
                },
                {
                  step: "3",
                  icon: Zap,
                  title: "Receba Insight em 30 Segundos",
                  description: "95% de fidelidade autêntica. Já consultado por +1.000 profissionais.",
                },
              ].map((item, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 + index * 0.1, duration: 0.3 }}
                  className="text-center space-y-3 sm:space-y-4"
                >
                  <div className="inline-flex items-center justify-center w-12 h-12 sm:w-14 sm:h-14 md:w-16 md:h-16 rounded-full bg-muted">
                    <item.icon className="h-6 w-6 sm:h-7 sm:w-7 md:h-8 md:w-8 text-muted-foreground" />
                  </div>
                  <div className="space-y-1 sm:space-y-2">
                    <div className="text-xs sm:text-sm font-medium text-accent">Passo {item.step}</div>
                    <h3 className="text-base sm:text-lg md:text-xl font-semibold">{item.title}</h3>
                    <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed px-2">
                      {item.description}
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* IA Genérica vs Clone Perfeito */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4 max-w-5xl mx-auto">
              <Card className="p-4 sm:p-5 md:p-6 rounded-2xl bg-background border-border">
                <div className="space-y-3 sm:space-y-4">
                  <div className="flex items-center gap-2 sm:gap-3">
                    <div className="flex items-center justify-center w-8 h-8 sm:w-9 sm:h-9 md:w-10 md:h-10 rounded-full bg-destructive/10">
                      <X className="h-4 w-4 sm:h-5 sm:w-5 text-destructive" />
                    </div>
                    <h4 className="text-base sm:text-lg font-semibold">IA Genérica</h4>
                  </div>
                  <ul className="space-y-2 sm:space-y-3 text-xs sm:text-sm text-muted-foreground">
                    <li className="flex gap-2">
                      <span className="text-destructive flex-shrink-0">×</span>
                      <span>Respostas superficiais e genéricas</span>
                    </li>
                    <li className="flex gap-2">
                      <span className="text-destructive flex-shrink-0">×</span>
                      <span>Ignora contexto histórico e nuances</span>
                    </li>
                    <li className="flex gap-2">
                      <span className="text-destructive flex-shrink-0">×</span>
                      <span>Não reflete estilo de pensamento único</span>
                    </li>
                    <li className="flex gap-2">
                      <span className="text-destructive flex-shrink-0">×</span>
                      <span>Soa como Wikipedia genérica</span>
                    </li>
                  </ul>
                </div>
              </Card>

              <Card className="p-4 sm:p-5 md:p-6 rounded-2xl bg-accent/5 border-accent/20">
                <div className="space-y-3 sm:space-y-4">
                  <div className="flex items-center gap-2 sm:gap-3">
                    <div className="flex items-center justify-center w-8 h-8 sm:w-9 sm:h-9 md:w-10 md:h-10 rounded-full bg-accent/20">
                      <Check className="h-4 w-4 sm:h-5 sm:w-5 text-accent" />
                    </div>
                    <h4 className="text-base sm:text-lg font-semibold">Clone Cognitivo</h4>
                  </div>
                  <ul className="space-y-2 sm:space-y-3 text-xs sm:text-sm text-muted-foreground">
                    <li className="flex gap-2">
                      <span className="text-accent flex-shrink-0">✓</span>
                      <span>Fala com a voz única de cada lenda</span>
                    </li>
                    <li className="flex gap-2">
                      <span className="text-accent flex-shrink-0">✓</span>
                      <span>Cita casos reais e controvérsias históricas</span>
                    </li>
                    <li className="flex gap-2">
                      <span className="text-accent flex-shrink-0">✓</span>
                      <span>Usa padrões de raciocínio autênticos</span>
                    </li>
                    <li className="flex gap-2">
                      <span className="text-accent flex-shrink-0">✓</span>
                      <span>Como se estivessem vivos na sua frente</span>
                    </li>
                  </ul>
                </div>
              </Card>
            </div>

            {/* Badge "Como Se Estivessem Vivos" */}
            <div className="text-center pt-8 sm:pt-10 md:pt-12 px-2">
              <div className="inline-flex items-center gap-2 px-3 py-2 sm:px-4 sm:py-2.5 md:px-6 md:py-3 rounded-full bg-muted border border-border/50">
                <Award className="h-4 w-4 sm:h-5 sm:w-5 text-accent" />
                <span className="text-xs sm:text-sm font-medium">Como Se Estivessem Vivos na Sua Frente</span>
              </div>
              <p className="text-xs sm:text-sm text-muted-foreground mt-3 sm:mt-4 max-w-2xl mx-auto">
                Respostas que capturam não só conhecimento, mas o jeito único de pensar de cada lenda
              </p>
              <div className="mt-4 sm:mt-5 md:mt-6 p-3 sm:p-4 bg-muted/30 rounded-lg border border-border/30 max-w-2xl mx-auto">
                <p className="text-xs sm:text-sm text-muted-foreground italic leading-relaxed">
                  Philip Kotler não diria "use redes sociais". Ele diria: <span className="text-foreground font-medium">"Segmente por psicografia, não demografia. Depois teste canais."</span>
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Tour Interativo das 18 Lendas */}
        <section id="tour-section" className="w-full py-10 sm:py-14 md:py-20 bg-muted/20">
          <div className="container mx-auto px-4">
            <div className="text-center mb-8 sm:mb-10 md:mb-12 px-2">
              <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-semibold mb-3 sm:mb-4">
                18 Lendas. 450+ Anos. 30 Segundos Para Respostas.
              </h2>
              <p className="text-sm sm:text-base md:text-lg text-muted-foreground max-w-2xl mx-auto">
                Escolha sua lenda. Descreva seu desafio. Receba insights que livros não ensinam.
              </p>
            </div>

            {isLoading ? (
              <div className="text-center py-12">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  className="inline-block"
                >
                  <Sparkles className="h-8 w-8 text-accent" />
                </motion.div>
                <p className="text-muted-foreground mt-4">Carregando especialistas...</p>
              </div>
            ) : marketingLegends.length === 0 ? (
              <Card className="p-8 max-w-xl mx-auto text-center">
                <p className="text-muted-foreground">Nenhum especialista disponível no momento</p>
              </Card>
            ) : (
              <div className="max-w-4xl mx-auto">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={tourIndex}
                    initial={{ opacity: 0, x: 100 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -100 }}
                    transition={{ duration: 0.3 }}
                  >
                    <div className="relative">
                      {/* Progress Bar */}
                      <div className="flex gap-1 sm:gap-2 mb-6 sm:mb-7 md:mb-8">
                        {marketingLegends.map((_, idx) => (
                          <div
                            key={idx}
                            className={`h-1.5 flex-1 rounded-full transition-colors duration-200 ${
                              idx <= tourIndex ? "bg-accent" : "bg-muted"
                            }`}
                          />
                        ))}
                      </div>

                      {/* Expert Card with Chat Button */}
                      <ExpertCard
                        expert={currentExpert}
                        variant="rich"
                        index={tourIndex}
                        onChat={handleConsult}
                      />

                      {/* Navigation */}
                      <div className="flex justify-between items-center mt-6 sm:mt-7 md:mt-8 pt-6 sm:pt-7 md:pt-8 border-t">
                        <Button
                          variant="ghost"
                          onClick={() => setTourIndex(Math.max(0, tourIndex - 1))}
                          disabled={tourIndex === 0}
                          data-testid="button-tour-previous"
                          className="h-12 sm:h-auto"
                        >
                          <ChevronLeft className="h-4 w-4 mr-1" />
                          Anterior
                        </Button>

                        <span className="text-xs sm:text-sm text-muted-foreground">
                          {tourIndex + 1} de {marketingLegends.length}
                        </span>

                        {tourIndex < marketingLegends.length - 1 ? (
                          <Button
                            variant="ghost"
                            onClick={() => setTourIndex(tourIndex + 1)}
                            data-testid="button-tour-next"
                            className="h-12 sm:h-auto"
                          >
                            Próximo
                            <ChevronRight className="h-4 w-4 ml-1" />
                          </Button>
                        ) : (
                          <Button
                            onClick={() => setLocation("/register")}
                            data-testid="button-complete-tour"
                            className="h-12 sm:h-auto"
                          >
                            Continuar
                            <ChevronRight className="h-4 w-4 ml-1" />
                          </Button>
                        )}
                      </div>
                    </div>
                  </motion.div>
                </AnimatePresence>
              </div>
            )}
          </div>
        </section>

        {/* ROSTER DAS LENDAS - Grid Completo */}
        <section className="w-full py-12 sm:py-16 md:py-20 lg:py-24 bg-background">
          <div className="container mx-auto px-4">
            <div className="text-center mb-10 sm:mb-12 md:mb-16 px-2">
              <motion.h2
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-semibold mb-4 sm:mb-5 md:mb-6"
              >
                CONHEÇA AS <span className="text-accent">18 LENDAS</span>
              </motion.h2>
              <motion.p
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="text-sm sm:text-base md:text-lg lg:text-xl text-muted-foreground max-w-4xl mx-auto"
              >
                Não são influencers. Não são "especialistas auto-proclamados". São os inventores. Os que faturaram bilhões. Os que escreveram os livros que todo mundo copia.
              </motion.p>
            </div>

            {/* Grid de Experts - Using Unified ExpertCard */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 md:gap-6 max-w-7xl mx-auto">
              {marketingLegends.map((expert, idx) => (
                <ExpertCard
                  key={expert.id}
                  expert={{
                    id: String(expert.id),
                    name: expert.name,
                    title: expert.title,
                    expertise: expert.expertise,
                    bio: expert.bio,
                    avatar: expert.avatar || null,
                    category: expert.category,
                  }}
                  variant="rich"
                  index={idx}
                  onChat={() => handleConsult(expert.id)}
                />
              ))}
            </div>

            {/* Stats de Impacto */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="mt-10 sm:mt-12 md:mt-16 text-center space-y-6 sm:space-y-8 px-2"
            >
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-5 md:gap-6 max-w-4xl mx-auto">
                <div className="space-y-1 sm:space-y-2">
                  <div className="text-3xl sm:text-4xl md:text-5xl font-bold text-accent">{totalYearsExperience}+</div>
                  <p className="text-sm sm:text-base md:text-lg text-muted-foreground">Anos de Expertise Real</p>
                </div>
                <div className="space-y-1 sm:space-y-2">
                  <div className="text-3xl sm:text-4xl md:text-5xl font-bold text-accent">Bilhões</div>
                  <p className="text-sm sm:text-base md:text-lg text-muted-foreground">Faturados Combinados</p>
                </div>
                <div className="space-y-1 sm:space-y-2">
                  <div className="text-3xl sm:text-4xl md:text-5xl font-bold text-accent">18</div>
                  <p className="text-sm sm:text-base md:text-lg text-muted-foreground">Mentes Que Mudaram o Marketing</p>
                </div>
              </div>

              <div className="max-w-3xl mx-auto space-y-3 sm:space-y-4">
                <p className="text-base sm:text-lg md:text-xl lg:text-2xl text-foreground font-semibold">
                  Eles INVENTARAM as estratégias que os gurus de hoje COPIAM.
                </p>
                <p className="text-sm sm:text-base md:text-lg text-muted-foreground">
                  Philip Kotler criou os 4Ps. Eugene Schwartz vendeu U$1 BI com copy. Seth Godin inventou o conceito de tribo. Gary Vaynerchuk dominou social media antes de virar moda.
                </p>
              </div>

              <Button
                size="lg"
                className="gap-2 h-12 sm:h-14 md:h-16 px-6 sm:px-8 md:px-12 text-base sm:text-lg md:text-xl font-semibold mt-6 sm:mt-8 w-full sm:w-auto"
                onClick={() => setLocation("/register")}
                data-testid="button-meet-legends"
              >
                Consultar as Lendas Agora
                <ChevronRight className="h-4 w-4 sm:h-5 sm:w-5 md:h-6 md:w-6" />
              </Button>
            </motion.div>
          </div>
        </section>

        {/* Perguntas Concretas */}
        <section className="w-full py-10 sm:py-14 md:py-20 bg-muted/20">
          <div className="container mx-auto px-4">
            <div className="text-center mb-8 sm:mb-10 md:mb-12 px-2">
              <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-semibold mb-3 sm:mb-4">
                Perguntas Que Cada Lenda Responde
              </h2>
              <p className="text-sm sm:text-base md:text-lg text-muted-foreground max-w-2xl mx-auto">
                Exemplos reais de como consultar cada especialista.
                Faça suas próprias perguntas ou use essas como inspiração.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4 max-w-6xl mx-auto">
              {[
                {
                  expert: "Philip Kotler",
                  title: "Pai do Marketing Moderno",
                  questions: [
                    "Como segmentar meu mercado B2B de forma eficaz?",
                    "Qual estratégia de precificação maximiza valor percebido?",
                    "Como aplicar os 4Ps em produtos digitais?",
                  ],
                },
                {
                  expert: "Seth Godin",
                  title: "Visionário das Tribos",
                  questions: [
                    "Como criar uma tribo engajada ao redor da minha marca?",
                    "Qual a diferença entre marketing de permissão e interrupção?",
                    "Como ser notável (remarkable) num mercado saturado?",
                  ],
                },
                {
                  expert: "Gary Vaynerchuk",
                  title: "Rei do Marketing de Conteúdo",
                  questions: [
                    "Qual plataforma social devo priorizar em 2025?",
                    "Como produzir conteúdo autêntico que vende sem ser vendedor?",
                    "Estratégia de 'jab, jab, jab, right hook' para meu nicho?",
                  ],
                },
                {
                  expert: "Neil Patel",
                  title: "Growth Hacker Legendário",
                  questions: [
                    "Como rankear no Google para palavras-chave competitivas?",
                    "Qual estratégia de link building funciona hoje?",
                    "Como otimizar taxa de conversão do meu funil?",
                  ],
                },
                {
                  expert: "Al Ries",
                  title: "Mestre do Posicionamento",
                  questions: [
                    "Como posicionar minha startup em mercado dominado?",
                    "Lei da categoria: devo criar nova categoria ou competir?",
                    "Como simplificar mensagem para ocupar mente do consumidor?",
                  ],
                },
                {
                  expert: "Ann Handley",
                  title: "Rainha do Content Marketing",
                  questions: [
                    "Como escrever emails que convertem sem parecer spam?",
                    "Qual estrutura de storytelling funciona para B2B?",
                    "Como criar conteúdo que educa e vende simultaneamente?",
                  ],
                },
              ].map((item, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.25, delay: index * 0.05 }}
                >
                  <Card className="p-4 sm:p-5 md:p-6 h-full rounded-2xl">
                    <div className="space-y-3 sm:space-y-4">
                      <div>
                        <h3 className="font-semibold text-base sm:text-lg mb-1">{item.expert}</h3>
                        <p className="text-xs sm:text-sm text-muted-foreground">{item.title}</p>
                      </div>
                      <div className="space-y-1.5 sm:space-y-2">
                        {item.questions.map((question, qIndex) => (
                          <div key={qIndex} className="flex gap-2 text-xs sm:text-sm">
                            <span className="text-accent flex-shrink-0">•</span>
                            <span className="text-muted-foreground leading-relaxed">
                              "{question}"
                            </span>
                          </div>
                        ))}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="w-full gap-2 mt-2 h-12 sm:h-auto"
                        onClick={() => {
                          const expert = marketingLegends.find((e) => e.name === item.expert);
                          if (expert) setLocation(`/chat/${expert.id}`);
                        }}
                        data-testid={`button-ask-${item.expert.toLowerCase().replace(/\s+/g, "-")}`}
                      >
                        <MessageSquare className="h-4 w-4" />
                        Perguntar para {item.expert.split(" ")[0]}
                      </Button>
                    </div>
                  </Card>
                </motion.div>
              ))}
            </div>

            <div className="text-center mt-8 sm:mt-10 md:mt-12 px-2">
              <p className="text-xs sm:text-sm text-muted-foreground">
                David Aaker (Branding), Jay Levinson (Guerrilla), Donald Miller (StoryBrand), Robert Cialdini (Persuasão) e +8 outros prontos para consulta.
              </p>
            </div>
          </div>
        </section>

        {/* CTA FINAL GIGANTE - IMPOSSÍVEL DE IGNORAR */}
        <section className="relative w-full py-16 sm:py-20 md:py-32 lg:py-40 bg-gradient-to-b from-background via-accent/5 to-destructive/10 overflow-hidden">
          {/* Background Pattern */}
            <div className="absolute inset-0 opacity-5">
              <div className="absolute inset-0 bg-gradient-to-br from-accent to-destructive" />
            </div>

            <div className="container mx-auto px-4 relative z-10">
              <div className="max-w-5xl mx-auto text-center space-y-8 sm:space-y-10 md:space-y-12">
                
                {/* Urgência Máxima */}
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.5 }}
                  className="space-y-4 sm:space-y-6 px-2"
                >
                  <div className="inline-flex items-center gap-2 px-3 py-2 sm:px-4 sm:py-2.5 md:px-6 md:py-3 rounded-full bg-destructive/10 border border-destructive/20">
                    <Zap className="h-4 w-4 sm:h-5 sm:w-5 text-destructive" />
                    <span className="text-xs sm:text-sm font-semibold text-destructive uppercase tracking-wide">
                      CADA MINUTO PERDIDO = DINHEIRO NA MESA
                    </span>
                  </div>

                  <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-bold leading-tight">
                    <span className="text-foreground">Se Você Não Testar Isso,</span>
                    <br />
                    <span className="text-destructive">Você É Louco.</span>
                  </h2>

                  <div className="max-w-3xl mx-auto space-y-4 sm:space-y-6">
                    <p className="text-base sm:text-lg md:text-xl lg:text-2xl font-semibold text-foreground">
                      ZERO RISCO. 100% GRÁTIS. 30 SEGUNDOS PARA COMEÇAR.
                    </p>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 text-left">
                      <Card className="p-4 sm:p-5 md:p-6 bg-background/50 backdrop-blur border-accent/20">
                        <div className="flex items-center gap-2 sm:gap-3 mb-2 sm:mb-3">
                          <Check className="h-5 w-5 sm:h-6 sm:w-6 text-accent flex-shrink-0" />
                          <h3 className="text-sm sm:text-base font-semibold">Sem Cartão</h3>
                        </div>
                        <p className="text-xs sm:text-sm text-muted-foreground">Nem pedimos. Comece agora mesmo.</p>
                      </Card>

                      <Card className="p-4 sm:p-5 md:p-6 bg-background/50 backdrop-blur border-accent/20">
                        <div className="flex items-center gap-2 sm:gap-3 mb-2 sm:mb-3">
                          <Check className="h-5 w-5 sm:h-6 sm:w-6 text-accent flex-shrink-0" />
                          <h3 className="text-sm sm:text-base font-semibold">100% Grátis</h3>
                        </div>
                        <p className="text-xs sm:text-sm text-muted-foreground">Primeira consulta. Zero custo. Zero pegadinha.</p>
                      </Card>

                      <Card className="p-4 sm:p-5 md:p-6 bg-background/50 backdrop-blur border-accent/20">
                        <div className="flex items-center gap-2 sm:gap-3 mb-2 sm:mb-3">
                          <Check className="h-5 w-5 sm:h-6 sm:w-6 text-accent flex-shrink-0" />
                          <h3 className="text-sm sm:text-base font-semibold">30 Segundos</h3>
                        </div>
                        <p className="text-xs sm:text-sm text-muted-foreground">Respostas rápidas. Insights imediatos.</p>
                      </Card>
                    </div>
                  </div>
                </motion.div>

                {/* The Big Ask */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3, duration: 0.5 }}
                  className="space-y-6 sm:space-y-8 pt-6 sm:pt-8 px-2"
                >
                  <div className="max-w-3xl mx-auto space-y-3 sm:space-y-4 text-sm sm:text-base md:text-lg text-muted-foreground">
                    <p className="font-semibold text-foreground text-base sm:text-lg md:text-xl lg:text-2xl">
                      Você já desperdiçou dinheiro com curso que não funcionou.
                    </p>
                    <p className="font-semibold text-foreground text-base sm:text-lg md:text-xl lg:text-2xl">
                      Você já pagou agência que não entregou.
                    </p>
                    <p className="font-semibold text-foreground text-base sm:text-lg md:text-xl lg:text-2xl">
                      Você já seguiu guru que só queria vender.
                    </p>
                    <p className="text-lg sm:text-xl md:text-2xl lg:text-3xl font-bold text-accent pt-4 sm:pt-6">
                      E SE... você pudesse perguntar diretamente pro cara que INVENTOU o que você precisa?
                    </p>
                  </div>

                  {/* CTA Gigante */}
                  <div className="space-y-3 sm:space-y-4">
                    <Button
                      size="lg"
                      onClick={() => setLocation("/register")}
                      className="gap-2 sm:gap-3 h-14 sm:h-16 md:h-20 px-8 sm:px-12 md:px-16 text-base sm:text-lg md:text-xl lg:text-2xl font-bold shadow-2xl hover:shadow-accent/20 transition-all duration-300 w-full sm:w-auto"
                      data-testid="button-final-cta-giant"
                    >
                      COMEÇAR AGORA (100% GRÁTIS)
                      <ChevronRight className="h-5 w-5 sm:h-6 sm:w-6 md:h-8 md:w-8" />
                    </Button>

                    <div className="flex flex-wrap justify-center gap-3 sm:gap-4 text-xs sm:text-sm text-muted-foreground">
                      <div className="flex items-center gap-1.5 sm:gap-2">
                        <Check className="h-3 w-3 sm:h-4 sm:w-4 text-accent" />
                        <span>Sem cartão de crédito</span>
                      </div>
                      <div className="flex items-center gap-1.5 sm:gap-2">
                        <Check className="h-3 w-3 sm:h-4 sm:w-4 text-accent" />
                        <span>Primeira consulta grátis</span>
                      </div>
                      <div className="flex items-center gap-1.5 sm:gap-2">
                        <Check className="h-3 w-3 sm:h-4 sm:w-4 text-accent" />
                        <span>18 lendas disponíveis</span>
                      </div>
                      <div className="flex items-center gap-1.5 sm:gap-2">
                        <Check className="h-3 w-3 sm:h-4 sm:w-4 text-accent" />
                        <span>Respostas em 30s</span>
                      </div>
                    </div>
                  </div>

                  {/* Final Blow */}
                  <div className="pt-6 sm:pt-8 max-w-2xl mx-auto">
                    <p className="text-base sm:text-lg md:text-xl lg:text-2xl text-foreground italic font-medium">
                      "O maior erro não é tentar e falhar. É não tentar quando não custa nada."
                    </p>
                    <p className="text-sm sm:text-base md:text-lg text-muted-foreground mt-3 sm:mt-4">
                      — Philip Kotler (provavelmente diria algo assim)
                    </p>
                  </div>
                </motion.div>
              </div>
            </div>
          </section>
      </div>
    </AnimatedPage>
  );
}
