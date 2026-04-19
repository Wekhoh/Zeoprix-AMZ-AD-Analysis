import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
	isOnboardingDismissed,
	markOnboardingDismissed,
} from "../src/utils/onboarding";

const KEY = "amz-onboarding-done";

beforeEach(() => {
	localStorage.clear();
});

afterEach(() => {
	localStorage.clear();
});

describe("onboarding dismissal state", () => {
	it("reports not-dismissed when storage is empty", () => {
		expect(isOnboardingDismissed()).toBe(false);
	});

	it("reports not-dismissed when storage has a non-'true' value", () => {
		localStorage.setItem(KEY, "false");
		expect(isOnboardingDismissed()).toBe(false);
	});

	it("reports not-dismissed when storage has an unrelated string", () => {
		// Guards against a loose `Boolean(item)` implementation
		localStorage.setItem(KEY, "1");
		expect(isOnboardingDismissed()).toBe(false);
	});

	it("reports dismissed after markOnboardingDismissed is called", () => {
		expect(isOnboardingDismissed()).toBe(false);
		markOnboardingDismissed();
		expect(isOnboardingDismissed()).toBe(true);
	});

	it("markOnboardingDismissed writes exact 'true' string to expected key", () => {
		markOnboardingDismissed();
		expect(localStorage.getItem(KEY)).toBe("true");
	});

	it("markOnboardingDismissed is idempotent", () => {
		markOnboardingDismissed();
		markOnboardingDismissed();
		expect(localStorage.getItem(KEY)).toBe("true");
		expect(isOnboardingDismissed()).toBe(true);
	});
});
