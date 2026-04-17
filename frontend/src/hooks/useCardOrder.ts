import { useCallback, useMemo, useState } from "react";

/**
 * Persists a user-chosen ordering of string IDs to localStorage.
 *
 * - On first load, returns the stored order (or `defaultOrder` if none).
 * - Every render reconciles the stored order against `defaultOrder`:
 *   * stored IDs no longer in `defaultOrder` are dropped
 *   * new IDs added to `defaultOrder` are appended at the end
 * - Callers should pass a stable `defaultOrder` array (memoize if it's derived).
 */
export function useCardOrder(
	storageKey: string,
	defaultOrder: string[],
): [string[], (next: string[]) => void] {
	const [stored, setStored] = useState<string[]>(() => loadStored(storageKey));

	const order = useMemo(
		() => reconcile(stored, defaultOrder),
		[stored, defaultOrder],
	);

	const setOrder = useCallback(
		(next: string[]) => {
			setStored(next);
			try {
				localStorage.setItem(storageKey, JSON.stringify(next));
			} catch {
				// Ignore quota / disabled storage failures
			}
		},
		[storageKey],
	);

	return [order, setOrder];
}

function loadStored(storageKey: string): string[] {
	try {
		const raw = localStorage.getItem(storageKey);
		if (!raw) return [];
		const parsed: unknown = JSON.parse(raw);
		if (!Array.isArray(parsed)) return [];
		return parsed.filter((v): v is string => typeof v === "string");
	} catch {
		return [];
	}
}

function reconcile(stored: string[], defaults: string[]): string[] {
	const defaultSet = new Set(defaults);
	const kept = stored.filter((id) => defaultSet.has(id));
	const keptSet = new Set(kept);
	const appended = defaults.filter((id) => !keptSet.has(id));
	return [...kept, ...appended];
}
