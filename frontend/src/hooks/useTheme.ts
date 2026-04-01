import {
	useState,
	useEffect,
	useCallback,
	useContext,
	createContext,
	useSyncExternalStore,
} from "react";
import type { ReactNode } from "react";
import React from "react";

export type ThemeMode = "light" | "dark" | "system";
export type ResolvedTheme = "light" | "dark";

const STORAGE_KEY = "amz-theme-mode";
const MEDIA_QUERY = "(prefers-color-scheme: dark)";

function getStoredMode(): ThemeMode {
	const stored = localStorage.getItem(STORAGE_KEY);
	if (stored === "light" || stored === "dark" || stored === "system") {
		return stored;
	}
	return "system";
}

function getSystemTheme(): ResolvedTheme {
	return window.matchMedia(MEDIA_QUERY).matches ? "dark" : "light";
}

function subscribeToMediaQuery(callback: () => void): () => void {
	const mq = window.matchMedia(MEDIA_QUERY);
	mq.addEventListener("change", callback);
	return () => mq.removeEventListener("change", callback);
}

function useSystemTheme(): ResolvedTheme {
	return useSyncExternalStore(subscribeToMediaQuery, getSystemTheme);
}

interface ThemeContextValue {
	mode: ThemeMode;
	resolvedTheme: ResolvedTheme;
	isDark: boolean;
	setMode: (next: ThemeMode) => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: ReactNode }) {
	const [mode, setModeState] = useState<ThemeMode>(getStoredMode);
	const systemTheme = useSystemTheme();

	const resolvedTheme: ResolvedTheme = mode === "system" ? systemTheme : mode;
	const isDark = resolvedTheme === "dark";

	const setMode = useCallback((next: ThemeMode) => {
		localStorage.setItem(STORAGE_KEY, next);
		setModeState(next);
	}, []);

	useEffect(() => {
		document.documentElement.dataset.theme = resolvedTheme;
	}, [resolvedTheme]);

	const value = { mode, resolvedTheme, isDark, setMode };

	return React.createElement(ThemeContext.Provider, { value }, children);
}

export function useTheme(): ThemeContextValue {
	const ctx = useContext(ThemeContext);
	if (!ctx) {
		// Fallback for components outside ThemeProvider (shouldn't happen in normal use)
		const mode = getStoredMode();
		const resolved = mode === "system" ? getSystemTheme() : mode;
		return {
			mode,
			resolvedTheme: resolved,
			isDark: resolved === "dark",
			setMode: (next: ThemeMode) => {
				localStorage.setItem(STORAGE_KEY, next);
				window.location.reload();
			},
		};
	}
	return ctx;
}
