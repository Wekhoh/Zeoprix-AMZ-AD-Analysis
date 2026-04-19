import { describe, expect, it } from "vitest";
import { calcWowDeltas } from "../src/utils/wowDeltas";
import type { DailyTrend } from "../src/types/api";

/**
 * Build a DailyTrend row with safe defaults; override only what a given
 * test needs. Keeps test setup declarative.
 */
function makeDay(
	date: string,
	overrides: Partial<DailyTrend> = {},
): DailyTrend {
	return {
		date,
		spend: 0,
		orders: 0,
		roas: null,
		impressions: 0,
		clicks: 0,
		sales: 0,
		ctr: null,
		cpc: null,
		acos: null,
		...overrides,
	};
}

describe("calcWowDeltas — input guards", () => {
	it("returns null for empty array", () => {
		expect(calcWowDeltas([])).toBeNull();
	});

	it("returns null for single-day trend", () => {
		expect(calcWowDeltas([makeDay("2026-01-01")])).toBeNull();
	});
});

describe("calcWowDeltas — day-over-day (2–13 days)", () => {
	it("computes DoD delta; leaves WoW null when < 14 days", () => {
		const trend = [
			makeDay("2026-01-01", { spend: 100, orders: 10 }),
			makeDay("2026-01-02", { spend: 120, orders: 12 }),
		];
		const r = calcWowDeltas(trend);
		expect(r).not.toBeNull();
		expect(r!.dod_spend).toBeCloseTo(20, 5); // (120-100)/100 * 100
		expect(r!.dod_orders).toBeCloseTo(20, 5);
		// WoW series null because < 14 days
		expect(r!.spend).toBeNull();
		expect(r!.orders).toBeNull();
		expect(r!.roas).toBeNull();
		expect(r!.acos).toBeNull();
	});

	it("DoD spend = -50% when spend halves", () => {
		const trend = [
			makeDay("2026-01-01", { spend: 200 }),
			makeDay("2026-01-02", { spend: 100 }),
		];
		expect(calcWowDeltas(trend)!.dod_spend).toBeCloseTo(-50, 5);
	});

	it("DoD is null when prev day has zero spend (no divide-by-zero)", () => {
		const trend = [
			makeDay("2026-01-01", { spend: 0 }),
			makeDay("2026-01-02", { spend: 100 }),
		];
		expect(calcWowDeltas(trend)!.dod_spend).toBeNull();
	});

	it("sorts unordered input by date before computing", () => {
		// Input reversed: day 2 first, day 1 second
		const trend = [
			makeDay("2026-01-02", { spend: 150 }),
			makeDay("2026-01-01", { spend: 100 }),
		];
		// Should still compute (last=day2 150 vs prev=day1 100) = +50%
		expect(calcWowDeltas(trend)!.dod_spend).toBeCloseTo(50, 5);
	});

	it("DoD ROAS computed from per-day spend + sales (not trend.roas)", () => {
		const trend = [
			makeDay("2026-01-01", { spend: 100, sales: 200 }), // ROAS 2.0
			makeDay("2026-01-02", { spend: 100, sales: 300 }), // ROAS 3.0
		];
		// (3.0 - 2.0) / 2.0 * 100 = +50%
		expect(calcWowDeltas(trend)!.dod_roas).toBeCloseTo(50, 5);
	});

	it("DoD ACOS computed from per-day spend + sales", () => {
		const trend = [
			makeDay("2026-01-01", { spend: 50, sales: 100 }), // ACOS 0.5
			makeDay("2026-01-02", { spend: 20, sales: 100 }), // ACOS 0.2
		];
		// (0.2 - 0.5) / 0.5 * 100 = -60%
		expect(calcWowDeltas(trend)!.dod_acos).toBeCloseTo(-60, 5);
	});
});

describe("calcWowDeltas — week-over-week (≥14 days)", () => {
	function makeRange(startDay: number, count: number, spend: number) {
		const days: DailyTrend[] = [];
		for (let i = 0; i < count; i++) {
			const d = String(startDay + i).padStart(2, "0");
			days.push(
				makeDay(`2026-01-${d}`, { spend, orders: 5, sales: spend * 2 }),
			);
		}
		return days;
	}

	it("computes both DoD and WoW when given 14 days", () => {
		// Days 01-07: prev week (spend 50/day, total 350)
		// Days 08-14: last week (spend 100/day, total 700)
		const trend = [...makeRange(1, 7, 50), ...makeRange(8, 7, 100)];
		const r = calcWowDeltas(trend);
		expect(r).not.toBeNull();
		// WoW spend: (700 - 350) / 350 * 100 = 100%
		expect(r!.spend).toBeCloseTo(100, 5);
		// DoD spend: last day (100) vs prev day (100) = 0
		expect(r!.dod_spend).toBeCloseTo(0, 5);
	});

	it("WoW is null when any previous-week metric is zero", () => {
		// Days 01-07 all zero spend → prev week total = 0 → null
		const trend = [...makeRange(1, 7, 0), ...makeRange(8, 7, 100)];
		const r = calcWowDeltas(trend);
		expect(r!.spend).toBeNull();
	});
});
