import { motion } from "framer-motion";
import { Check, X, Loader2, Search, Sparkles } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import type { ExpertStatus } from "@/hooks/useCouncilStream";

interface ExpertAvatarProps {
  status: ExpertStatus;
  index: number;
}

const statusConfig = {
  waiting: {
    icon: null,
    color: "text-muted-foreground",
    bgColor: "bg-muted",
    label: "Aguardando",
  },
  researching: {
    icon: Search,
    color: "text-accent",
    bgColor: "bg-accent/10",
    label: "Pesquisando",
  },
  analyzing: {
    icon: Sparkles,
    color: "text-accent",
    bgColor: "bg-accent/10",
    label: "Analisando",
  },
  completed: {
    icon: Check,
    color: "text-green-500",
    bgColor: "bg-green-500/10",
    label: "Concluído",
  },
  failed: {
    icon: X,
    color: "text-destructive",
    bgColor: "bg-destructive/10",
    label: "Falhou",
  },
};

export function ExpertAvatar({ status, index }: ExpertAvatarProps) {
  const config = statusConfig[status.status];
  const Icon = config.icon;
  const isActive = status.status === "analyzing" || status.status === "researching";

  // Get initials from expert name
  const initials = status.expertName
    ?.split(" ")
    .map((n) => n[0])
    .join("")
    .substring(0, 2)
    .toUpperCase() || "?";

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.1, type: "spring", stiffness: 200 }}
      whileHover={{ y: -4, scale: 1.05 }}
      data-testid={`expert-avatar-${status.expertId}`}
    >
      <Card className={`p-4 relative overflow-hidden rounded-xl transition-all ${
        isActive ? "ring-2 ring-accent/40 shadow-lg shadow-accent/20" : 
        status.status === "completed" ? "ring-2 ring-primary/30 shadow-md shadow-primary/10" :
        "hover:shadow-md"
      }`}>
        {/* Animated background for active experts */}
        {isActive && (
          <>
            <motion.div
              className="absolute inset-0 bg-gradient-to-br from-accent/10 to-transparent"
              animate={{ opacity: [0.3, 0.7, 0.3] }}
              transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
            />
            <div className="absolute inset-0 bg-grid-pattern-dense opacity-5" />
          </>
        )}
        
        {/* Completed glow */}
        {status.status === "completed" && (
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-accent/5" />
        )}

        <div className="relative space-y-3">
          {/* Avatar with progress ring */}
          <div className="relative mx-auto w-20 h-20">
            {/* Progress ring */}
            <svg className="absolute inset-0 w-full h-full -rotate-90">
              {/* Background ring */}
              <circle
                cx="40"
                cy="40"
                r="36"
                fill="none"
                stroke="currentColor"
                strokeWidth="4"
                className="text-muted"
                opacity="0.2"
              />
              {/* Progress ring */}
              <motion.circle
                cx="40"
                cy="40"
                r="36"
                fill="none"
                stroke="currentColor"
                strokeWidth="4"
                className={config.color}
                strokeLinecap="round"
                strokeDasharray={226} // 2 * π * 36
                initial={{ strokeDashoffset: 226 }}
                animate={{ strokeDashoffset: 226 - (226 * status.progress) / 100 }}
                transition={{ duration: 0.5 }}
              />
            </svg>

            {/* Avatar circle with photo */}
            <div className="absolute inset-2">
              <Avatar className="w-full h-full ring-2 ring-card">
                <AvatarImage 
                  src={status.expertAvatar} 
                  alt={status.expertName}
                  className="object-cover"
                />
                <AvatarFallback className={`text-lg font-semibold ${config.bgColor} ${config.color}`}>
                  {initials}
                </AvatarFallback>
              </Avatar>
            </div>

            {/* Status icon overlay with animation */}
            {Icon && (
              <motion.div
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ type: "spring", stiffness: 300, damping: 20 }}
                className={`absolute -bottom-1 -right-1 w-8 h-8 rounded-full ${
                  status.status === "completed" 
                    ? "bg-green-500 text-white shadow-lg shadow-green-500/50" 
                    : `${config.bgColor} ${config.color}`
                } flex items-center justify-center border-3 border-card`}
              >
                {isActive ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                  >
                    <Icon className="w-4 h-4" />
                  </motion.div>
                ) : (
                  <Icon className="w-4 h-4" />
                )}
              </motion.div>
            )}
          </div>

          {/* Expert name */}
          <div className="text-center">
            <p className="font-semibold text-sm line-clamp-2">
              {status.expertName || "Expert"}
            </p>
            <p className={`text-xs mt-1 ${config.color}`}>{config.label}</p>
          </div>

          {/* Stats (when completed) */}
          {status.status === "completed" && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-xs text-center space-y-1 text-muted-foreground"
            >
              {status.insightCount !== undefined && (
                <div>{status.insightCount} insight{status.insightCount !== 1 ? 's' : ''}</div>
              )}
              {status.recommendationCount !== undefined && (
                <div>{status.recommendationCount} recomendaç{status.recommendationCount !== 1 ? 'ões' : 'ão'}</div>
              )}
            </motion.div>
          )}

          {/* Error message */}
          {status.status === "failed" && status.error && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-xs text-destructive text-center line-clamp-2"
            >
              {status.error}
            </motion.div>
          )}
        </div>
      </Card>
    </motion.div>
  );
}
