import { useEffect, useState } from "react";
import api from "../api/client";

export interface AdTypeField {
	key: string;
	label: string;
	exclusive: boolean;
}

export interface AdTypeCatalog {
	ad_type: string;
	label: string;
	fields: AdTypeField[];
	exclusive_fields: string[];
}

export interface UseAdTypeCatalogReturn {
	catalog: AdTypeCatalog | null;
	loading: boolean;
	error: Error | null;
}

// Module-scope cache. The catalog is fully static from the backend's
// perspective (same payload every call), so caching for the lifetime of
// the page avoids re-fetching when the user flips between ad-type tabs.
const cache = new Map<string, AdTypeCatalog>();

export function _clearAdTypeCatalogCache(): void {
	cache.clear();
}

type FetchStatus =
	| { kind: "idle" }
	| { kind: "loading" }
	| { kind: "error"; error: Error };

export function useAdTypeCatalog(
	adType: string | null | undefined,
): UseAdTypeCatalogReturn {
	const key = adType ? adType.toUpperCase() : null;

	// Tick only exists to trigger a rerender after the imperative `cache`
	// Map is populated — catalog itself is derived, not stored in state.
	const [, setTick] = useState(0);
	const [status, setStatus] = useState<FetchStatus>({ kind: "idle" });

	useEffect(() => {
		if (!key || cache.has(key)) return;

		let cancelled = false;
		// eslint-disable-next-line react-hooks/set-state-in-effect -- canonical fetch-reset: clear prior status on key change before issuing a new request (same pattern as Campaigns.tsx data-fetch effect)
		setStatus({ kind: "loading" });

		api
			.get<AdTypeCatalog>(`/ad-types/${key}`)
			.then((res) => {
				if (cancelled) return;
				cache.set(key, res.data);
				setTick((t) => t + 1);
				setStatus({ kind: "idle" });
			})
			.catch((err: unknown) => {
				if (cancelled) return;
				setStatus({
					kind: "error",
					error: err instanceof Error ? err : new Error(String(err)),
				});
			});

		return () => {
			cancelled = true;
		};
	}, [key]);

	const catalog = key ? (cache.get(key) ?? null) : null;

	return {
		catalog,
		loading: status.kind === "loading",
		error: status.kind === "error" ? status.error : null,
	};
}
