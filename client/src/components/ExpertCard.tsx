import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MessageSquare, Star, Users, Sparkles } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

export interface Expert {
  id: string;
  name: string;
  title: string;
  expertise: string[];
  bio: string;
  avatar: string | null;
  category?: string;
}

interface ExpertCardProps {
  expert: Expert;
  variant?: "rich" | "compact";
  onChat?: (expertId: string) => void;
  onAddToCouncil?: (expertId: string) => void;
  councilAdded?: boolean;
  index?: number;
  className?: string;
  showStars?: boolean;
  stars?: number;
  justification?: string;
  recommendationScore?: number;
}

export function ExpertCard({
  expert,
  variant = "rich",
  onChat,
  onAddToCouncil,
  councilAdded = false,
  index = 0,
  className,
  showStars = false,
  stars = 5,
  justification,
  recommendationScore,
}: ExpertCardProps) {
  const initials = expert.name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  const handleChatClick = (e?: React.MouseEvent) => {
    e?.stopPropagation();
    if (onChat) onChat(expert.id);
  };

  const handleCouncilClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onAddToCouncil) onAddToCouncil(expert.id);
  };

  const isHighlyRecommended = showStars && stars >= 4;

  if (variant === "compact") {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.1 * index }}
        className={className}
      >
        <Card
          className="rounded-2xl hover-elevate cursor-pointer transition-all relative"
          onClick={handleChatClick}
          data-testid={`card-expert-${expert.id}`}
        >
          {isHighlyRecommended && (
            <div className="absolute -top-2 -right-2 z-10">
              <Badge className="gap-1 rounded-full px-2 py-1 sm:px-3 sm:py-1.5 bg-accent text-white shadow-sm text-xs">
                <Sparkles className="h-3 w-3" />
                Top
              </Badge>
            </div>
          )}
          
          <CardContent className="p-4 sm:p-5 md:p-6">
            <div className="flex items-start gap-3 sm:gap-4 mb-3 sm:mb-4">
              <Avatar className="w-12 h-12 sm:w-14 sm:h-14 ring-2 ring-border shrink-0 rounded-full">
                <AvatarImage src={expert.avatar || undefined} alt={expert.name} className="rounded-full" />
                <AvatarFallback className="bg-accent/10 text-accent font-semibold text-sm sm:text-base rounded-full">
                  {initials}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-base sm:text-lg mb-1">{expert.name}</h3>
                <p className="text-xs sm:text-sm text-accent line-clamp-1">{expert.title}</p>
              </div>
            </div>
            
            {justification && (
              <p className="text-xs sm:text-sm text-muted-foreground mb-3 line-clamp-2">
                {justification}
              </p>
            )}

            <div className="flex flex-wrap gap-1.5 sm:gap-2 mb-3 sm:mb-4">
              {expert.expertise.slice(0, 3).map((skill, idx) => (
                <Badge
                  key={idx}
                  variant="secondary"
                  className="rounded-full text-xs px-2 py-0.5 sm:px-3 sm:py-1"
                >
                  {skill}
                </Badge>
              ))}
            </div>

            {showStars && (
              <div className="flex items-center gap-1 mb-3">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={i}
                    className={cn(
                      "h-3 w-3 sm:h-4 sm:w-4",
                      i < stars
                        ? "fill-accent text-accent"
                        : "text-muted-foreground/30"
                    )}
                  />
                ))}
                {recommendationScore && (
                  <span className="text-xs text-muted-foreground ml-1">
                    ({recommendationScore})
                  </span>
                )}
              </div>
            )}

            <div className="flex flex-col sm:flex-row gap-2">
              <Button
                variant="default"
                className="flex-1 gap-2 h-10 sm:h-auto rounded-xl text-sm sm:text-base"
                onClick={handleChatClick}
                data-testid={`button-chat-${expert.id}`}
              >
                <MessageSquare className="w-4 h-4" />
                Conversar
              </Button>
              {onAddToCouncil && (
                <Button
                  variant="outline"
                  className="flex-1 gap-2 h-10 sm:h-auto rounded-xl text-sm sm:text-base"
                  onClick={handleCouncilClick}
                  data-testid={`button-council-${expert.id}`}
                >
                  <Users className="w-4 h-4" />
                  {councilAdded ? "Adicionado" : "Conselho"}
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  // Rich variant - Similar to Landing Tour
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.1 * index }}
      className={className}
    >
      <Card
        className="rounded-2xl hover-elevate cursor-pointer transition-all relative"
        onClick={handleChatClick}
        data-testid={`card-expert-${expert.id}`}
      >
        {isHighlyRecommended && (
          <div className="absolute -top-2 -right-2 z-10">
            <Badge className="gap-1 rounded-full px-3 py-1.5 sm:px-4 sm:py-2 bg-accent text-white shadow-sm text-xs sm:text-sm">
              <Sparkles className="h-3 w-3 sm:h-4 sm:w-4" />
              Altamente Recomendado
            </Badge>
          </div>
        )}
        
        <CardContent className="p-4 sm:p-6 md:p-8">
          <div className="flex flex-col items-center text-center space-y-4 sm:space-y-5 md:space-y-6">
            <Avatar className="h-24 w-24 sm:h-28 sm:w-28 md:h-32 md:w-32 border-3 sm:border-4 border-accent/20 ring-2 ring-offset-2 ring-accent/10 rounded-full">
              <AvatarImage src={expert.avatar || undefined} alt={expert.name} className="rounded-full" />
              <AvatarFallback className="text-xl sm:text-2xl md:text-3xl font-semibold bg-accent/10 text-accent rounded-full">
                {initials}
              </AvatarFallback>
            </Avatar>

            <div className="space-y-2 sm:space-y-3 w-full">
              <h3 className="text-xl sm:text-2xl font-semibold">{expert.name}</h3>
              <p className="text-base sm:text-lg text-accent font-medium">{expert.title}</p>
            </div>

            <div className="flex flex-wrap gap-1.5 sm:gap-2 justify-center">
              {expert.expertise.slice(0, 4).map((skill, idx) => (
                <Badge
                  key={idx}
                  variant="secondary"
                  className="rounded-full text-xs sm:text-sm px-2 py-1 sm:px-3 sm:py-1.5"
                  data-testid={`badge-expertise-${expert.id}-${idx}`}
                >
                  {skill}
                </Badge>
              ))}
            </div>

            {expert.bio && expert.bio.trim() && (
              <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed line-clamp-3">
                {expert.bio}
              </p>
            )}

            {showStars && (
              <div className="flex items-center gap-1 justify-center">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={i}
                    className={cn(
                      "h-4 w-4 sm:h-5 sm:w-5",
                      i < stars
                        ? "fill-accent text-accent"
                        : "text-muted-foreground/30"
                    )}
                    data-testid={`star-${expert.id}-${i}`}
                  />
                ))}
                {recommendationScore && (
                  <span className="text-xs sm:text-sm text-muted-foreground ml-2">
                    ({recommendationScore}/100)
                  </span>
                )}
              </div>
            )}

            {justification && (
              <div className="bg-accent/5 border border-accent/10 rounded-xl p-3 sm:p-4 w-full">
                <p className="text-xs sm:text-sm leading-relaxed">
                  <span className="font-medium text-accent flex items-center gap-1 mb-1 justify-center">
                    <Sparkles className="h-3 w-3 sm:h-4 sm:w-4" />
                    Por que recomendamos
                  </span>
                  <span className="text-muted-foreground">
                    {justification}
                  </span>
                </p>
              </div>
            )}

            <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 w-full pt-2">
              <Button
                variant="default"
                className="flex-1 gap-2 h-12 sm:h-auto rounded-xl text-sm sm:text-base"
                onClick={handleChatClick}
                data-testid={`button-chat-${expert.id}`}
              >
                <MessageSquare className="w-4 h-4 sm:w-5 sm:w-5" />
                Conversar com {expert.name.split(" ")[0]}
              </Button>
              {onAddToCouncil && (
                <Button
                  variant="outline"
                  className="gap-2 h-12 sm:h-auto rounded-xl text-sm sm:text-base"
                  onClick={handleCouncilClick}
                  data-testid={`button-council-${expert.id}`}
                >
                  <Users className="w-4 h-4 sm:w-5 sm:w-5" />
                  {councilAdded ? "No Conselho" : "Adicionar"}
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
