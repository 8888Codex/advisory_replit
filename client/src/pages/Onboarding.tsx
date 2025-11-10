import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient, useQuery } from "@tanstack/react-query";
import { useLocation } from "wouter";
import { Building2, Users, Target, Zap, CheckCircle2, Clock, Sparkles, TrendingUp } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { insertUserPersonaSchema, type OnboardingStatus } from "@shared/schema";
import { apiRequest } from "@/lib/queryClient";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { z } from "zod";

const onboardingSchema = insertUserPersonaSchema.extend({
  userId: z.string().default("default_user"),
  companyName: z.string().optional(),
  industry: z.string().min(1, "Setor é obrigatório"),
  companySize: z.string().min(1, "Tamanho da empresa é obrigatório"),
  targetAudience: z.string().min(50, "Descreva seu público-alvo com pelo menos 50 caracteres"),
  primaryGoal: z.string().min(1, "Objetivo principal é obrigatório"),
  mainChallenge: z.string().min(30, "Descreva seu desafio com pelo menos 30 caracteres"),
  enrichmentLevel: z.enum(["quick", "strategic", "complete"]).default("quick"),
});

type OnboardingFormData = z.infer<typeof onboardingSchema>;

const STEPS = [
  { id: 1, title: "Sobre Seu Negócio", icon: Building2 },
  { id: 2, title: "Seu Público-Alvo", icon: Users },
  { id: 3, title: "Objetivos & Desafios", icon: Target },
  { id: 4, title: "Nível de Enriquecimento", icon: Sparkles },
];

const ENRICHMENT_LEVELS = [
  {
    id: "quick",
    name: "Quick",
    duration: "~30-45s",
    description: "Análise essencial e rápida",
    modules: 3,
    features: [
      "Núcleo Psicográfico (valores, medos)",
      "Jornada do Comprador (gatilhos, objeções)",
      "Insights Estratégicos (mensagem central)",
    ],
    icon: Zap,
  },
  {
    id: "strategic",
    name: "Strategic",
    duration: "~2-3min",
    description: "Análise intermediária (Recomendado)",
    modules: 6,
    features: [
      "Tudo do Quick +",
      "Perfil Comportamental (Cialdini)",
      "Linguagem & Comunicação (StoryBrand)",
      "Jobs-to-be-Done (funcional, emocional)",
    ],
    icon: TrendingUp,
    recommended: true,
  },
  {
    id: "complete",
    name: "Complete",
    duration: "~5-7min",
    description: "Análise completa com todos especialistas",
    modules: 8,
    features: [
      "Tudo do Strategic +",
      "Perfil de Decisão (critérios, velocidade)",
      "Exemplos de Copy Prontos (headline, email)",
      "YouTube research + 18 especialistas",
    ],
    icon: Sparkles,
  },
];

const pageVariants = {
  initial: { opacity: 0, x: 20 },
  animate: { opacity: 1, x: 0, transition: { duration: 0.3, ease: "easeOut" } },
  exit: { opacity: 0, x: -20, transition: { duration: 0.2, ease: "easeIn" } },
};

