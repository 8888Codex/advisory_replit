import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  MessageCircle, 
  TrendingUp, 
  TrendingDown, 
  Minus,
  Target,
  Heart,
  Lightbulb,
  MessageSquare
} from "lucide-react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { useState } from "react";

interface RedditInsights {
  communities?: string[];
  painPoints?: string[];
  goals?: string[];
  values?: string[];
  language?: string;
  sentiment?: {
    overall: 'positive' | 'neutral' | 'negative';
    breakdown: Record<string, string>;
    summary: string;
  };
  trendingTopics?: Array<{
    topic: string;
    mentions: string;
    trend: 'rising' | 'stable' | 'declining';
    relevance: string;
  }>;
}

interface RedditInsightsCardProps {
  data: RedditInsights | null;
}

export function RedditInsightsCard({ data }: RedditInsightsCardProps) {
  const [isPainPointsOpen, setIsPainPointsOpen] = useState(false);
  const [isGoalsOpen, setIsGoalsOpen] = useState(false);
  const [isValuesOpen, setIsValuesOpen] = useState(false);

  if (!data || (!data.communities?.length && !data.sentiment && !data.trendingTopics?.length)) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageCircle className="w-5 h-5 text-orange-500" />
            Reddit Insights
          </CardTitle>
          <CardDescription>
            Insights do Reddit não disponíveis
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment.toLowerCase()) {
      case 'positive':
        return 'bg-green-500/10 text-green-700 border-green-500/20';
      case 'negative':
        return 'bg-red-500/10 text-red-700 border-red-500/20';
      default:
        return 'bg-yellow-500/10 text-yellow-700 border-yellow-500/20';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend.toLowerCase()) {
      case 'rising':
        return <TrendingUp className="w-4 h-4 text-green-600" />;
      case 'declining':
        return <TrendingDown className="w-4 h-4 text-red-600" />;
      default:
        return <Minus className="w-4 h-4 text-gray-600" />;
    }
  };

  const getMentionsColor = (mentions: string) => {
    switch (mentions.toLowerCase()) {
      case 'high':
        return 'bg-orange-500/10 text-orange-700 border-orange-500/20';
      case 'medium':
        return 'bg-blue-500/10 text-blue-700 border-blue-500/20';
      default:
        return 'bg-gray-500/10 text-gray-700 border-gray-500/20';
    }
  };

  return (
    <Card className="border-orange-200 dark:border-orange-900">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageCircle className="w-5 h-5 text-orange-500" />
          Reddit Insights
        </CardTitle>
        <CardDescription>
          Análise de comunidades, sentimento e tendências no Reddit
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Communities */}
        {data.communities && data.communities.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-orange-500" />
              Comunidades Relevantes
            </h3>
            <div className="flex flex-wrap gap-2">
              {data.communities.map((community, idx) => (
                <Badge
                  key={idx}
                  variant="outline"
                  className="bg-orange-500/5 border-orange-500/20 text-orange-700"
                >
                  {community}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Sentiment Analysis */}
        {data.sentiment && (
          <div>
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <Heart className="w-4 h-4 text-pink-500" />
              Análise de Sentimento
            </h3>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <span className="text-sm text-muted-foreground">Tom Geral:</span>
                <Badge className={getSentimentColor(data.sentiment.overall)}>
                  {data.sentiment.overall === 'positive' ? '😊 Positivo' : 
                   data.sentiment.overall === 'negative' ? '😞 Negativo' : 
                   '😐 Neutro'}
                </Badge>
              </div>
              
              {data.sentiment.summary && (
                <p className="text-sm text-muted-foreground italic bg-muted/30 p-3 rounded-md">
                  {data.sentiment.summary}
                </p>
              )}

              {data.sentiment.breakdown && Object.keys(data.sentiment.breakdown).length > 0 && (
                <div className="mt-3">
                  <p className="text-xs font-medium text-muted-foreground mb-2">
                    Breakdown por Comunidade:
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {Object.entries(data.sentiment.breakdown).map(([community, sentiment]) => (
                      <div
                        key={community}
                        className="flex items-center justify-between p-2 bg-muted/30 rounded-md"
                      >
                        <span className="text-xs font-medium">{community}</span>
                        <Badge
                          variant="outline"
                          className={`text-xs ${getSentimentColor(sentiment)}`}
                        >
                          {sentiment}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Trending Topics */}
        {data.trendingTopics && data.trendingTopics.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-blue-500" />
              Tópicos em Alta
            </h3>
            <div className="space-y-3">
              {data.trendingTopics.map((topic, idx) => (
                <div
                  key={idx}
                  className="p-3 border border-muted rounded-lg space-y-2 hover:bg-muted/30 transition-colors"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2 flex-1">
                      {getTrendIcon(topic.trend)}
                      <span className="font-medium text-sm">{topic.topic}</span>
                    </div>
                    <Badge
                      variant="outline"
                      className={`text-xs ${getMentionsColor(topic.mentions)}`}
                    >
                      {topic.mentions}
                    </Badge>
                  </div>
                  {topic.relevance && (
                    <p className="text-xs text-muted-foreground pl-6">
                      {topic.relevance}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Pain Points (Collapsible) */}
        {data.painPoints && data.painPoints.length > 0 && (
          <Collapsible open={isPainPointsOpen} onOpenChange={setIsPainPointsOpen}>
            <CollapsibleTrigger className="w-full">
              <div className="flex items-center justify-between p-2 hover:bg-muted/30 rounded-md">
                <h3 className="text-sm font-semibold flex items-center gap-2">
                  <Target className="w-4 h-4 text-red-500" />
                  Pain Points ({data.painPoints.length})
                </h3>
                <Badge variant="outline" className="text-xs">
                  {isPainPointsOpen ? 'Ocultar' : 'Mostrar'}
                </Badge>
              </div>
            </CollapsibleTrigger>
            <CollapsibleContent className="mt-2">
              <ul className="space-y-2">
                {data.painPoints.map((point, idx) => (
                  <li
                    key={idx}
                    className="text-sm p-2 bg-red-500/5 border border-red-500/20 rounded-md"
                  >
                    {point}
                  </li>
                ))}
              </ul>
            </CollapsibleContent>
          </Collapsible>
        )}

        {/* Goals (Collapsible) */}
        {data.goals && data.goals.length > 0 && (
          <Collapsible open={isGoalsOpen} onOpenChange={setIsGoalsOpen}>
            <CollapsibleTrigger className="w-full">
              <div className="flex items-center justify-between p-2 hover:bg-muted/30 rounded-md">
                <h3 className="text-sm font-semibold flex items-center gap-2">
                  <Target className="w-4 h-4 text-green-500" />
                  Goals ({data.goals.length})
                </h3>
                <Badge variant="outline" className="text-xs">
                  {isGoalsOpen ? 'Ocultar' : 'Mostrar'}
                </Badge>
              </div>
            </CollapsibleTrigger>
            <CollapsibleContent className="mt-2">
              <ul className="space-y-2">
                {data.goals.map((goal, idx) => (
                  <li
                    key={idx}
                    className="text-sm p-2 bg-green-500/5 border border-green-500/20 rounded-md"
                  >
                    {goal}
                  </li>
                ))}
              </ul>
            </CollapsibleContent>
          </Collapsible>
        )}

        {/* Values (Collapsible) */}
        {data.values && data.values.length > 0 && (
          <Collapsible open={isValuesOpen} onOpenChange={setIsValuesOpen}>
            <CollapsibleTrigger className="w-full">
              <div className="flex items-center justify-between p-2 hover:bg-muted/30 rounded-md">
                <h3 className="text-sm font-semibold flex items-center gap-2">
                  <Heart className="w-4 h-4 text-purple-500" />
                  Values ({data.values.length})
                </h3>
                <Badge variant="outline" className="text-xs">
                  {isValuesOpen ? 'Ocultar' : 'Mostrar'}
                </Badge>
              </div>
            </CollapsibleTrigger>
            <CollapsibleContent className="mt-2">
              <ul className="space-y-2">
                {data.values.map((value, idx) => (
                  <li
                    key={idx}
                    className="text-sm p-2 bg-purple-500/5 border border-purple-500/20 rounded-md"
                  >
                    {value}
                  </li>
                ))}
              </ul>
            </CollapsibleContent>
          </Collapsible>
        )}

        {/* Language */}
        {data.language && (
          <div>
            <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
              <Lightbulb className="w-4 h-4 text-yellow-500" />
              Linguagem Autêntica
            </h3>
            <p className="text-sm text-muted-foreground bg-yellow-500/5 border border-yellow-500/20 p-3 rounded-md">
              {data.language}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

