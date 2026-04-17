// Shared onboarding state. Extracted from OnboardingGuide so that react-refresh
// (Vite HMR) can safely hot-reload the OnboardingGuide *component* without the
// file also exporting a plain function.

const ONBOARDING_KEY = "amz-onboarding-done";

export function isOnboardingDismissed(): boolean {
	return localStorage.getItem(ONBOARDING_KEY) === "true";
}

export function markOnboardingDismissed(): void {
	localStorage.setItem(ONBOARDING_KEY, "true");
}
