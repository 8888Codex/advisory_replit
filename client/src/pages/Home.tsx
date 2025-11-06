import { useEffect } from "react";
import { useLocation } from "wouter";
import { useQuery } from "@tanstack/react-query";
import { Hero } from "@/components/Hero";
import { HowItWorks } from "@/components/HowItWorks";
import { ExpertShowcase } from "@/components/ExpertShowcase";
import { Button } from "@/components/ui/button";
import { AnimatedPage } from "@/components/AnimatedPage";
import { ArrowRight } from "lucide-react";
import { motion } from "framer-motion";

export default function Home() {
  const [, setLocation] = useLocation();

  // Check if user has completed onboarding
  const { data: profile } = useQuery({
    queryKey: ["/api/profile"],
    retry: false,
  });

  useEffect(() => {
    // Check if onboarding has been completed
    const onboardingComplete = localStorage.getItem("onboarding_complete");
    
    // If no localStorage flag and no profile, redirect to welcome
    if (!onboardingComplete && !profile) {
      setLocation("/welcome");
    }
  }, [profile, setLocation]);

  return (
    <AnimatedPage>
      <div className="min-h-screen">
        {/* Hero Section with Expert Showcase */}
        <Hero />

        {/* How It Works Section */}
        <HowItWorks />

        {/* Expert Showcase Section */}
        <section className="w-full py-20 md:py-28">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.3 }}
              className="text-center mb-16"
            >
              <h2 className="text-3xl md:text-4xl lg:text-5xl font-semibold mb-4">
                Conheça os Especialistas
              </h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                18 lendas do marketing esperando para ajudar você
              </p>
            </motion.div>

            <ExpertShowcase />
          </div>
        </section>

        {/* Final CTA Section */}
        <section className="w-full py-20 md:py-28 bg-muted/30">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4 }}
              className="max-w-3xl mx-auto text-center space-y-8"
            >
              <h2 className="text-3xl md:text-4xl lg:text-5xl font-semibold">
                Pronto Para Elevar Suas<br className="hidden md:block" />
                Decisões Estratégicas?
              </h2>
              
              <p className="text-lg md:text-xl text-muted-foreground leading-relaxed">
                450+ anos de expertise esperando por você.<br />
                Comece sua primeira consulta agora.
              </p>

              <div className="flex flex-col items-center gap-4 pt-4">
                <Button 
                  size="lg" 
                  className="gap-2 rounded-xl px-8 py-6 text-base md:text-lg"
                  onClick={() => setLocation("/onboarding")}
                  data-testid="button-cta-final"
                >
                  Começar Conversa Grátis
                  <ArrowRight className="h-5 w-5" />
                </Button>
                
                <p className="text-sm text-muted-foreground">
                  Sem cartão de crédito • 18 especialistas disponíveis • Acesso imediato
                </p>
              </div>
            </motion.div>
          </div>
        </section>
      </div>
    </AnimatedPage>
  );
}
