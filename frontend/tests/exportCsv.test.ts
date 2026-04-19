import { describe, expect, it } from "vitest";
import { safeCsvCell } from "../src/utils/exportCsv";

describe("safeCsvCell — formula injection guard", () => {
	it("returns empty string for null", () => {
		expect(safeCsvCell(null)).toBe("");
	});

	it("returns empty string for undefined", () => {
		expect(safeCsvCell(undefined)).toBe("");
	});

	it("passes through normal campaign names untouched", () => {
		expect(safeCsvCell("US-Summer-Sale")).toBe("US-Summer-Sale");
		expect(safeCsvCell("Campaign 2026")).toBe("Campaign 2026");
	});

	it("prefixes leading = (Excel formula)", () => {
		expect(safeCsvCell("=SUM(A1:A10)")).toBe("'=SUM(A1:A10)");
	});

	it("prefixes leading + (unary plus / formula)", () => {
		expect(safeCsvCell("+17")).toBe("'+17");
	});

	it("prefixes leading - (guards against -2+3 style formula)", () => {
		// The guard is conservative: ANY leading trigger gets prefixed, even
		// for numeric-looking strings. Callers that want typed negatives
		// should pass Numbers, not strings.
		expect(safeCsvCell("-123")).toBe("'-123");
	});

	it("prefixes leading @ (Lotus / old-style formula)", () => {
		expect(safeCsvCell("@alice")).toBe("'@alice");
	});

	it("prefixes leading tab character", () => {
		expect(safeCsvCell("\tEvil")).toBe("'\tEvil");
	});

	it("prefixes leading carriage return", () => {
		expect(safeCsvCell("\rEvil")).toBe("'\rEvil");
	});

	it("prefixes leading null byte", () => {
		expect(safeCsvCell("\x00Evil")).toBe("'\x00Evil");
	});

	it("blocks the classic =cmd attack payload", () => {
		const payload = "=cmd|' /c calc'!A1";
		expect(safeCsvCell(payload)).toBe("'" + payload);
	});

	it("only guards the FIRST character — embedded = is fine", () => {
		expect(safeCsvCell("Sales =Europe")).toBe("Sales =Europe");
	});

	it("coerces numbers to safe strings", () => {
		expect(safeCsvCell(42)).toBe("42");
		expect(safeCsvCell(0)).toBe("0");
		// Number -5 → String "-5" starts with "-" → guard fires. Acceptable
		// because '-5 still displays correctly; callers needing typed
		// negatives should format in their render() hook upstream.
		expect(safeCsvCell(-5)).toBe("'-5");
	});

	it("coerces booleans", () => {
		expect(safeCsvCell(true)).toBe("true");
		expect(safeCsvCell(false)).toBe("false");
	});

	it("empty string passes through", () => {
		expect(safeCsvCell("")).toBe("");
	});
});
