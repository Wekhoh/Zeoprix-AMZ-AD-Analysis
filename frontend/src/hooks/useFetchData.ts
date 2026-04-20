import { useCallback, useEffect, useState, type DependencyList } from "react";

/**
 * Generic data-fetch-on-deps-change hook. Replaces the boilerplate
 * repeated in 10+ pages:
 *
 *   setLoading(true)
 *   Promise.all([api.get(...)])
 *     .then(([res]) => setState(res.data))
 *     .catch(() => {})
 *     .finally(() => setLoading(false))
 *
 * Usage:
 *
 *   const { data, loading, error, refetch } = useFetchData(
 *     () => api.get<T>(url).then((r) => r.data),
 *     [url]
 *   );
 *
 * Contract matching useMemo/useCallback: caller owns the `deps` array.
 * Anything the fetcher closure captures must be listed there. The hook
 * re-fetches when any dep changes or when `refetch()` is called.
 *
 * Cancellation: if the component unmounts or deps change before the
 * fetch resolves, the stale resolution is discarded (setState is not
 * called). Safe against strict-mode double-mount.
 */

type FetchStatus<T> =
	| { kind: "idle" }
	| { kind: "loading" }
	| { kind: "success"; data: T }
	| { kind: "error"; error: Error };

export interface UseFetchDataReturn<T> {
	data: T | null;
	loading: boolean;
	error: Error | null;
	refetch: () => void;
}

export function useFetchData<T>(
	fetcher: () => Promise<T>,
	deps: DependencyList,
): UseFetchDataReturn<T> {
	const [status, setStatus] = useState<FetchStatus<T>>({ kind: "idle" });
	const [refetchTick, setRefetchTick] = useState(0);

	useEffect(() => {
		let cancelled = false;
		// Reset to loading before issuing a fresh fetch. The pinned 7.0.x
		// react-hooks plugin tolerates this pattern; if ever upgraded to
		// 7.1+ (which flags set-state-in-effect more aggressively), add
		// an eslint-disable comment on the next line.
		setStatus({ kind: "loading" });

		fetcher()
			.then((data) => {
				if (cancelled) return;
				setStatus({ kind: "success", data });
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
		// `fetcher` intentionally NOT in dep list — the whole point of this
		// hook is to let callers control refetch via their explicit `deps`
		// array (same contract as useMemo/useCallback). Re-running on every
		// render because of fetcher identity would defeat the purpose.
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [...deps, refetchTick]);

	const refetch = useCallback(() => {
		setRefetchTick((t) => t + 1);
	}, []);

	return {
		data: status.kind === "success" ? status.data : null,
		loading: status.kind === "loading",
		error: status.kind === "error" ? status.error : null,
		refetch,
	};
}
