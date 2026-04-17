import { useCallback, useMemo, useState } from "react";

/**
 * Persists a set of hidden column keys to localStorage.
 *
 * Usage:
 *   const [hiddenKeys, toggleColumn, resetColumns] = useColumnVisibility(
 *     "campaigns_hidden_cols",
 *     ["name", "ad_type", "status", "spend", "orders", ...]  // all known keys
 *   );
 *   const visibleColumns = allColumns.filter(c => !hiddenKeys.has(c.key));
 *
 * - Stored keys not present in `allKeys` are ignored (stale keys after schema
 *   changes don't leak).
 * - Returns a Set for O(1) lookup during render.
 */
export function useColumnVisibility(
	storageKey: string,
	allKeys: string[],
): [Set<string>, (key: string) => void, () => void] {
	const [rawHidden, setRawHidden] = useState<string[]>(() =>
		loadHidden(storageKey),
	);

	const hiddenKeys = useMemo(() => {
		const allowed = new Set(allKeys);
		return new Set(rawHidden.filter((k) => allowed.has(k)));
	}, [rawHidden, allKeys]);

	const toggleColumn = useCallback(
		(key: string) => {
			setRawHidden((prev) => {
				const set = new Set(prev);
				if (set.has(key)) {
					set.delete(key);
				} else {
					set.add(key);
				}
				const next = [...set];
				try {
					localStorage.setItem(storageKey, JSON.stringify(next));
				} catch {
					// Ignore quota / disabled storage failures
				}
				return next;
			});
		},
		[storageKey],
	);

	const resetColumns = useCallback(() => {
		setRawHidden([]);
		try {
			localStorage.removeItem(storageKey);
		} catch {
			// Ignore
		}
	}, [storageKey]);

	return [hiddenKeys, toggleColumn, resetColumns];
}

function loadHidden(storageKey: string): string[] {
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
