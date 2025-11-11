import { useState } from 'react';
import { Sparkles, Loader2, Undo2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from '@/components/ui/tooltip';
import { useToast } from '@/hooks/use-toast';
import { apiRequest } from '@/lib/queryClient';
import { motion, AnimatePresence } from 'framer-motion';

interface AIEnhanceButtonProps {
  currentText: string;
  fieldType: 'target_audience' | 'challenge' | 'goal';
  context?: Record<string, any>;
  onEnhanced: (enhancedText: string) => void;
  disabled?: boolean;
}

export function AIEnhanceButton({
  currentText,
  fieldType,
  context = {},
  onEnhanced,
  disabled
}: AIEnhanceButtonProps) {
  const [isEnhancing, setIsEnhancing] = useState(false);
  const [previousText, setPreviousText] = useState<string | null>(null);
  const [showUndo, setShowUndo] = useState(false);
  const { toast } = useToast();
  
  const handleEnhance = async () => {
    // Validation
    if (!currentText || currentText.length < 10) {
      toast({
        title: "Texto muito curto",
        description: "Escreva pelo menos uma frase para eu poder melhorar!",
        variant: "destructive"
      });
      return;
    }
    
    setIsEnhancing(true);
    
    try {
      const response = await apiRequest('/api/ai/enhance-prompt', {
        method: 'POST',
        body: JSON.stringify({
          text: currentText,
          field_type: fieldType,
          context
        }),
        headers: { 'Content-Type': 'application/json' }
      });
      
      const data = await response.json();
      
      // Save current text for undo
      setPreviousText(currentText);
      
      // Update field with enhanced text
      onEnhanced(data.enhanced_text);
      
      // Show success feedback
      toast({
        title: "✨ Texto melhorado com sucesso!",
        description: `Expandido de ${data.original_length} para ${data.enhanced_length} caracteres (${data.improvement_ratio}x)`,
      });
      
      // Show undo button for 10 seconds
      setShowUndo(true);
      setTimeout(() => setShowUndo(false), 10000);
      
    } catch (error: any) {
      console.error('AI enhance error:', error);
      
      // Handle specific errors
      if (error.message?.includes('429')) {
        toast({
          title: "Limite atingido",
          description: "Você atingiu o limite de 20 melhorias por hora. Tente novamente em alguns minutos.",
          variant: "destructive"
        });
      } else {
        toast({
          title: "Erro ao melhorar texto",
          description: error.message || "Tente novamente em alguns segundos",
          variant: "destructive"
        });
      }
    } finally {
      setIsEnhancing(false);
    }
  };
  
  const handleUndo = () => {
    if (previousText) {
      onEnhanced(previousText);
      setShowUndo(false);
      setPreviousText(null);
      
      toast({
        title: "Texto restaurado",
        description: "Voltamos ao texto original",
      });
    }
  };
  
  const canEnhance = !disabled && !isEnhancing && currentText && currentText.length >= 10;
  
  return (
    <TooltipProvider>
      <div className="flex items-center gap-2">
        <AnimatePresence>
          {showUndo && previousText && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              transition={{ duration: 0.2 }}
            >
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={handleUndo}
                    className="gap-2 text-muted-foreground hover:text-foreground"
                  >
                    <Undo2 className="h-4 w-4" />
                    Desfazer
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Restaurar texto original</p>
                </TooltipContent>
              </Tooltip>
            </motion.div>
          )}
        </AnimatePresence>
        
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleEnhance}
              disabled={!canEnhance}
              className="gap-2 border-primary/50 hover:bg-primary/10 hover:border-primary transition-all"
            >
              {isEnhancing ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Melhorando...</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  <span>Melhorar com IA</span>
                </>
              )}
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p className="max-w-xs">
              {canEnhance 
                ? "A IA vai expandir e detalhar seu texto, tornando-o mais estratégico e completo"
                : "Escreva pelo menos uma frase completa para ativar"}
            </p>
          </TooltipContent>
        </Tooltip>
      </div>
    </TooltipProvider>
  );
}

