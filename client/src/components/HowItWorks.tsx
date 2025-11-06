import { motion } from "framer-motion";
import { Card } from "@/components/ui/card";
import { MessageSquare, Users as UsersIcon, Target } from "lucide-react";

export function HowItWorks() {
  const features = [
    {
      icon: MessageSquare,
      title: "1:1 Consultoria",
      description: "Chat direto com qualquer uma das 18 lendas do marketing",
      delay: 0
    },
    {
      icon: UsersIcon,
      title: "Sala de Conselho",
      description: "Múltiplas mentes debatendo seu desafio em tempo real",
      delay: 0.1
    },
    {
      icon: Target,
      title: "Persona Intelligence",
      description: "Conheça profundamente seu público com dados reais do YouTube",
      delay: 0.2
    }
  ];

  return (
    <section className="w-full py-20 md:py-28">
      <div className="container mx-auto px-4">
        <div className="max-w-5xl mx-auto">
          {/* Section Header */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.3 }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-semibold mb-4">
              Como Funciona
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Três formas de acessar expertise estratégica de elite
            </p>
          </motion.div>

          {/* Feature Cards */}
          <div className="grid md:grid-cols-3 gap-6 md:gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{
                  duration: 0.3,
                  delay: feature.delay,
                  ease: [0.25, 0.1, 0.25, 1]
                }}
              >
                <Card className="p-8 h-full rounded-2xl hover:shadow-lg transition-all duration-300 group hover-elevate">
                  <div className="flex flex-col items-center text-center gap-4">
                    {/* Icon */}
                    <div className="flex-shrink-0 w-16 h-16 rounded-2xl bg-accent/10 flex items-center justify-center border border-accent/20 group-hover:scale-110 transition-transform duration-300">
                      <feature.icon className="h-8 w-8 text-accent" />
                    </div>
                    
                    {/* Title */}
                    <h3 className="text-xl font-semibold">
                      {feature.title}
                    </h3>
                    
                    {/* Description */}
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {feature.description}
                    </p>
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
