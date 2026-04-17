import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { useColumnVisibility } from "../src/hooks/useColumnVisibility";

const KEY = "test_cols";
const ALL = ["a", "b", "c", "d"];

afterEach(() => {
	localStorage.clear();
});

describe("useColumnVisibility", () => {
	it("starts with empty hidden set when storage is empty", () => {
		const { result } = renderHook(() => useColumnVisibility(KEY, ALL));
		const [hidden] = result.current;
		expect(hidden.size).toBe(0);
	});

	it("toggleColumn hides and un-hides a key", () => {
		const { result } = renderHook(() => useColumnVisibility(KEY, ALL));
		const [, toggle] = result.current;

		act(() => toggle("b"));
		expect(result.current[0].has("b")).toBe(true);
		expect(result.current[0].size).toBe(1);

		act(() => toggle("b"));
		expect(result.current[0].has("b")).toBe(false);
		expect(result.current[0].size).toBe(0);
	});

	it("persists hidden keys to localStorage", () => {
		const { result } = renderHook(() => useColumnVisibility(KEY, ALL));
		const [, toggle] = result.current;

		act(() => {
			toggle("a");
			toggle("c");
		});

		const stored = JSON.parse(localStorage.getItem(KEY) ?? "[]");
		expect(stored.sort()).toEqual(["a", "c"]);
	});

	it("hydrates from localStorage on mount", () => {
		localStorage.setItem(KEY, JSON.stringify(["b", "d"]));
		const { result } = renderHook(() => useColumnVisibility(KEY, ALL));
		const [hidden] = result.current;

		expect(hidden.has("b")).toBe(true);
		expect(hidden.has("d")).toBe(true);
		expect(hidden.size).toBe(2);
	});

	it("filters stored keys that are no longer in allKeys (schema drift guard)", () => {
		// Stored contains "obsolete" which isn't in current allKeys
		localStorage.setItem(KEY, JSON.stringify(["a", "obsolete"]));
		const { result } = renderHook(() => useColumnVisibility(KEY, ALL));
		const [hidden] = result.current;

		expect(hidden.has("a")).toBe(true);
		expect(hidden.has("obsolete")).toBe(false);
		expect(hidden.size).toBe(1);
	});

	it("resetColumns clears everything and removes storage entry", () => {
		const { result } = renderHook(() => useColumnVisibility(KEY, ALL));
		const [, toggle, reset] = result.current;

		act(() => {
			toggle("a");
			toggle("b");
		});
		expect(result.current[0].size).toBe(2);

		act(() => reset());
		expect(result.current[0].size).toBe(0);
		expect(localStorage.getItem(KEY)).toBeNull();
	});

	it("is resilient to malformed JSON in storage", () => {
		localStorage.setItem(KEY, "{{not valid json");
		const { result } = renderHook(() => useColumnVisibility(KEY, ALL));
		const [hidden] = result.current;
		expect(hidden.size).toBe(0); // falls back to empty
	});

	it("is resilient to non-array JSON in storage", () => {
		localStorage.setItem(KEY, JSON.stringify({ bogus: true }));
		const { result } = renderHook(() => useColumnVisibility(KEY, ALL));
		const [hidden] = result.current;
		expect(hidden.size).toBe(0);
	});
});
