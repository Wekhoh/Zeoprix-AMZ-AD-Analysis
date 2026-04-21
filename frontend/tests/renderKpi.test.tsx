import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { renderAcos } from "../src/utils/renderKpi";

afterEach(() => {
	cleanup();
});

describe("renderAcos", () => {
	it("returns dash for null", () => {
		expect(renderAcos(null)).toBe("-");
	});

	it("returns dash for undefined", () => {
		expect(renderAcos(undefined)).toBe("-");
	});

	it("renders red span for acos above 50%", () => {
		const { container } = render(<>{renderAcos(0.6)}</>);
		const span = container.querySelector("span");
		expect(span).not.toBeNull();
		expect(span!.textContent).toBe("60.00%");
		expect(span!.style.color).toBe("rgb(255, 77, 79)"); // #ff4d4f
	});

	it("renders green span for acos below 25%", () => {
		const { container } = render(<>{renderAcos(0.15)}</>);
		const span = container.querySelector("span");
		expect(span).not.toBeNull();
		expect(span!.textContent).toBe("15.00%");
		expect(span!.style.color).toBe("rgb(82, 196, 26)"); // #52c41a
	});

	it("renders neutral span for acos in the mid band (25%..50%)", () => {
		const { container } = render(<>{renderAcos(0.35)}</>);
		const span = container.querySelector("span");
		expect(span).not.toBeNull();
		expect(span!.textContent).toBe("35.00%");
		expect(span!.style.color).toBe("");
	});

	it("treats boundary 0.5 as neutral (strict >)", () => {
		const { container } = render(<>{renderAcos(0.5)}</>);
		const span = container.querySelector("span");
		expect(span!.style.color).toBe("");
	});

	it("treats boundary 0.25 as neutral (strict <)", () => {
		const { container } = render(<>{renderAcos(0.25)}</>);
		const span = container.querySelector("span");
		expect(span!.style.color).toBe("");
	});
});
