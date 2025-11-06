import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, PieChart, Pie, Cell
} from 'recharts';
import { 
  MessageSquare, Users, Flame, Calendar, TrendingUp, 
  Lightbulb, Target, Sparkles
} from "lucide-react";
import { motion } from "framer-motion";

// ============================================
// TYPE DEFINITIONS
// ============================================

interface OverviewStats {
  totalConversations: number;
  totalExperts: number;
  totalCouncils: number;
  currentStreak: number;
  lastActive: string | null;
}

interface TimelinePoint {
  date: string;
  chats: number;
  councils: number;
  total: number;
}

interface TopExpert {
  expertId: string;
  expertName: string;
  category: string;
  consultations: number;
  lastConsulted: string | null;
  avatar: string;
}

interface Recommendation {
  type: "expert_suggestion" | "pattern_insight" | "next_step" | "system_message";
  title: string;
  description: string;
  action?: string;
}

// ============================================
// OVERVIEW CARDS COMPONENT
// ============================================

function OverviewCards({ data, isLoading }: { data?: OverviewStats; isLoading: boolean }) {
  const cards = [
    {
      label: "Total de Conversas",
      value: data?.totalConversations || 0,
      icon: MessageSquare,
      color: "text-blue-500",
      bgColor: "bg-blue-50 dark:bg-blue-950",
    },
    {
      label: "Experts Consultados",
      value: data?.totalExperts || 0,
      icon: Users,
      color: "text-purple-500",
      bgColor: "bg-purple-50 dark:bg-purple-950",
    },
    {
      label: "Councils Realizados",
      value: data?.totalCouncils || 0,
      icon: Sparkles,
      color: "text-amber-500",
      bgColor: "bg-amber-50 dark:bg-amber-950",
    },
    {
      label: "Streak Atual",
      value: data?.currentStreak || 0,
      icon: Flame,
      color: "text-orange-500",
      bgColor: "bg-orange-50 dark:bg-orange-950",
      suffix: data?.currentStreak === 1 ? " dia" : " dias"
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, idx) => (
        <motion.div
          key={card.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: idx * 0.05 }}
        >
          <Card className="rounded-2xl" data-testid={`card-${card.label.toLowerCase().replace(/\s+/g, "-")}`}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {card.label}
              </CardTitle>
              <div className={`p-2 rounded-lg ${card.bgColor}`}>
                <card.icon className={`h-4 w-4 ${card.color}`} />
              </div>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <Skeleton className="h-8 w-20" />
              ) : (
                <div className="text-3xl font-semibold">
                  {card.value}{card.suffix || ''}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </div>
  );
}

// ============================================
// ACTIVITY CHART COMPONENT
// ============================================

