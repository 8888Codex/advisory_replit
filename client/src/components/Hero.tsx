import { Button } from "@/components/ui/button";
import { ArrowRight, Users } from "lucide-react";
import { Link } from "wouter";
import { motion } from "framer-motion";
import { useRipple } from "@/hooks/use-ripple";
import { useQuery } from "@tanstack/react-query";

export function Hero() {
  const { createRipple } = useRipple();
  
  // Get experts for trust badge
  const { data: experts } = useQuery<Array<{id: string; name: string; avatar: string}>>({
    queryKey: ["/api/experts"],
  });
  
  return (
    <section className="relative w-full py-12 md:py-20">
      <div className="container mx-auto px-4">
        <div className="flex flex-col items-center text-center max-w-4xl mx-auto gap-6">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25 }}
            className="inline-flex items-center gap-2 bg-accent/10 rounded-full px-5 py-2 text-xs md:text-sm border border-accent/20"
          >
            <Users className="h-3 w-3 md:h-4 md:w-4 text-accent" />
            <span className="font-medium">
              18 Lendas do Marketing
            </span>
          </motion.div>

          {/* Main Headline - Compressed */}
          <motion.h1
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, delay: 0.05 }}
            className="text-3xl md:text-5xl lg:text-6xl font-semibold tracking-tight leading-tight"
          >
            450+ Anos de Expertise<br />
            em Marketing.{" "}
            <span className="text-accent">
              Agora em Uma Conversa.
            </span>
          </motion.h1>

          {/* Subheadline - Compressed */}
          <motion.p
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, delay: 0.1 }}
            className="text-base md:text-lg text-muted-foreground max-w-xl"
          >
            Consulte Kotler, Ogilvy, Godin e mais 15 mestres. Respostas em segundos.
          </motion.p>

          {/* Primary CTA - ABOVE THE FOLD */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, delay: 0.15 }}
            className="flex flex-col items-center gap-3 mt-2"
          >
            <Link href="/onboarding">
              <Button 
                size="lg" 
                className="gap-2 rounded-xl px-8 py-5 text-base press-effect" 
                data-testid="button-start-free"
                onClick={createRipple}
              >
                Começar Conversa Grátis
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            
            {/* Social Proof */}
            <p className="text-xs md:text-sm text-muted-foreground">
              Sem cartão • Acesso imediato
            </p>
          </motion.div>

          {/* Trust Badge - BELOW CTA */}
          {experts && experts.length > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3, delay: 0.2 }}
              className="flex items-center justify-center mt-4"
            >
              <div className="flex items-center -space-x-2">
                {experts.slice(0, 12).map((expert, idx) => (
                  <div
                    key={expert.id}
                    className="relative w-8 h-8 md:w-10 md:h-10 rounded-full overflow-hidden border-2 border-background shadow-sm"
                  >
                    {expert.avatar ? (
                      <img
                        src={expert.avatar}
                        alt={expert.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full bg-gradient-to-br from-accent/30 to-accent/20 flex items-center justify-center">
                        <span className="text-[10px] font-semibold text-accent">
                          {expert.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                        </span>
                      </div>
                    )}
                  </div>
                ))}
                <div className="pl-3 text-xs md:text-sm text-muted-foreground font-medium">
                  +6 mais
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </section>
  );
}
