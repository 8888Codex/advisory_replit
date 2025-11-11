import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Info, CheckCircle2, AlertCircle } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { ActivityEvent } from "@/hooks/useCouncilStream";

interface ActivityFeedProps {
  activities: ActivityEvent[];
  className?: string;
}

const eventConfig = {
  info: {
    icon: Info,
    color: "text-accent",
    bgColor: "bg-accent/10",
  },
  success: {
    icon: CheckCircle2,
    color: "text-green-500",
    bgColor: "bg-green-500/10",
  },
  error: {
    icon: AlertCircle,
    color: "text-destructive",
    bgColor: "bg-destructive/10",
  },
};

export function ActivityFeed({ activities, className = "" }: ActivityFeedProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new activity added
  useEffect(() => {
    if (scrollRef.current) {
      const scrollElement = scrollRef.current.querySelector("[data-radix-scroll-area-viewport]");
      if (scrollElement) {
        scrollElement.scrollTop = scrollElement.scrollHeight;
      }
    }
  }, [activities]);

  return (
    <div className={`space-y-3 ${className}`} data-testid="activity-feed">
      <div className="glass-premium rounded-xl p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-accent/10 ring-1 ring-accent/20">
              <Info className="h-4 w-4 text-accent" />
            </div>
            <h3 className="font-semibold text-sm">Feed de Atividades</h3>
          </div>
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 300 }}
          >
            <span className="text-xs px-2 py-1 rounded-full bg-primary/10 text-primary font-medium">
              {activities.length}
            </span>
          </motion.div>
        </div>

      <ScrollArea ref={scrollRef} className="h-[400px] rounded-lg">
        <AnimatePresence mode="popLayout">
          {activities.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center justify-center h-full text-muted-foreground text-sm"
            >
              Nenhuma atividade ainda...
            </motion.div>
          ) : (
            <div className="space-y-3">
              {activities.map((activity, index) => {
                const config = eventConfig[activity.type];
                const Icon = config.icon;

                return (
                  <motion.div
                    key={activity.id}
                    initial={{ opacity: 0, x: -20, scale: 0.95 }}
                    animate={{ opacity: 1, x: 0, scale: 1 }}
                    exit={{ opacity: 0, x: 20, scale: 0.95 }}
                    transition={{ delay: index * 0.05, duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
                    whileHover={{ x: 4 }}
                    className={`flex gap-3 p-3 rounded-xl border ${
                      activity.type === "success" 
                        ? "bg-gradient-to-br from-green-500/5 to-green-500/10 border-green-500/20" 
                        : activity.type === "error"
                        ? "bg-destructive/5 border-destructive/20"
                        : "bg-muted/30 border-border/50"
                    } backdrop-blur-sm`}
                    data-testid={`activity-event-${activity.id}`}
                  >
                    <motion.div
                      initial={{ scale: 0, rotate: -180 }}
                      animate={{ scale: 1, rotate: 0 }}
                      transition={{ type: "spring", stiffness: 300, delay: index * 0.05 + 0.1 }}
                      className={`p-1.5 rounded-lg ${config.bgColor} flex-shrink-0`}
                    >
                      <Icon className={`w-4 h-4 ${config.color}`} />
                    </motion.div>
                    
                    <div className="flex-1 min-w-0">
                      {activity.expertName && (
                        <p className="font-semibold text-sm text-accent">{activity.expertName}</p>
                      )}
                      <p className="text-sm text-foreground/90 leading-relaxed">{activity.message}</p>
                      <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                        <span className="inline-block w-1 h-1 rounded-full bg-accent animate-pulse-subtle" />
                        {new Date(activity.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          )}
        </AnimatePresence>
      </ScrollArea>
      </div>
    </div>
  );
}
