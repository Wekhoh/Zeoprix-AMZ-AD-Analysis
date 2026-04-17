import { describe, expect, it } from "vitest";
import { fmtNum, fmtPct, fmtUsd } from "../src/utils/formatters";

describe("fmtUsd", () => {
	it("formats positive numbers with two decimals", () => {
		expect(fmtUsd(1.994)).toBe("$1.99");
		expect(fmtUsd(1000)).toBe("$1000.00");
	});

	it("formats zero", () => {
		expect(fmtUsd(0)).toBe("$0.00");
	});

	it("returns dash for null/undefined", () => {
		expect(fmtUsd(null)).toBe("-");
		expect(fmtUsd(undefined)).toBe("-");
	});

	it("handles negative numbers", () => {
		expect(fmtUsd(-5.5)).toBe("$-5.50");
	});
});

describe("fmtPct", () => {
	it("defaults to 1 decimal place", () => {
		expect(fmtPct(0.42)).toBe("42.0%");
		expect(fmtPct(0.123)).toBe("12.3%");
	});

	it("accepts a custom digits argument", () => {
		expect(fmtPct(0.42, 2)).toBe("42.00%");
		expect(fmtPct(0.1234, 3)).toBe("12.340%");
		expect(fmtPct(0.42, 0)).toBe("42%");
	});

	it("returns dash for null/undefined", () => {
		expect(fmtPct(null)).toBe("-");
		expect(fmtPct(undefined)).toBe("-");
	});

	it("handles zero", () => {
		expect(fmtPct(0)).toBe("0.0%");
	});
});

describe("fmtNum", () => {
	it("uses locale grouping", () => {
		expect(fmtNum(1234)).toBe("1,234");
		expect(fmtNum(1000000)).toBe("1,000,000");
	});

	it("returns dash for null/undefined", () => {
		expect(fmtNum(null)).toBe("-");
		expect(fmtNum(undefined)).toBe("-");
	});

	it("handles zero", () => {
		expect(fmtNum(0)).toBe("0");
	});
});