function ActivityChart({ data, isLoading }: { data?: TimelinePoint[]; isLoading: boolean }) {
  if (isLoading) {
    return (
      <Card className="rounded-2xl">
        <CardHeader>
          <CardTitle className="font-semibold">Atividade nos Últimos 30 Dias</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>
    );
  }

  const chartData = data || [];

  return (
    <Card className="rounded-2xl">
      <CardHeader>
        <CardTitle className="font-semibold flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-primary" />
          Atividade nos Últimos 30 Dias
        </CardTitle>
        <CardDescription>
          Histórico de conversas 1:1 e sessões de Council
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => {
                const date = new Date(value);
                return `${date.getDate()}/${date.getMonth() + 1}`;
              }}
            />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip 
              labelFormatter={(value) => {
                const date = new Date(value);
                return date.toLocaleDateString('pt-BR');
              }}
            />
            <Line 
              type="monotone" 
              dataKey="chats" 
              stroke="hsl(var(--chart-1))" 
              strokeWidth={2}
              name="Chats 1:1"
              dot={{ r: 3 }}
            />
            <Line 
              type="monotone" 
              dataKey="councils" 
              stroke="hsl(var(--chart-2))" 
              strokeWidth={2}
              name="Councils"
              dot={{ r: 3 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

// ============================================
// EXPERT RANKING COMPONENT
// ============================================

function ExpertRankingList({ data, isLoading }: { data?: TopExpert[]; isLoading: boolean }) {
  if (isLoading) {
    return (
      <Card className="rounded-2xl">
        <CardHeader>
          <CardTitle className="font-semibold">Top Experts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center gap-3">
                <Skeleton className="h-10 w-10 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-3 w-20" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const experts = data || [];
  const medals = ['🥇', '🥈', '🥉'];

  return (
    <Card className="rounded-2xl">
      <CardHeader>
        <CardTitle className="font-semibold flex items-center gap-2">
          <Users className="h-5 w-5 text-primary" />
          Experts Mais Consultados
        </CardTitle>
        <CardDescription>
          Ranking dos seus especialistas favoritos
        </CardDescription>
      </CardHeader>
      <CardContent>
        {experts.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-8">
            Comece a consultar experts para ver seu ranking!
          </p>
        ) : (
          <div className="space-y-4">
            {experts.map((expert, idx) => (
              <motion.div
                key={expert.expertId}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: idx * 0.05 }}
                className="flex items-center gap-3 p-3 rounded-xl hover-elevate active-elevate-2 cursor-pointer"
                data-testid={`expert-rank-${idx + 1}`}
              >
                <div className="flex items-center gap-2">
                  {idx < 3 ? (
                    <span className="text-2xl">{medals[idx]}</span>
                  ) : (
                    <span className="text-muted-foreground font-semibold w-8 text-center">
                      {idx + 1}
                    </span>
                  )}
                  <Avatar className="h-10 w-10">
                    <AvatarImage src={expert.avatar} alt={expert.expertName} />
                    <AvatarFallback>
                      {expert.expertName.split(' ').map(n => n[0]).join('').slice(0, 2)}
                    </AvatarFallback>
                  </Avatar>
                </div>
                <div className="flex-1">
                  <div className="font-semibold text-sm">{expert.expertName}</div>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="secondary" className="text-xs">
                      {expert.category}
                    </Badge>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-semibold text-lg">{expert.consultations}</div>
                  <div className="text-xs text-muted-foreground">
                    {expert.consultations === 1 ? 'consulta' : 'consultas'}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ============================================
// CATEGORY DISTRIBUTION COMPONENT
// ============================================

function CategoryDistribution({ data, isLoading }: { data?: Record<string, number>; isLoading: boolean }) {
  if (isLoading) {
    return (
      <Card className="rounded-2xl">
        <CardHeader>
          <CardTitle className="font-semibold">Distribuição por Categoria</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>
    );
  }

  const categoryData = data || {};
  const chartData = Object.entries(categoryData).map(([name, value]) => ({
    name,
    value,
  }));

  const COLORS = [
    'hsl(var(--chart-1))',
    'hsl(var(--chart-2))',
    'hsl(var(--chart-3))',
    'hsl(var(--chart-4))',
    'hsl(var(--chart-5))',
  ];

  return (
    <Card className="rounded-2xl">
      <CardHeader>
        <CardTitle className="font-semibold flex items-center gap-2">
          <Target className="h-5 w-5 text-primary" />
          Distribuição por Categoria
        </CardTitle>
        <CardDescription>
          Áreas de especialização mais consultadas
        </CardDescription>
      </CardHeader>
      <CardContent>
        {chartData.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-8">
            Consulte experts de diferentes categorias para ver a distribuição
          </p>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}

// ============================================
// SMART RECOMMENDATIONS COMPONENT
// ============================================

function SmartRecommendations({ data, isLoading }: { data?: Recommendation[]; isLoading: boolean }) {
  if (isLoading) {
    return (
      <Card className="rounded-2xl">
        <CardHeader>
          <CardTitle className="font-semibold">Recomendações Inteligentes</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-20 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const recommendations = data || [];

  const getIcon = (type: string) => {
    switch (type) {
      case "expert_suggestion":
        return Users;
      case "pattern_insight":
        return TrendingUp;
      case "next_step":
        return Target;
      default:
        return Lightbulb;
    }
  };

  const getColor = (type: string) => {
    switch (type) {
      case "expert_suggestion":
        return "text-purple-500";
      case "pattern_insight":
        return "text-blue-500";
      case "next_step":
        return "text-green-500";
      default:
        return "text-amber-500";
    }
  };

  return (
    <Card className="rounded-2xl">
      <CardHeader>
        <CardTitle className="font-semibold flex items-center gap-2">
          <Lightbulb className="h-5 w-5 text-primary" />
          Recomendações Inteligentes
        </CardTitle>
        <CardDescription>
          Insights gerados por IA baseados no seu histórico
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {recommendations.map((rec, idx) => {
            const Icon = getIcon(rec.type);
            const color = getColor(rec.type);
            
            return (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: idx * 0.08 }}
                className="p-4 rounded-xl border hover-elevate active-elevate-2 cursor-pointer"
                data-testid={`recommendation-${idx}`}
              >
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg bg-muted/50`}>
                    <Icon className={`h-4 w-4 ${color}`} />
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold text-sm mb-1">{rec.title}</div>
                    <div className="text-sm text-muted-foreground">{rec.description}</div>
                    {rec.action && (
                      <div className="mt-2">
                        <Badge variant="outline" className="text-xs">
                          {rec.action}
                        </Badge>
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================
// MAIN ANALYTICS PAGE
// ============================================

export default function Analytics() {
  // Fetch all analytics data
  const { data: overview, isLoading: loadingOverview } = useQuery<OverviewStats>({
    queryKey: ['/api/analytics/overview'],
  });

  const { data: timeline, isLoading: loadingTimeline } = useQuery<TimelinePoint[]>({
    queryKey: ['/api/analytics/timeline'],
  });

  const { data: topExperts, isLoading: loadingExperts } = useQuery<TopExpert[]>({
    queryKey: ['/api/analytics/top-experts'],
  });

  const { data: recommendations, isLoading: loadingRecommendations } = useQuery<Recommendation[]>({
    queryKey: ['/api/analytics/recommendations'],
  });

  const { data: categories, isLoading: loadingCategories } = useQuery<Record<string, number>>({
    queryKey: ['/api/analytics/categories'],
  });

  return (
    <div className="container mx-auto py-8 px-4 max-w-7xl">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="mb-8"
      >
        <h1 className="text-4xl font-semibold mb-2 flex items-center gap-3">
          <Calendar className="h-10 w-10 text-muted-foreground" />
          Analytics & Insights
        </h1>
        <p className="text-muted-foreground">
          Acompanhe sua jornada de aprendizado com especialistas de marketing
        </p>
      </motion.div>

      {/* Overview Cards */}
      <OverviewCards data={overview} isLoading={loadingOverview} />

      {/* Charts and Rankings Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-8">
        {/* Activity Chart - 2 columns */}
        <div className="lg:col-span-2">
          <ActivityChart data={timeline} isLoading={loadingTimeline} />
        </div>

        {/* Expert Ranking - 1 column */}
        <div className="lg:col-span-1">
          <ExpertRankingList data={topExperts} isLoading={loadingExperts} />
        </div>
      </div>

      {/* Category Distribution and Recommendations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
        {/* Category Distribution */}
        <CategoryDistribution data={categories} isLoading={loadingCategories} />

        {/* Smart Recommendations */}
        <SmartRecommendations data={recommendations} isLoading={loadingRecommendations} />
      </div>
    </div>
  );
}
