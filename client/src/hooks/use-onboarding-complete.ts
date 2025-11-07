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
  });

  const isComplete = onboardingStatus?.completedAt !== null && onboardingStatus?.completedAt !== undefined;

  return {
    isComplete,
    isLoading,
    status: onboardingStatus,
  };
}
