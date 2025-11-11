import { motion } from "framer-motion";
import { ExpertAvatar } from "./ExpertAvatar";
import { ActivityFeed } from "./ActivityFeed";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Users } from "lucide-react";
import type { ExpertStatus, ActivityEvent } from "@/hooks/useCouncilStream";

interface CouncilAnimationProps {
  expertStatuses: ExpertStatus[];
  activityFeed: ActivityEvent[];
  isStreaming: boolean;
}

export function CouncilAnimation({
  expertStatuses,
  activityFeed,
  isStreaming,
}: CouncilAnimationProps) {
  const completedCount = expertStatuses.filter((s) => s.status === "completed").length;
  const totalCount = expertStatuses.length;

  return (
    <div className="space-y-6" data-testid="council-animation">
      {/* Premium Header with progress */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
        className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/20 via-accent/10 to-primary/20 p-6 border border-primary/20"
      >
        <div className="absolute inset-0 bg-grid-pattern opacity-10" />
        
        <div className="relative z-10 text-center">
          <div className="flex items-center justify-center gap-3 mb-3">
            <motion.div
              className="p-3 rounded-xl bg-gradient-to-br from-primary to-accent shadow-lg"
              animate={{ 
                rotate: isStreaming ? 360 : 0,
                scale: isStreaming ? [1, 1.05, 1] : 1
              }}
              transition={{ 
                rotate: { duration: 3, repeat: isStreaming ? Infinity : 0, ease: "linear" },
                scale: { duration: 2, repeat: isStreaming ? Infinity : 0, ease: "easeInOut" }
              }}
            >
              <Users className="h-6 w-6 text-white" />
            </motion.div>
            <h2 className="text-2xl font-bold text-gradient-primary">Conselho em Sessão</h2>
          </div>
          <p className="text-muted-foreground text-sm">
            {isStreaming
              ? `Analisando... (${completedCount}/${totalCount} especialista${totalCount !== 1 ? 's' : ''} concluído${completedCount !== 1 ? 's' : ''})`
              : `Análise completa (${completedCount}/${totalCount} especialista${totalCount !== 1 ? 's' : ''})`}
          </p>
          
          {/* Progress bar */}
          <motion.div className="mt-4 h-2 bg-muted/30 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-accent to-primary rounded-full"
              initial={{ width: "0%" }}
              animate={{ width: `${(completedCount / totalCount) * 100}%` }}
              transition={{ duration: 0.5, ease: "easeOut" }}
            />
          </motion.div>
        </div>
      </motion.div>

      {/* Grid + Feed Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Expert Avatars Grid */}
        <div className="lg:col-span-2">
          <Card className="rounded-2xl glass-premium border-accent/20 shadow-xl">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-accent/10 ring-2 ring-accent/20">
                  <Users className="h-5 w-5 text-accent" />
                </div>
                <div>
                  <CardTitle className="font-semibold">Painel de Especialistas</CardTitle>
                  <CardDescription>
                    Lendas do marketing analisando seu desafio em tempo real
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {expertStatuses.map((status, index) => (
                  <ExpertAvatar key={status.expertId} status={status} index={index} />
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Activity Feed */}
        <div className="lg:col-span-1">
          <ActivityFeed activities={activityFeed} />
        </div>
      </div>
    </div>
  );
}
