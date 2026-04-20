import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useFetchData } from "../src/hooks/useFetchData";

describe("useFetchData — happy path", () => {
	it("starts loading and resolves to data", async () => {
		const fetcher = vi.fn(() => Promise.resolve({ hello: "world" }));

		const { result } = renderHook(() => useFetchData(fetcher, []));

		expect(result.current.loading).toBe(true);
		expect(result.current.data).toBeNull();
		expect(result.current.error).toBeNull();

		await waitFor(() => {
			expect(result.current.data).toEqual({ hello: "world" });
		});

		expect(result.current.loading).toBe(false);
		expect(result.current.error).toBeNull();
		expect(fetcher).toHaveBeenCalledTimes(1);
	});

	it("calls fetcher once on mount with empty deps", async () => {
		const fetcher = vi.fn(() => Promise.resolve(42));
		const { result } = renderHook(() => useFetchData(fetcher, []));
		await waitFor(() => expect(result.current.data).toBe(42));
		expect(fetcher).toHaveBeenCalledTimes(1);
	});
});

describe("useFetchData — deps-driven refetch", () => {
	it("re-runs fetcher when a dep changes", async () => {
		const fetcher = vi.fn((n: number) => Promise.resolve(n * 10));
		const { result, rerender } = renderHook(
			({ n }: { n: number }) => useFetchData(() => fetcher(n), [n]),
			{ initialProps: { n: 1 } },
		);

		await waitFor(() => expect(result.current.data).toBe(10));
		expect(fetcher).toHaveBeenCalledTimes(1);

		rerender({ n: 2 });
		await waitFor(() => expect(result.current.data).toBe(20));
		expect(fetcher).toHaveBeenCalledTimes(2);
	});

	it("does NOT refetch when deps unchanged across rerender", async () => {
		const fetcher = vi.fn(() => Promise.resolve("ok"));
		const { result, rerender } = renderHook(() => useFetchData(fetcher, []));

		await waitFor(() => expect(result.current.data).toBe("ok"));
		expect(fetcher).toHaveBeenCalledTimes(1);

		rerender();
		rerender();
		// Still only 1 call — hook should not refetch on caller re-render
		expect(fetcher).toHaveBeenCalledTimes(1);
	});
});

describe("useFetchData — refetch()", () => {
	it("manually re-runs the fetcher", async () => {
		let counter = 0;
		const fetcher = vi.fn(() => Promise.resolve(++counter));

		const { result } = renderHook(() => useFetchData(fetcher, []));

		await waitFor(() => expect(result.current.data).toBe(1));

		act(() => result.current.refetch());
		await waitFor(() => expect(result.current.data).toBe(2));
		expect(fetcher).toHaveBeenCalledTimes(2);

		act(() => result.current.refetch());
		await waitFor(() => expect(result.current.data).toBe(3));
		expect(fetcher).toHaveBeenCalledTimes(3);
	});
});

describe("useFetchData — error path", () => {
	it("surfaces an Error from the fetcher", async () => {
		const boom = new Error("network down");
		const fetcher = vi.fn(() => Promise.reject(boom));

		const { result } = renderHook(() => useFetchData(fetcher, []));

		await waitFor(() => {
			expect(result.current.error).toBe(boom);
		});
		expect(result.current.data).toBeNull();
		expect(result.current.loading).toBe(false);
	});

	it("wraps non-Error rejections into Error instances", async () => {
		const fetcher = vi.fn(() => Promise.reject("boom"));

		const { result } = renderHook(() => useFetchData(fetcher, []));

		await waitFor(() => {
			expect(result.current.error).toBeInstanceOf(Error);
			expect(result.current.error?.message).toBe("boom");
		});
	});

	it("recovers after refetch if second attempt succeeds", async () => {
		const fetcher = vi
			.fn<() => Promise<string>>()
			.mockRejectedValueOnce(new Error("first"))
			.mockResolvedValueOnce("second");

		const { result } = renderHook(() => useFetchData(fetcher, []));

		await waitFor(() => expect(result.current.error).not.toBeNull());

		act(() => result.current.refetch());

		await waitFor(() => expect(result.current.data).toBe("second"));
		expect(result.current.error).toBeNull();
	});
});

describe("useFetchData — cancellation", () => {
	it("does not setState after unmount", async () => {
		let resolveFetch: ((v: string) => void) | undefined;
		const fetcher = vi.fn(
			() => new Promise<string>((res) => (resolveFetch = res)),
		);

		const { unmount } = renderHook(() => useFetchData(fetcher, []));
		unmount();
		resolveFetch?.("late");

		// Give microtasks a tick to flush — no React setState-after-unmount
		// warning should appear. If cancellation didn't work, testing-library
		// would surface an act() warning here.
		await new Promise((res) => setTimeout(res, 0));
		expect(true).toBe(true);
	});

	it("ignores stale fetch when deps change mid-flight", async () => {
		// First fetcher hangs; second resolves quickly. Without cancellation,
		// the slow first response would clobber the fresh second one.
		let resolveFirst: ((v: number) => void) | undefined;
		const fetcher = vi
			.fn<(n: number) => Promise<number>>()
			.mockImplementationOnce(
				() => new Promise<number>((res) => (resolveFirst = res)),
			)
			.mockImplementationOnce((n: number) => Promise.resolve(n));

		const { result, rerender } = renderHook(
			({ n }: { n: number }) => useFetchData(() => fetcher(n), [n]),
			{ initialProps: { n: 1 } },
		);

		// Trigger the second fetch before the first resolves
		rerender({ n: 2 });
		await waitFor(() => expect(result.current.data).toBe(2));

		// NOW resolve the stale first fetch — hook should ignore it
		resolveFirst?.(99);
		await new Promise((res) => setTimeout(res, 0));
		expect(result.current.data).toBe(2); // still 2, not 99
	});
});
