import { useState } from "react";
import { useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
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
  Send,
} from "lucide-react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { apiRequestJson, queryClient } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";
import type { Expert } from "@shared/schema";

interface ProfileFormData {
  companyName: string;
  industry: string;
  companySize: string;
  targetAudience: string;
  mainProducts: string;
  channels: string[];
  budgetRange: string;
  primaryGoal: string;
  mainChallenge: string;
  timeline: string;
}

export default function Landing() {
  const [, setLocation] = useLocation();
  const { toast } = useToast();
  const [showProfileForm, setShowProfileForm] = useState(false);
  const [tourIndex, setTourIndex] = useState(0);
  const [profileData, setProfileData] = useState<ProfileFormData>({
    companyName: "",
    industry: "",
    companySize: "",
    targetAudience: "",
    mainProducts: "",
    channels: [],
    budgetRange: "",
    primaryGoal: "",
    mainChallenge: "",
    timeline: "",
  });

  const handleConsult = (expertId: string) => {
    // Check if user completed onboarding
    const onboardingComplete = localStorage.getItem("onboarding_complete");
    
    if (!onboardingComplete) {
      // Redirect to onboarding first
      setLocation("/onboarding");
    } else {
      // Go directly to chat
      setLocation(`/chat/${expertId}`);
    }
  };

  const { data: experts = [], isLoading } = useQuery<Expert[]>({
    queryKey: ["/api/experts"],
  });

  const marketingLegends = experts.filter((e) => e.expertise && e.expertise.length > 0);
  const totalYearsExperience = marketingLegends.length * 25;
  const currentExpert = marketingLegends[tourIndex];

  const saveProfileMutation = useMutation({
    mutationFn: async (data: ProfileFormData) => {
      return await apiRequestJson("/api/profile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/profile"] });
      localStorage.setItem("onboarding_complete", "true");
      toast({
        title: "Perfil Salvo com Sucesso!",
        description: "Sua consultoria personalizada está pronta. Bem-vindo ao O Conselho!",
      });
      setLocation("/home");
    },
    onError: () => {
      toast({
        title: "Erro ao salvar perfil",
        description: "Tente novamente.",
        variant: "destructive",
      });
    },
  });

  const handleProfileSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    saveProfileMutation.mutate(profileData);
  };

  const updateProfileField = (field: keyof ProfileFormData, value: any) => {
    setProfileData((prev) => ({ ...prev, [field]: value }));
  };

  const toggleChannel = (channel: string) => {
    setProfileData((prev) => ({
      ...prev,
      channels: prev.channels.includes(channel)
        ? prev.channels.filter((c) => c !== channel)
        : [...prev.channels, channel],
    }));
  };

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
      icon: Users,
      value: "18",
      label: "Lendas do Marketing",
      description: "De Philip Kotler a Gary Vaynerchuk",
    },
    {
      icon: Calendar,
      value: `${totalYearsExperience}+`,
      label: "Anos de Expertise",
      description: "Consultas respondidas em português",
    },
    {
      icon: Award,
      value: "95%",
      label: "Fidelidade Autêntica",
      description: "Testado por usuários reais em comparação cega",
    },
  ];

  return (
    <AnimatedPage>
      <div className="min-h-screen">
        {/* Hero Section */}
        <section className="relative w-full py-20 md:py-28 bg-gradient-to-b from-muted/30 to-background">
          <div className="container mx-auto px-4">
            <div className="max-w-5xl mx-auto text-center space-y-8">
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-full bg-muted border border-border/50"
              >
                <Sparkles className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium text-muted-foreground">
                  18 Lendas do Marketing Mundial
                </span>
              </motion.div>

              <motion.h1
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.05 }}
                className="text-5xl md:text-6xl lg:text-7xl font-semibold tracking-tight leading-tight"
              >
                <span className="text-accent">450+ Anos de Expertise</span> em Marketing.
                <br />
                Agora em Uma Conversa.
              </motion.h1>

              <motion.p
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.1 }}
                className="text-xl md:text-2xl text-muted-foreground max-w-3xl mx-auto leading-relaxed"
              >
                De Philip Kotler a Gary Vaynerchuk. Consulte as maiores mentes do marketing como se estivessem vivos na sua frente.
              </motion.p>

              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.15 }}
                className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-4"
              >
                <Button
                  size="lg"
                  className="gap-2"
                  onClick={() => {
                    document.getElementById("tour-section")?.scrollIntoView({ behavior: "smooth" });
                  }}
                  data-testid="button-explore-experts"
                >
                  Explorar Especialistas
                  <ChevronRight className="h-5 w-5" />
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  onClick={() => setLocation("/create")}
                  data-testid="button-create-expert"
                >
                  Criar Seu Especialista
                </Button>
              </motion.div>
            </div>
          </div>
        </section>

        {/* Impact Stats */}
        <section className="w-full py-16 bg-background">
          <div className="container mx-auto px-4">
            <div className="grid md:grid-cols-3 gap-4 max-w-5xl mx-auto">
              {impactStats.map((stat, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: 0.2 + index * 0.05 }}
                >
                  <Card className="p-8 text-center rounded-2xl">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-muted mb-4">
                      <stat.icon className="h-8 w-8 text-muted-foreground" />
                    </div>
                    <div className="text-4xl font-semibold mb-2">{stat.value}</div>
                    <h3 className="text-lg font-medium mb-2">{stat.label}</h3>
                    <p className="text-sm text-muted-foreground">{stat.description}</p>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Timeline de Impacto */}
        <section className="w-full py-20 bg-muted/20">
          <div className="container mx-auto px-4">
            <div className="text-center mb-12">
              <motion.h2
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className="text-4xl md:text-5xl font-semibold mb-4"
              >
                57 Anos de Inovação em Marketing. Grátis Para Começar.
              </motion.h2>
              <motion.p
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: 0.05 }}
                className="text-lg text-muted-foreground max-w-2xl mx-auto"
              >
                De 1967 até hoje: converse com quem inventou as estratégias que você estuda.
              </motion.p>
            </div>

            <div className="max-w-5xl mx-auto space-y-6">
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
                  <Card className="p-6 rounded-2xl">
                    <div className="flex items-start gap-6">
                      <div className="flex-shrink-0 text-center">
                        <Badge variant="secondary" className="rounded-full px-4 py-1 mb-2">
                          {era.decade}
                        </Badge>
                      </div>
                      <div className="flex-1 space-y-2">
                        <h3 className="text-xl font-semibold">{era.title}</h3>
                        <p className="text-sm text-muted-foreground">
                          <span className="font-medium">Lendas: </span>
                          {era.experts.join(", ")}
                        </p>
                        <p className="text-sm text-muted-foreground leading-relaxed">
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
              className="text-center mt-12"
            >
              <p className="text-muted-foreground">
                Mais de 50 anos de inovação em marketing, agora em conversas instantâneas
              </p>
            </motion.div>
          </div>
        </section>

        {/* Como Funciona */}
        <section className="w-full py-20 bg-background">
          <div className="container mx-auto px-4">
            <div className="text-center space-y-4 mb-12">
              <h2 className="text-3xl md:text-4xl font-semibold">
                Como Funciona a Clonagem Cognitiva?
              </h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                3 passos simples separam você das maiores mentes do marketing mundial
              </p>
            </div>

            {/* 3 Steps */}
            <div className="grid md:grid-cols-3 gap-4 max-w-5xl mx-auto mb-16">
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
                  className="text-center space-y-4"
                >
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-muted">
                    <item.icon className="h-8 w-8 text-muted-foreground" />
                  </div>
                  <div className="space-y-2">
                    <div className="text-sm font-medium text-accent">Passo {item.step}</div>
                    <h3 className="text-xl font-semibold">{item.title}</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {item.description}
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* IA Genérica vs Clone Perfeito */}
            <div className="grid md:grid-cols-2 gap-4 max-w-5xl mx-auto">
              <Card className="p-6 rounded-2xl bg-background border-border">
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center w-10 h-10 rounded-full bg-destructive/10">
                      <X className="h-5 w-5 text-destructive" />
                    </div>
                    <h4 className="text-lg font-semibold">IA Genérica</h4>
                  </div>
                  <ul className="space-y-3 text-sm text-muted-foreground">
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

              <Card className="p-6 rounded-2xl bg-accent/5 border-accent/20">
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center w-10 h-10 rounded-full bg-accent/20">
                      <Check className="h-5 w-5 text-accent" />
                    </div>
                    <h4 className="text-lg font-semibold">Clone Cognitivo</h4>
                  </div>
                  <ul className="space-y-3 text-sm text-muted-foreground">
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
            <div className="text-center pt-12">
              <div className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-muted border border-border/50">
                <Award className="h-5 w-5 text-accent" />
                <span className="text-sm font-medium">Como Se Estivessem Vivos na Sua Frente</span>
              </div>
              <p className="text-sm text-muted-foreground mt-4 max-w-2xl mx-auto">
                Respostas que capturam não só conhecimento, mas o jeito único de pensar de cada lenda
              </p>
              <div className="mt-6 p-4 bg-muted/30 rounded-lg border border-border/30 max-w-2xl mx-auto">
                <p className="text-sm text-muted-foreground italic leading-relaxed">
                  Philip Kotler não diria "use redes sociais". Ele diria: <span className="text-foreground font-medium">"Segmente por psicografia, não demografia. Depois teste canais."</span>
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Tour Interativo das 18 Lendas */}
        <section id="tour-section" className="w-full py-20 bg-muted/20">
          <div className="container mx-auto px-4">
            <div className="text-center mb-12">
              <h2 className="text-4xl md:text-5xl font-semibold mb-4">
                18 Lendas. 450+ Anos. 30 Segundos Para Respostas.
              </h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
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
                    <Card className="p-8 rounded-2xl">
                      {/* Progress Bar */}
                      <div className="flex gap-2 mb-8">
                        {marketingLegends.map((_, idx) => (
                          <div
                            key={idx}
                            className={`h-1.5 flex-1 rounded-full transition-colors duration-200 ${
                              idx <= tourIndex ? "bg-accent" : "bg-muted"
                            }`}
                          />
                        ))}
                      </div>

                      {/* Expert Content */}
                      <div className="flex flex-col md:flex-row gap-8 items-start">
                        <div className="flex-shrink-0 mx-auto md:mx-0">
                          <Avatar className="h-32 w-32 border-4 border-accent/20">
                            <AvatarImage src={currentExpert.avatar || undefined} alt={currentExpert.name} />
                            <AvatarFallback className="text-3xl font-semibold bg-accent/10">
                              {expertInitials}
                            </AvatarFallback>
                          </Avatar>
                        </div>

                        <div className="flex-1 space-y-4 text-center md:text-left">
                          <div>
                            <h3 className="text-2xl font-semibold mb-2">{currentExpert.name}</h3>
                            <p className="text-lg text-muted-foreground mb-4">{currentExpert.title}</p>
                          </div>

                          <div className="flex flex-wrap gap-2 justify-center md:justify-start">
                            {currentExpert.expertise.slice(0, 4).map((skill, idx) => (
                              <Badge key={idx} variant="secondary" className="rounded-full">
                                {skill}
                              </Badge>
                            ))}
                          </div>

                          <p className="text-sm text-muted-foreground leading-relaxed">
                            {currentExpert.bio}
                          </p>

                          <Button
                            onClick={() => handleConsult(currentExpert.id)}
                            className="gap-2"
                            data-testid={`button-chat-${currentExpert.id}`}
                          >
                            <MessageSquare className="h-4 w-4" />
                            Conversar com {currentExpert.name.split(" ")[0]}
                          </Button>
                        </div>
                      </div>

                      {/* Navigation */}
                      <div className="flex justify-between items-center mt-8 pt-8 border-t">
                        <Button
                          variant="ghost"
                          onClick={() => setTourIndex(Math.max(0, tourIndex - 1))}
                          disabled={tourIndex === 0}
                          data-testid="button-tour-previous"
                        >
                          <ChevronLeft className="h-4 w-4 mr-1" />
                          Anterior
                        </Button>

                        <span className="text-sm text-muted-foreground">
                          {tourIndex + 1} de {marketingLegends.length}
                        </span>

                        {tourIndex < marketingLegends.length - 1 ? (
                          <Button
                            variant="ghost"
                            onClick={() => setTourIndex(tourIndex + 1)}
                            data-testid="button-tour-next"
                          >
                            Próximo
                            <ChevronRight className="h-4 w-4 ml-1" />
                          </Button>
                        ) : (
                          <Button
                            onClick={() => setShowProfileForm(true)}
                            data-testid="button-complete-tour"
                          >
                            Continuar
                            <ChevronRight className="h-4 w-4 ml-1" />
                          </Button>
                        )}
                      </div>
                    </Card>
                  </motion.div>
                </AnimatePresence>
              </div>
            )}
          </div>
        </section>

        {/* Perguntas Concretas */}
        <section className="w-full py-20 bg-background">
          <div className="container mx-auto px-4">
            <div className="text-center mb-12">
              <h2 className="text-4xl md:text-5xl font-semibold mb-4">
                Perguntas Que Cada Lenda Responde
              </h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Exemplos reais de como consultar cada especialista.
                Faça suas próprias perguntas ou use essas como inspiração.
              </p>
            </div>

            <div className="grid md:grid-cols-2 gap-4 max-w-6xl mx-auto">
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
                  <Card className="p-6 h-full rounded-2xl">
                    <div className="space-y-4">
                      <div>
                        <h3 className="font-semibold text-lg mb-1">{item.expert}</h3>
                        <p className="text-sm text-muted-foreground">{item.title}</p>
                      </div>
                      <div className="space-y-2">
                        {item.questions.map((question, qIndex) => (
                          <div key={qIndex} className="flex gap-2 text-sm">
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
                        className="w-full gap-2 mt-2"
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

            <div className="text-center mt-12">
              <p className="text-sm text-muted-foreground mb-4">
                David Aaker (Branding), Jay Levinson (Guerrilla), Donald Miller (StoryBrand), Robert Cialdini (Persuasão) e +8 outros prontos para consulta.
              </p>
            </div>
          </div>
        </section>

        {/* Formulário de Perfil */}
        {showProfileForm && (
          <section className="w-full py-20 bg-muted/20">
            <div className="container mx-auto px-4">
              <div className="max-w-3xl mx-auto">
                <div className="text-center mb-12">
                  <h2 className="text-4xl md:text-5xl font-semibold mb-4">
                    1 Minuto Para Descobrir Qual Lenda Pode 10x Seu Marketing
                  </h2>
                  <p className="text-lg text-muted-foreground">
                    Responda 4 perguntas. Receba recomendações personalizadas de especialistas que dominam seu desafio específico.
                  </p>
                </div>

                <Card className="p-8 rounded-2xl">
                  <form onSubmit={handleProfileSubmit} className="space-y-6">
                    <div className="grid md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="companyName">Nome da Empresa</Label>
                        <Input
                          id="companyName"
                          value={profileData.companyName}
                          onChange={(e) => updateProfileField("companyName", e.target.value)}
                          placeholder="Sua empresa"
                          required
                          data-testid="input-company-name"
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="industry">Indústria</Label>
                        <Select
                          value={profileData.industry}
                          onValueChange={(value) => updateProfileField("industry", value)}
                          required
                        >
                          <SelectTrigger id="industry" data-testid="select-industry">
                            <SelectValue placeholder="Selecione" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="Tecnologia">Tecnologia</SelectItem>
                            <SelectItem value="E-commerce">E-commerce</SelectItem>
                            <SelectItem value="Saúde">Saúde</SelectItem>
                            <SelectItem value="Educação">Educação</SelectItem>
                            <SelectItem value="Finanças">Finanças</SelectItem>
                            <SelectItem value="Serviços">Serviços</SelectItem>
                            <SelectItem value="Varejo">Varejo</SelectItem>
                            <SelectItem value="Outro">Outro</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="companySize">Tamanho da Empresa</Label>
                        <Select
                          value={profileData.companySize}
                          onValueChange={(value) => updateProfileField("companySize", value)}
                          required
                        >
                          <SelectTrigger id="companySize" data-testid="select-company-size">
                            <SelectValue placeholder="Selecione" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="1-10">1-10 funcionários</SelectItem>
                            <SelectItem value="11-50">11-50 funcionários</SelectItem>
                            <SelectItem value="51-200">51-200 funcionários</SelectItem>
                            <SelectItem value="201-1000">201-1000 funcionários</SelectItem>
                            <SelectItem value="1000+">1000+ funcionários</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="primaryGoal">Objetivo Principal</Label>
                        <Select
                          value={profileData.primaryGoal}
                          onValueChange={(value) => updateProfileField("primaryGoal", value)}
                          required
                        >
                          <SelectTrigger id="primaryGoal" data-testid="select-primary-goal">
                            <SelectValue placeholder="Selecione" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="aumentar-vendas">Aumentar Vendas</SelectItem>
                            <SelectItem value="brand-awareness">Brand Awareness</SelectItem>
                            <SelectItem value="gerar-leads">Gerar Leads</SelectItem>
                            <SelectItem value="engagement">Engagement</SelectItem>
                            <SelectItem value="lancamento">Lançamento de Produto</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="mainChallenge">Principal Desafio</Label>
                      <Textarea
                        id="mainChallenge"
                        value={profileData.mainChallenge}
                        onChange={(e) => updateProfileField("mainChallenge", e.target.value)}
                        placeholder="Descreva seu maior desafio de marketing..."
                        rows={4}
                        required
                        data-testid="textarea-main-challenge"
                      />
                    </div>

                    <Button
                      type="submit"
                      size="lg"
                      className="w-full gap-2"
                      disabled={saveProfileMutation.isPending}
                      data-testid="button-submit-profile"
                    >
                      {saveProfileMutation.isPending ? (
                        <>
                          <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                          >
                            <Sparkles className="h-5 w-5" />
                          </motion.div>
                          Salvando...
                        </>
                      ) : (
                        <>
                          <Send className="h-5 w-5" />
                          Começar Minha Jornada Premium
                        </>
                      )}
                    </Button>

                    <p className="text-center text-sm text-muted-foreground">
                      Você poderá atualizar essas informações a qualquer momento
                    </p>
                  </form>
                </Card>
              </div>
            </div>
          </section>
        )}

        {/* Final CTA */}
        {!showProfileForm && (
          <section className="w-full py-20 bg-background">
            <div className="container mx-auto px-4">
              <div className="max-w-3xl mx-auto text-center space-y-6">
                <h2 className="text-4xl md:text-5xl font-semibold">
                  Sua Próxima Decisão de Marketing Vale Milhões. Consulte Quem Domina Isso.
                </h2>
                <p className="text-lg text-muted-foreground">
                  Grátis para começar. 30 segundos para primeiras respostas. 18 lendas disponíveis agora.
                </p>
                <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-4">
                  <Button
                    size="lg"
                    onClick={() => setLocation("/onboarding")}
                    className="gap-2"
                    data-testid="button-final-cta"
                  >
                    Começar Consultoria Grátis
                    <ChevronRight className="h-5 w-5" />
                  </Button>
                  <Button
                    size="lg"
                    variant="outline"
                    onClick={() => setLocation("/create")}
                    data-testid="button-final-create"
                  >
                    Criar Meu Especialista
                  </Button>
                </div>
              </div>
            </div>
          </section>
        )}
      </div>
    </AnimatedPage>
  );
}
