import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { User } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { motion } from "framer-motion";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface ChatMessageProps {
  message: Message;
  expertName?: string;
  expertAvatar?: string;
}

export function ChatMessage({ message, expertName, expertAvatar }: ChatMessageProps) {
  const isUser = message.role === "user";
  const initials = expertName
    ?.split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2) || "AI";

  return (
    <motion.div
      initial={{ opacity: 0, x: isUser ? 20 : -20, y: 10, scale: 0.95 }}
      animate={{ opacity: 1, x: 0, y: 0, scale: 1 }}
      transition={{ 
        duration: 0.3, 
        ease: [0.4, 0, 0.2, 1]
      }}
      className={cn(
        "flex gap-3 mb-4",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
      data-testid={`message-${message.id}`}
    >
      {/* Avatar for expert/user */}
      <Avatar className={cn(
        "h-10 w-10 flex-shrink-0 transition-all duration-300",
        isUser 
          ? "ring-2 ring-accent/20" 
          : "ring-2 ring-primary/30 shadow-md shadow-primary/20"
      )}>
        {isUser ? (
          <AvatarFallback className="bg-accent/10">
            <User className="h-5 w-5" />
          </AvatarFallback>
        ) : (
          <>
            <AvatarImage src={expertAvatar} alt={expertName} />
            <AvatarFallback className="text-xs bg-accent/10 text-accent">{initials}</AvatarFallback>
          </>
        )}
      </Avatar>

      <div className={cn("flex flex-col gap-1 max-w-[75%]", isUser ? "items-end" : "items-start")}>
        {!isUser && expertName && (
          <span className="text-xs font-medium text-muted-foreground px-3">
            {expertName}
          </span>
        )}
        <motion.div
          initial={{ scale: 0.95 }}
          animate={{ scale: 1 }}
          transition={{ duration: 0.2, delay: 0.1 }}
          className={cn(
            "rounded-2xl px-4 py-3 text-sm shadow-md",
            isUser
              ? "bg-gradient-to-br from-primary to-accent text-white shadow-primary/30"
              : "glass-premium"
          )}
        >
          {isUser ? (
            <p className="leading-relaxed whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  h1: ({ children }) => (
                    <h1 className="text-lg font-bold mt-4 mb-2 first:mt-0">{children}</h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="text-base font-bold mt-3 mb-2 first:mt-0">{children}</h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="text-sm font-semibold mt-3 mb-1 first:mt-0">{children}</h3>
                  ),
                  p: ({ children }) => (
                    <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>
                  ),
                  ul: ({ children }) => (
                    <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>
                  ),
                  li: ({ children }) => (
                    <li className="leading-relaxed">{children}</li>
                  ),
                  strong: ({ children }) => (
                    <strong className="font-semibold">{children}</strong>
                  ),
                  em: ({ children }) => (
                    <em className="italic">{children}</em>
                  ),
                  code: ({ children, className }) => {
                    const isInline = !className;
                    return isInline ? (
                      <code className="bg-muted px-1.5 py-0.5 rounded text-xs font-mono">
                        {children}
                      </code>
                    ) : (
                      <code className="block bg-muted p-3 rounded-lg text-xs font-mono overflow-x-auto mb-2">
                        {children}
                      </code>
                    );
                  },
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-4 border-primary pl-4 italic my-2">
                      {children}
                    </blockquote>
                  ),
                  hr: () => <hr className="my-4 border-border" />,
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </motion.div>
      </div>
    </motion.div>
  );
}

// Typing Indicator Component
export function TypingIndicator({ expertName, expertAvatar }: { expertName?: string; expertAvatar?: string }) {
  const initials = expertName
    ?.split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2) || "AI";

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="flex gap-3 mb-4"
    >
      <Avatar className="h-10 w-10 flex-shrink-0 ring-2 ring-primary/30 shadow-md shadow-primary/20">
        <AvatarImage src={expertAvatar} alt={expertName} />
        <AvatarFallback className="text-xs bg-accent/10 text-accent">{initials}</AvatarFallback>
      </Avatar>
      
      <div className="flex flex-col gap-1">
        {expertName && (
          <span className="text-xs font-medium text-muted-foreground px-3">
            {expertName}
          </span>
        )}
        <div className="rounded-2xl px-5 py-3 glass-premium">
          <div className="flex gap-1.5">
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                className="w-2 h-2 rounded-full bg-primary"
                animate={{
                  scale: [1, 1.3, 1],
                  opacity: [0.5, 1, 0.5],
                }}
                transition={{
                  duration: 1.2,
                  repeat: Infinity,
                  delay: i * 0.15,
                  ease: "easeInOut",
                }}
              />
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