export default function Onboarding() {
  const [step, setStep] = useState(1);
  const [, navigate] = useLocation();
  const { toast} = useToast();
  const queryClient = useQueryClient();

  const form = useForm<OnboardingFormData>({
    resolver: zodResolver(onboardingSchema),
    defaultValues: {
      userId: "default_user",
      companyName: "",
      industry: "",
      companySize: "",
      targetAudience: "",
      primaryGoal: "",
      mainChallenge: "",
      enrichmentLevel: "quick",
    },
  });

  // Load onboarding status on mount (to resume progress)
  const { data: onboardingStatus, isLoading: isLoadingStatus } = useQuery<OnboardingStatus | null>({
    queryKey: ["/api/onboarding/status"],
    retry: false, // Don't retry if user hasn't started onboarding yet
    queryFn: async () => {
      try {
        const res = await fetch("/api/onboarding/status", {
          credentials: "include",
        });
        
        // Se não autenticado ou não encontrado, retorna null (não é erro)
        if (res.status === 401 || res.status === 404) {
          return null;
        }
        
        if (!res.ok) {
          throw new Error(`${res.status}: ${await res.text()}`);
        }
        
        return await res.json();
      } catch (error) {
        console.log("[ONBOARDING] Failed to load status, starting fresh:", error);
        return null;
      }
    },
  });

  // Populate form and step when onboarding status is loaded
  useEffect(() => {
    if (onboardingStatus && onboardingStatus.completedAt === null) {
      // Resume onboarding from saved progress (incomplete onboarding)
      console.log("[ONBOARDING] Resuming incomplete onboarding...");
      form.reset({
        userId: "default_user",
        companyName: onboardingStatus.companyName || "",
        industry: onboardingStatus.industry || "",
        companySize: onboardingStatus.companySize || "",
        targetAudience: onboardingStatus.targetAudience || "",
        primaryGoal: onboardingStatus.goals?.[0] || "",
        mainChallenge: onboardingStatus.mainChallenge || "",
        enrichmentLevel: onboardingStatus.enrichmentLevel || "quick",
      });
      // Resume from next step after last saved
      setStep(Math.min((onboardingStatus.currentStep || 0) + 1, 4));
    } else if (onboardingStatus && onboardingStatus.completedAt) {
      // Onboarding already completed - start fresh for new persona
      console.log("[ONBOARDING] Onboarding completed. Starting fresh for new persona.");
      form.reset({
        userId: "default_user",
        companyName: "",
        industry: "",
        companySize: "",
        targetAudience: "",
        primaryGoal: "",
        mainChallenge: "",
        enrichmentLevel: "quick",
      });
      setStep(1);
    }
    // NOTA: Permite criar múltiplas personas mesmo após onboarding completo
  }, [onboardingStatus, form]);

  // Save onboarding progress mutation (called on each step)
  const saveProgressMutation = useMutation({
    mutationFn: async (data: Partial<OnboardingFormData> & { currentStep: number }) => {
      return await apiRequest("/api/onboarding/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          currentStep: data.currentStep,
          companyName: data.companyName,
          industry: data.industry,
          companySize: data.companySize,
          targetAudience: data.targetAudience,
          goals: data.primaryGoal ? [data.primaryGoal] : undefined,
          mainChallenge: data.mainChallenge,
          enrichmentLevel: data.enrichmentLevel,
        }),
      });
    },
  });

  // Complete onboarding mutation
  const completeOnboardingMutation = useMutation({
    mutationFn: async () => {
      return await apiRequest("/api/onboarding/complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
    },
    onSuccess: () => {
      // Invalidate status query so useOnboardingComplete hook sees the change
      queryClient.invalidateQueries({ queryKey: ["/api/onboarding/status"] });
    },
  });

  const saveMutation = useMutation({
    mutationFn: async (data: OnboardingFormData) => {
      console.log("[ONBOARDING] saveMutation.mutationFn called, posting to /api/persona/create");
      console.log("[ONBOARDING] Data being sent:", data);
      const response = await apiRequest("/api/persona/create", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });
      const persona = await response.json();
      console.log("[ONBOARDING] Persona created successfully:", persona);
      return persona;
    },
    onSuccess: async (persona: any, data: OnboardingFormData) => {
      try {
        console.log("[ONBOARDING] saveMutation.onSuccess START, persona:", persona);
        
        // Mark onboarding as completed (fire and forget)
        console.log("[ONBOARDING] Marking onboarding as complete...");
        completeOnboardingMutation.mutate();
        
        // Dispatch background enrichment (fire and forget)
        console.log("[ONBOARDING] Starting background enrichment...");
        apiRequest("/api/persona/enrich/background", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            personaId: persona.id,
            mode: data.enrichmentLevel || "quick",
          }),
        }).then(() => {
          console.log("[ONBOARDING] Background enrichment dispatched successfully");
        }).catch((error) => {
          console.error("[ONBOARDING] Background enrichment dispatch failed:", error);
        });
        
        console.log("[ONBOARDING] Invalidating queries...");
        queryClient.invalidateQueries({ queryKey: ["/api/persona/current"] });
        
        console.log("[ONBOARDING] Showing toast...");
        toast({
          title: "Perfil criado com sucesso!",
          description: "Estamos enriquecendo sua persona em segundo plano. Você já pode usar a plataforma!",
        });
        
        console.log("[ONBOARDING] About to call navigate('/home')...");
        console.log("[ONBOARDING] Navigate function:", typeof navigate, navigate);
        navigate("/home");
        console.log("[ONBOARDING] Navigate called successfully");
      } catch (error) {
        console.error("[ONBOARDING] ERROR in onSuccess:", error);
        // Still try to navigate even if something fails
        try {
          navigate("/home");
        } catch (navError) {
          console.error("[ONBOARDING] Failed to navigate:", navError);
        }
      }
    },
    onError: (error: Error) => {
      console.error("[ONBOARDING] saveMutation.onError:", error);
      toast({
        title: "Erro ao salvar perfil",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const onSubmit = async (data: OnboardingFormData) => {
    console.log("[ONBOARDING] onSubmit called with data:", data);
    try {
      await saveMutation.mutateAsync(data);
    } catch (error) {
      console.error("[ONBOARDING] onSubmit failed:", error);
    }
  };

  const handleNext = async () => {
    const fieldsToValidate = getStepFields(step);
    console.log("[ONBOARDING] handleNext called, step:", step, "fields to validate:", fieldsToValidate);
    const isValid = await form.trigger(fieldsToValidate);
    console.log("[ONBOARDING] Validation result:", isValid, "errors:", form.formState.errors);
    
    if (isValid) {
      // Save progress before moving to next step
      const formData = form.getValues();
      console.log("[ONBOARDING] Form data:", formData);
      await saveProgressMutation.mutateAsync({
        ...formData,
        currentStep: step,
      });
      
      if (step < 4) {
        console.log("[ONBOARDING] Moving to next step");
        setStep(step + 1);
      } else {
        console.log("[ONBOARDING] Final step - calling onSubmit to create persona");
        form.handleSubmit(onSubmit)();
      }
    } else {
      console.log("[ONBOARDING] Validation failed!");
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1);
    }
  };

  const getStepFields = (currentStep: number): (keyof OnboardingFormData)[] => {
    switch (currentStep) {
      case 1:
        return ["industry", "companySize"];
      case 2:
        return ["targetAudience"];
      case 3:
        return ["primaryGoal", "mainChallenge"];
      case 4:
        return ["enrichmentLevel"];
      default:
        return [];
    }
  };

  const progress = (step / STEPS.length) * 100;

  return (
    <div className="min-h-screen flex items-center justify-center p-6 lg:p-8">
      <Card className="w-full max-w-3xl rounded-2xl border border-border/50">
        <CardContent className="p-8 lg:p-10">
          <div className="mb-8">
            <h1 className="text-4xl font-semibold tracking-tight mb-2">
              Bem-vindo ao O Conselho
            </h1>
            <p className="text-muted-foreground">
              Configure seu perfil para análises personalizadas do Conselho de Clones
            </p>
          </div>

          <div className="space-y-6 mb-8">
            <Progress value={progress} className="h-1.5" data-testid="progress-onboarding" />
            <div className="flex justify-between gap-2">
              {STEPS.map((s, idx) => {
                const Icon = s.icon;
                const isActive = step === s.id;
                const isCompleted = step > s.id;
                
                return (
                  <div key={s.id} className="flex items-center gap-3 flex-1">
                    <div
                      className={`flex items-center justify-center w-10 h-10 rounded-full transition-all duration-200 ${
                        isCompleted
                          ? "bg-accent text-white"
                          : isActive
                          ? "bg-accent text-white"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {isCompleted ? (
                        <CheckCircle2 className="w-5 h-5" />
                      ) : (
                        <Icon className="w-5 h-5" />
                      )}
                    </div>
                    <div className="hidden md:block flex-1">
                      <p className={`text-sm font-medium ${isActive ? "text-foreground" : "text-muted-foreground"}`}>
                        {s.title}
                      </p>
                    </div>
                    {idx < STEPS.length - 1 && (
                      <div className="hidden md:block h-px flex-1 bg-border" />
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
              <AnimatePresence mode="wait">
                {step === 1 && (
                  <motion.div
                    key="step1"
                    variants={pageVariants}
                    initial="initial"
                    animate="animate"
                    exit="exit"
                    className="space-y-6"
                  >
                    <FormField
                      control={form.control}
                      name="companyName"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-base font-medium">Nome da Empresa (Opcional)</FormLabel>
                          <FormControl>
                            <Input 
                              placeholder="Ex: Minha Empresa Ltda" 
                              {...field} 
                              className="rounded-xl"
                              data-testid="input-company-name"
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="industry"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-base font-medium">Setor / Indústria *</FormLabel>
                          <FormControl>
                            <Input 
                              placeholder="Ex: E-commerce de moda, SaaS, Consultoria..." 
                              {...field} 
                              className="rounded-xl"
                              data-testid="input-industry"
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="companySize"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-base font-medium">Tamanho da Empresa *</FormLabel>
                          <Select onValueChange={field.onChange} value={field.value} defaultValue={field.value}>
                            <FormControl>
                              <SelectTrigger className="rounded-xl" data-testid="select-company-size">
                                <SelectValue placeholder="Selecione o tamanho..." />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="1-10">1-10 funcionários</SelectItem>
                              <SelectItem value="11-50">11-50 funcionários</SelectItem>
                              <SelectItem value="51-200">51-200 funcionários</SelectItem>
                              <SelectItem value="201-1000">201-1000 funcionários</SelectItem>
                              <SelectItem value="1000+">Mais de 1000 funcionários</SelectItem>
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </motion.div>
                )}

                {step === 2 && (
                  <motion.div
                    key="step2"
                    variants={pageVariants}
                    initial="initial"
                    animate="animate"
                    exit="exit"
                    className="space-y-6"
                  >
                    <FormField
                      control={form.control}
                      name="targetAudience"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-base font-medium">Descreva Seu Público-Alvo *</FormLabel>
                          <FormDescription>
                            Seja específico: idade, localização, interesses, comportamentos, valores...
                          </FormDescription>
                          <FormControl>
                            <Textarea 
                              placeholder="Ex: Mulheres entre 25-35 anos, urbanas, classe A/B, interessadas em moda sustentável e consciente. Valorizam qualidade sobre quantidade, engajadas nas redes sociais, e procuram marcas com propósito alinhado aos seus valores..." 
                              {...field} 
                              rows={8}
                              className="rounded-xl resize-none"
                              data-testid="textarea-target-audience"
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </motion.div>
                )}

                {step === 3 && (
                  <motion.div
                    key="step3"
                    variants={pageVariants}
                    initial="initial"
                    animate="animate"
                    exit="exit"
                    className="space-y-6"
                  >
                    <FormField
                      control={form.control}
                      name="primaryGoal"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-base font-medium">Objetivo Principal *</FormLabel>
                          <Select onValueChange={field.onChange} value={field.value}>
                            <FormControl>
                              <SelectTrigger className="rounded-xl" data-testid="select-primary-goal">
                                <SelectValue placeholder="Selecione seu objetivo..." />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="growth">Crescimento / Aquisição</SelectItem>
                              <SelectItem value="positioning">Posicionamento de Marca</SelectItem>
                              <SelectItem value="retention">Retenção de Clientes</SelectItem>
                              <SelectItem value="launch">Lançamento de Produto</SelectItem>
                              <SelectItem value="awareness">Awareness / Reconhecimento</SelectItem>
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="mainChallenge"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-base font-medium">Maior Desafio Atual *</FormLabel>
                          <FormDescription>
                            Descreva o principal obstáculo que você enfrenta
                          </FormDescription>
                          <FormControl>
                            <Textarea 
                              placeholder="Ex: Alto custo de aquisição de clientes (CAC), dificuldade em se diferenciar da concorrência, baixa taxa de conversão no funil..." 
                              {...field} 
                              rows={6}
                              className="rounded-xl resize-none"
                              data-testid="textarea-main-challenge"
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </motion.div>
                )}

                {step === 4 && (
                  <motion.div
                    key="step4"
                    variants={pageVariants}
                    initial="initial"
                    animate="animate"
                    exit="exit"
                    className="space-y-6"
                  >
                    <div>
                      <h3 className="text-lg font-semibold mb-2">Escolha o Nível de Enriquecimento</h3>
                      <p className="text-sm text-muted-foreground mb-6">
                        Selecione a profundidade da análise. Você pode fazer upgrade a qualquer momento.
                      </p>
                    </div>

                    <FormField
                      control={form.control}
                      name="enrichmentLevel"
                      render={({ field }) => (
                        <FormItem>
                          <FormControl>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-5 md:gap-6">
                              {ENRICHMENT_LEVELS.map((level) => {
                                const Icon = level.icon;
                                const isSelected = field.value === level.id;
                                
                                return (
                                  <button
                                    key={level.id}
                                    type="button"
                                    onClick={() => field.onChange(level.id)}
                                    className={`relative rounded-2xl p-5 md:p-6 text-left transition-all duration-200 hover-elevate ${
                                      isSelected
                                        ? "border-2 border-accent bg-accent/5"
                                        : "border border-border/50"
                                    }`}
                                    data-testid={`card-enrichment-level-${level.id}`}
                                  >
                                    {level.recommended && (
                                      <Badge className="absolute top-4 right-4 bg-accent text-white text-xs px-2.5 py-0.5">
                                        Recomendado
                                      </Badge>
                                    )}
                                    
                                    <div className="flex items-start gap-3 mb-4">
                                      <div className={`p-2.5 rounded-lg flex-shrink-0 ${isSelected ? "bg-accent/10" : "bg-muted"}`}>
                                        <Icon className={`w-5 h-5 ${isSelected ? "text-accent" : "text-muted-foreground"}`} />
                                      </div>
                                      <div className="flex-1 min-w-0">
                                        <h4 className="font-semibold text-base mb-1">{level.name}</h4>
                                        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                                          <div className="flex items-center gap-1">
                                            <Clock className="w-3 h-3" />
                                            <span>{level.duration}</span>
                                          </div>
                                          <Badge variant="outline" className="text-xs px-1.5 py-0">
                                            {level.modules} módulos
                                          </Badge>
                                        </div>
                                      </div>
                                    </div>

                                    <p className="text-sm text-muted-foreground mb-5 leading-relaxed">
                                      {level.description}
                                    </p>

                                    <ul className="space-y-2.5">
                                      {level.features.map((feature, idx) => (
                                        <li key={idx} className="flex items-start gap-2.5 text-sm">
                                          <CheckCircle2 className={`w-4 h-4 mt-0.5 flex-shrink-0 ${isSelected ? "text-accent" : "text-muted-foreground"}`} />
                                          <span className="text-muted-foreground leading-snug">{feature}</span>
                                        </li>
                                      ))}
                                    </ul>
                                  </button>
                                );
                              })}
                            </div>
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </motion.div>
                )}
              </AnimatePresence>

              <div className="flex justify-between pt-6">
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleBack}
                  disabled={step === 1}
                  className="rounded-xl px-6"
                  data-testid="button-back"
                >
                  Voltar
                </Button>
                <Button
                  type="button"
                  onClick={handleNext}
                  disabled={saveMutation.isPending}
                  className="rounded-xl px-8 bg-accent hover:bg-accent text-white font-medium"
                  data-testid="button-next"
                >
                  {step === 4 ? (saveMutation.isPending ? "Criando seu perfil..." : "Finalizar") : "Próximo"}
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}
