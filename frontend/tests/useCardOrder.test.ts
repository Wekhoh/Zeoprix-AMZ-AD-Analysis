import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { useCardOrder } from "../src/hooks/useCardOrder";

const KEY = "test_card_order";
const DEFAULT = ["spend", "orders", "acos", "roas"];

afterEach(() => {
	localStorage.clear();
});

describe("useCardOrder", () => {
	it("returns defaultOrder when nothing is stored", () => {
		const { result } = renderHook(() => useCardOrder(KEY, DEFAULT));
		const [order] = result.current;
		expect(order).toEqual(DEFAULT);
	});

	it("persists a new order to localStorage", () => {
		const { result } = renderHook(() => useCardOrder(KEY, DEFAULT));
		const [, setOrder] = result.current;

		const newOrder = ["roas", "spend", "orders", "acos"];
		act(() => setOrder(newOrder));

		expect(result.current[0]).toEqual(newOrder);
		expect(JSON.parse(localStorage.getItem(KEY) ?? "[]")).toEqual(newOrder);
	});

	it("hydrates from localStorage on mount", () => {
		localStorage.setItem(
			KEY,
			JSON.stringify(["acos", "roas", "spend", "orders"]),
		);
		const { result } = renderHook(() => useCardOrder(KEY, DEFAULT));
		expect(result.current[0]).toEqual(["acos", "roas", "spend", "orders"]);
	});

	it("drops stored IDs no longer present in defaults (schema shrink)", () => {
		// Stored contains "tacos" which isn't in current defaults
		localStorage.setItem(
			KEY,
			JSON.stringify(["roas", "tacos", "spend", "orders", "acos"]),
		);
		const { result } = renderHook(() => useCardOrder(KEY, DEFAULT));
		// "tacos" removed; other stored order preserved; "tacos" no append of missing
		expect(result.current[0]).toEqual(["roas", "spend", "orders", "acos"]);
	});

	it("appends new default IDs at the end (schema grow)", () => {
		// Simulate pre-TACoS state saved → TACoS added later
		localStorage.setItem(
			KEY,
			JSON.stringify(["roas", "orders", "spend", "acos"]),
		);
		const grownDefaults = [...DEFAULT, "tacos"];
		const { result } = renderHook(() => useCardOrder(KEY, grownDefaults));

		// User's preferred order preserved for existing keys, new "tacos" appended
		expect(result.current[0]).toEqual([
			"roas",
			"orders",
			"spend",
			"acos",
			"tacos",
		]);
	});

	it("is resilient to malformed JSON in storage", () => {
		localStorage.setItem(KEY, "{{not valid");
		const { result } = renderHook(() => useCardOrder(KEY, DEFAULT));
		expect(result.current[0]).toEqual(DEFAULT);
	});

	it("is resilient to non-array JSON", () => {
		localStorage.setItem(KEY, JSON.stringify({ looks: "wrong" }));
		const { result } = renderHook(() => useCardOrder(KEY, DEFAULT));
		expect(result.current[0]).toEqual(DEFAULT);
	});

	it("filters non-string entries defensively", () => {
		localStorage.setItem(KEY, JSON.stringify([1, "spend", null, "orders"]));
		const { result } = renderHook(() => useCardOrder(KEY, DEFAULT));
		// Non-strings dropped; known strings kept + rest appended
		expect(result.current[0]).toContain("spend");
		expect(result.current[0]).toContain("orders");
		expect(result.current[0]).toContain("acos");
		expect(result.current[0]).toContain("roas");
		expect(result.current[0].length).toBe(4);
	});
});
