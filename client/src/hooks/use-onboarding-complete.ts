import { useQuery } from "@tanstack/react-query";
import type { OnboardingStatus } from "@shared/schema";

/**
 * Shared hook to check if user completed onboarding
 * Replaces localStorage-based checks with PostgreSQL-backed status
 */
export function useOnboardingComplete() {
  const { data: onboardingStatus, isLoading } = useQuery<OnboardingStatus | null>({
    queryKey: ["/api/onboarding/status"],
    retry: false,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    queryFn: async () => {
      try {
        const res = await fetch("/api/onboarding/status", {
          credentials: "include",
        });
        
        // Se não autenticado ou não encontrado, retorna null (não é erro)
        if (res.status === 401 || res.status === 404) {
          return null;
        }
        
        if (!res.ok) {
          throw new Error(`${res.status}: ${await res.text()}`);
        }
        
        return await res.json();
      } catch (error) {
        console.log("[ONBOARDING] Failed to check status:", error);
        return null;
      }
    },
  });

  const isComplete = onboardingStatus?.completedAt !== null && onboardingStatus?.completedAt !== undefined;

  return {
    isComplete,
    isLoading,
    status: onboardingStatus,
  };
}
