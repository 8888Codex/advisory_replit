import { motion } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MessageSquare } from "lucide-react";
import { useLocation } from "wouter";

interface Expert {
  id: string;
  name: string;
  title: string;
  avatar: string;
  expertise: string[];
}

export function ExpertShowcase() {
  const [, setLocation] = useLocation();
  
  const { data: experts, isLoading } = useQuery<Expert[]>({
    queryKey: ["/api/experts"],
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

  if (isLoading || !experts) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {Array.from({ length: 18 }).map((_, i) => (
          <div
            key={i}
            className="aspect-square rounded-2xl bg-muted/50 animate-pulse"
          />
        ))}
      </div>
    );
  }

  const expertQuotes: Record<string, string> = {
    "Philip Kotler": "Marketing é criar valor.",
    "David Ogilvy": "Expertise vende.",
    "Claude C. Hopkins": "Propaganda é vender.",
    "David Aaker": "Brand equity é tudo.",
    "Jay Levinson": "Marketing é promover.",
    "Al Ries & Jack Trout": "Posicionamento é mental.",
    "Simon Sinek": "Start with Why.",
    "Donald Miller": "Clareza sempre vence.",
    "Dan Kennedy": "Quem gasta mais, vence.",
    "Eugene Schwartz": "Copy canaliza desejo.",
    "Drayton Bird": "Teste tudo.",
    "Robert Cialdini": "Influência é ciência.",
    "Daniel Kahneman": "Nada é tão importante.",
    "Seth Godin": "Conte histórias.",
    "Ann Handley": "Cliente é o herói.",
    "Neil Patel": "SEO é parceria.",
    "Gary Vaynerchuk": "Relacionamentos em escala.",
    "Jay Abraham": "Entregue valor."
  };

  return (
    <div className="w-full max-w-7xl mx-auto">
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 md:gap-6">
        {experts.slice(0, 18).map((expert, index) => (
          <motion.div
            key={expert.id}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{
              duration: 0.25,
              delay: index * 0.03,
              ease: [0.25, 0.1, 0.25, 1]
            }}
          >
            {/* Simple Card - Touch-Friendly */}
            <div className="flex flex-col gap-3 p-4 rounded-2xl bg-card border border-border hover-elevate transition-all duration-200">
              {/* Avatar */}
              <div className="relative aspect-square w-full">
                {expert.avatar ? (
                  <img
                    src={expert.avatar}
                    alt={expert.name}
                    className="w-full h-full object-cover rounded-xl"
                  />
                ) : (
                  <div className="w-full h-full rounded-xl bg-gradient-to-br from-accent/20 to-accent/10 flex items-center justify-center">
                    <span className="text-2xl md:text-3xl font-semibold text-accent">
                      {expert.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                    </span>
                  </div>
                )}
              </div>

              {/* Info - Always Visible */}
              <div className="flex flex-col gap-2">
                {/* Name */}
                <h3 className="font-semibold text-sm line-clamp-2 min-h-[2.5rem]">
                  {expert.name}
                </h3>
                
                {/* Quote - Hidden on mobile for space */}
                <p className="hidden md:block text-xs text-muted-foreground line-clamp-2 italic min-h-[2.5rem]">
                  "{expertQuotes[expert.name] || expert.title}"
                </p>

                {/* Expertise Badge */}
                {expert.expertise && expert.expertise[0] && (
                  <Badge 
                    variant="secondary" 
                    className="w-fit text-xs truncate max-w-full"
                  >
                    {expert.expertise[0]}
                  </Badge>
                )}

                {/* CTA Button - Always Tappable */}
                <Button
                  size="sm"
                  variant="default"
                  className="w-full gap-1.5 text-xs mt-1"
                  onClick={() => handleConsult(expert.id)}
                  data-testid={`button-consult-${expert.id}`}
                >
                  <MessageSquare className="h-3 w-3" />
                  Consultar
                </Button>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
