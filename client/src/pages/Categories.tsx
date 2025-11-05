import { useQuery } from "@tanstack/react-query";
import { Link, useLocation } from "wouter";
import { motion, AnimatePresence } from "framer-motion";
import { useState, useMemo } from "react";
import {
  TrendingUp,
  Rocket,
  FileText,
  Target,
  Sparkles,
  BarChart,
  Search,
  Users,
  Share2,
  Package,
  Brain,
  Award,
  BarChart4,
  Handshake,
  TrendingUpDown,
  Loader2,
  Star,
  MessageSquare,
  type LucideIcon,
} from "lucide-react";
import { AnimatedPage } from "@/components/AnimatedPage";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { useDebounce } from "@/hooks/useDebounce";
import { apiRequest } from "@/lib/queryClient";

interface Category {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  expertCount: number;
}

interface ExpertRecommendation {
  expertId: string;
  expertName: string;
  avatar?: string | null;
  relevanceScore: number;
  stars: number;
  justification: string;
}

const CATEGORY_ICONS: Record<string, LucideIcon> = {
  marketing: TrendingUp,
  growth: Rocket,
  content: FileText,
  positioning: Target,
  creative: Sparkles,
  direct_response: BarChart,
  seo: Search,
  social: Users,
  viral: Share2,
  product: Package,
  psychology: Brain,
  branding: Award,
  analytics: BarChart4,
  sales: Handshake,
  sales_enablement: TrendingUpDown,
};

// Apple-style: Neutral palette, no rainbow colors
const CATEGORY_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  marketing: {
    bg: "bg-muted/50",
    text: "text-foreground",
    border: "border-border/50",
  },
  growth: {
    bg: "bg-muted/50",
    text: "text-foreground",
    border: "border-border/50",
  },
  content: {
    bg: "bg-muted/50",
    text: "text-foreground",
    border: "border-border/50",
  },
  positioning: {
    bg: "bg-muted/50",
    text: "text-foreground",
    border: "border-border/50",
  },
  creative: {
    bg: "bg-muted/50",
    text: "text-foreground",
    border: "border-border/50",
  },
  direct_response: {
    bg: "bg-muted/50",
    text: "text-foreground",
    border: "border-border/50",
  },
  seo: {
    bg: "bg-muted/50",
    text: "text-foreground",
    border: "border-border/50",
  },
  social: {
    bg: "bg-muted/50",
    text: "text-foreground",
    border: "border-border/50",
  },
  viral: {
    bg: "bg-muted/50",
    text: "text-foreground",
    border: "border-border/50",
  },
  product: {
    bg: "bg-muted/50",
    text: "text-foreground",
    border: "border-border/50",
  },
  psychology: {
    bg: "bg-muted/50",
    text: "text-foreground",
    border: "border-border/50",
  },
  branding: {
    bg: "bg-muted/50",
    text: "text-foreground",
    border: "border-border/50",
  },
  analytics: {
    bg: "bg-muted/50",
    text: "text-foreground",
    border: "border-border/50",
  },
  sales: {
    bg: "bg-muted/50",
    text: "text-foreground",
    border: "border-border/50",
  },
  sales_enablement: {
    bg: "bg-muted/50",
    text: "text-foreground",
    border: "border-border/50",
  },
};

function CategoryCard({ category, index }: { category: Category; index: number }) {
  const Icon = CATEGORY_ICONS[category.id] || TrendingUp;
  const colors = CATEGORY_COLORS[category.id] || CATEGORY_COLORS.marketing;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.3,
        delay: index * 0.05,
        ease: [0.25, 0.1, 0.25, 1],
      }}
    >
      <Link href={`/experts?category=${category.id}`} data-testid={`link-category-${category.id}`}>
        <motion.div
          className={cn(
            "group relative rounded-2xl p-8",
            "bg-card border border-border/50",
            "hover:shadow-md transition-shadow duration-200 cursor-pointer"
          )}
          whileHover={{
            y: -2,
            transition: { duration: 0.2, ease: [0.25, 0.1, 0.25, 1] },
          }}
          whileTap={{ scale: 0.98 }}
        >
          {/* Icon Circle */}
          <div
            className={cn(
              "w-14 h-14 rounded-full flex items-center justify-center mb-6",
              colors.bg,
              `border ${colors.border}`,
              "group-hover:scale-105 transition-transform duration-200"
            )}
            data-testid={`icon-category-${category.id}`}
          >
            <Icon className={cn("w-7 h-7", colors.text)} />
          </div>

          {/* Category Name */}
          <h3 className="text-xl font-medium tracking-tight mb-2" data-testid={`text-category-name-${category.id}`}>
            {category.name}
          </h3>

          {/* Description */}
          <p className="text-sm text-muted-foreground leading-relaxed mb-6" data-testid={`text-category-description-${category.id}`}>
            {category.description}
          </p>

          {/* Expert Count + CTA */}
          <div className="flex items-center justify-between gap-4">
            <span className="text-xs font-medium text-muted-foreground" data-testid={`text-expert-count-${category.id}`}>
              {category.expertCount} {category.expertCount === 1 ? "Especialista" : "Especialistas"}
            </span>

            <Button
              variant="ghost"
              size="sm"
              className={cn("rounded-xl", colors.text)}
              data-testid={`button-view-experts-${category.id}`}
            >
              Ver Especialistas →
            </Button>
          </div>
        </motion.div>
      </Link>
    </motion.div>
  );
}

function CategoryGridSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
      {[...Array(6)].map((_, i) => (
        <div key={i} className="rounded-2xl p-8 bg-card border border-border/50">
          <Skeleton className="w-14 h-14 rounded-full mb-6" />
          <Skeleton className="h-6 w-48 mb-2" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-3/4 mb-6" />
          <div className="flex items-center justify-between">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-8 w-40 rounded-xl" />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function Categories() {
  const [, setLocation] = useLocation();
  const [challenge, setChallenge] = useState("");
  const [councilExperts, setCouncilExperts] = useState<string[]>([]);

  const { data: categories, isLoading } = useQuery<Category[]>({
    queryKey: ["/api/categories"],
  });

  // Debounce challenge input for semantic recommendations
  const debouncedChallenge = useDebounce(challenge, 800);

  // Get semantic recommendations based on challenge (NO category filter - search ALL experts)
  const { data: semanticRecommendations, isLoading: loadingSemanticRecs } = useQuery<{ recommendations: ExpertRecommendation[] }>({
    queryKey: ["/api/recommend-experts", debouncedChallenge],
    queryFn: async () => {
      if (!debouncedChallenge.trim() || debouncedChallenge.trim().length < 10) {
        return { recommendations: [] };
      }
      
      const response = await apiRequest("/api/recommend-experts", {
        method: "POST",
        body: JSON.stringify({ 
          problem: debouncedChallenge,
          // NO categoryFilter - we want cross-category recommendations
        }),
        headers: { "Content-Type": "application/json" },
      });
      return response.json();
    },
    enabled: debouncedChallenge.trim().length >= 10,
  });

  const semanticRecs = semanticRecommendations?.recommendations || [];

  const toggleCouncilExpert = (expertId: string) => {
    setCouncilExperts(prev =>
      prev.includes(expertId)
        ? prev.filter(id => id !== expertId)
        : [...prev, expertId]
    );
  };
  
  const startCouncil = () => {
    // Guard against empty selection
    if (councilExperts.length === 0) return;
    
    // Navigate to TestCouncil with pre-selected experts via localStorage
    localStorage.setItem('preselectedExperts', JSON.stringify(councilExperts));
    localStorage.setItem('preselectedProblem', challenge);
    setLocation('/test-council');
  };

  const handleConsult = (rec: ExpertRecommendation) => {
    setLocation(`/chat/${rec.expertId}`);
  };

  return (
    <AnimatedPage>
      <div className="min-h-screen">
        <div className="max-w-7xl mx-auto px-6 py-24">
          {/* Header */}
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <h1 className="text-5xl md:text-6xl font-semibold tracking-tight mb-6" data-testid="heading-categories">
              Explore por Área de Expertise
            </h1>
            <p className="text-lg text-muted-foreground max-w-3xl mx-auto leading-relaxed" data-testid="text-categories-subtitle">
              Descreva seu desafio e deixe a IA recomendar os especialistas ideais, ou navegue pelas categorias abaixo.
            </p>
          </motion.div>

          {/* Semantic Search Section */}
          <motion.div
            className="mb-12 max-w-4xl mx-auto"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.1 }}
          >
            <Card className="border-primary/20 bg-card/50">
              <CardContent className="p-6">
                <div className="flex items-start gap-3 mb-3">
                  <Sparkles className="h-5 w-5 text-primary mt-1" />
                  <div className="flex-1">
                    <h2 className="text-lg font-semibold mb-1">Encontre o Especialista Ideal</h2>
                    <p className="text-sm text-muted-foreground">
                      Descreva seu desafio em detalhes e nossa IA analisará qual especialista é ideal para você.
                    </p>
                  </div>
                </div>
                <Textarea
                  placeholder="Ex: Preciso aumentar a conversão do meu e-commerce de moda. Temos 10mil visitas/mês mas apenas 1% de conversão..."
                  value={challenge}
                  onChange={(e) => setChallenge(e.target.value)}
                  className="min-h-[100px] resize-none"
                  data-testid="textarea-semantic-search"
                />
                {challenge.trim().length > 0 && challenge.trim().length < 10 && (
                  <p className="text-xs text-muted-foreground mt-2">
                    Digite pelo menos 10 caracteres para ver recomendações...
                  </p>
                )}
              </CardContent>
            </Card>
          </motion.div>

          {/* Semantic Recommendations */}
          {loadingSemanticRecs && debouncedChallenge.trim().length >= 10 && (
            <motion.div
              className="mb-12 max-w-4xl mx-auto"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <div className="flex items-center justify-center gap-3 py-8">
                <Loader2 className="h-5 w-5 animate-spin text-primary" />
                <p className="text-muted-foreground">🔍 Analisando seu desafio...</p>
              </div>
            </motion.div>
          )}

          {semanticRecs.length > 0 && (
            <motion.div
              className="mb-16 max-w-4xl mx-auto"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <h3 className="text-xl font-semibold mb-6 flex items-center gap-2">
                <Star className="h-5 w-5 text-primary" />
                Especialistas Recomendados para Você
              </h3>
              
              <div className="space-y-4">
                {semanticRecs.map((rec) => {
                  const initials = rec.expertName
                    .split(" ")
                    .map((n) => n[0])
                    .join("")
                    .toUpperCase()
                    .slice(0, 2);

                  return (
                    <motion.div
                      key={rec.expertId}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.26 }}
                    >
                      <Card className="hover:shadow-md transition-shadow cursor-pointer">
                        <CardContent className="p-6">
                          <div className="flex gap-4">
                            <Avatar className="h-16 w-16">
                              {rec.avatar && <AvatarImage src={rec.avatar} alt={rec.expertName} />}
                              <AvatarFallback className="bg-primary/10 text-primary font-semibold">
                                {initials}
                              </AvatarFallback>
                            </Avatar>
                            <div className="flex-1">
                              <div className="flex items-start justify-between mb-2">
                                <h4 className="font-semibold text-lg">{rec.expertName}</h4>
                                <div className="flex items-center gap-1">
                                  {[...Array(5)].map((_, i) => (
                                    <Star
                                      key={i}
                                      className={cn(
                                        "h-4 w-4",
                                        i < rec.stars
                                          ? "fill-primary text-primary"
                                          : "text-muted-foreground/30"
                                      )}
                                    />
                                  ))}
                                </div>
                              </div>
                              <p className="text-sm text-muted-foreground mb-4">
                                {rec.justification}
                              </p>
                              <div className="flex gap-2">
                                <Button
                                  size="sm"
                                  className="flex-1 gap-2"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleConsult(rec);
                                  }}
                                  data-testid={`button-chat-${rec.expertId}`}
                                >
                                  <MessageSquare className="h-4 w-4" />
                                  Conversar
                                </Button>
                                <Button 
                                  size="sm" 
                                  variant={councilExperts.includes(rec.expertId) ? "default" : "outline"}
                                  className="flex-1 gap-2"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    toggleCouncilExpert(rec.expertId);
                                  }}
                                  data-testid={`button-council-${rec.expertId}`}
                                >
                                  <Users className="h-4 w-4" />
                                  {councilExperts.includes(rec.expertId) ? "Adicionado" : "Conselho"}
                                </Button>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  );
                })}
              </div>

              <div className="text-center mt-6">
                <p className="text-sm text-muted-foreground">
                  Ou continue explorando as categorias abaixo
                </p>
              </div>
            </motion.div>
          )}

          {/* Categories Grid */}
          {isLoading ? (
            <CategoryGridSkeleton />
          ) : categories && categories.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8" data-testid="grid-categories">
              {categories.map((category, index) => (
                <CategoryCard key={category.id} category={category} index={index} />
              ))}
            </div>
          ) : (
            <div className="text-center py-16">
              <p className="text-muted-foreground">Nenhuma categoria disponível no momento.</p>
            </div>
          )}
        </div>
      </div>

      {/* Floating Action Button for Council */}
      <AnimatePresence>
        {councilExperts.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 100 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 100 }}
            transition={{ duration: 0.26 }}
            className="fixed bottom-8 right-8 z-50"
          >
            <Card className="border-primary bg-primary/5 shadow-lg">
              <CardContent className="p-4">
                <div className="flex items-center gap-4">
                  <div>
                    <p className="font-semibold text-sm">
                      {councilExperts.length} {councilExperts.length === 1 ? 'especialista selecionado' : 'especialistas selecionados'}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Monte sua mesa redonda
                    </p>
                  </div>
                  <Button
                    size="lg"
                    onClick={startCouncil}
                    disabled={councilExperts.length === 0}
                    className="gap-2"
                    data-testid="button-start-council"
                  >
                    <Users className="h-5 w-5" />
                    Iniciar Conselho
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </AnimatedPage>
  );
}
