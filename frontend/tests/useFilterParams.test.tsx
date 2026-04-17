import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import type { ReactNode } from "react";
import { useFilterParams } from "../src/hooks/useFilterParams";

function wrapperWithUrl(search: string) {
	return function Wrapper({ children }: { children: ReactNode }) {
		return <MemoryRouter initialEntries={[search]}>{children}</MemoryRouter>;
	};
}

beforeEach(() => {
	localStorage.clear();
});

afterEach(() => {
	localStorage.clear();
});

describe("useFilterParams — read from URL", () => {
	it("parses date_from / date_to as dayjs objects", () => {
		const { result } = renderHook(() => useFilterParams(), {
			wrapper: wrapperWithUrl("/?date_from=2026-01-15&date_to=2026-01-31"),
		});
		expect(result.current.dateFrom?.format("YYYY-MM-DD")).toBe("2026-01-15");
		expect(result.current.dateTo?.format("YYYY-MM-DD")).toBe("2026-01-31");
	});

	it("returns null dates when params absent", () => {
		const { result } = renderHook(() => useFilterParams(), {
			wrapper: wrapperWithUrl("/"),
		});
		expect(result.current.dateFrom).toBeNull();
		expect(result.current.dateTo).toBeNull();
	});

	it("parses campaign_id as number", () => {
		const { result } = renderHook(() => useFilterParams(), {
			wrapper: wrapperWithUrl("/?campaign_id=42"),
		});
		expect(result.current.campaignId).toBe(42);
	});

	it("returns undefined campaign_id when absent", () => {
		const { result } = renderHook(() => useFilterParams(), {
			wrapper: wrapperWithUrl("/"),
		});
		expect(result.current.campaignId).toBeUndefined();
	});
});

describe("useFilterParams — marketplace_id with localStorage fallback", () => {
	it("URL wins over localStorage", () => {
		localStorage.setItem("amz_marketplace_id", "99");
		const { result } = renderHook(() => useFilterParams(), {
			wrapper: wrapperWithUrl("/?marketplace_id=7"),
		});
		expect(result.current.marketplaceId).toBe(7);
	});

	it("falls back to localStorage when URL has no marketplace_id", () => {
		localStorage.setItem("amz_marketplace_id", "99");
		const { result } = renderHook(() => useFilterParams(), {
			wrapper: wrapperWithUrl("/"),
		});
		expect(result.current.marketplaceId).toBe(99);
	});

	it("is undefined when neither URL nor storage has a value", () => {
		const { result } = renderHook(() => useFilterParams(), {
			wrapper: wrapperWithUrl("/"),
		});
		expect(result.current.marketplaceId).toBeUndefined();
	});
});

describe("useFilterParams — setDateRange", () => {
	it("setDateRange(null, null) clears existing dates", () => {
		const { result } = renderHook(() => useFilterParams(), {
			wrapper: wrapperWithUrl("/?date_from=2026-01-01&date_to=2026-01-31"),
		});
		expect(result.current.dateFrom).not.toBeNull();

		act(() => {
			result.current.setDateRange(null, null);
		});

		expect(result.current.dateFrom).toBeNull();
		expect(result.current.dateTo).toBeNull();
	});
});

describe("useFilterParams — setCampaignId / setMarketplaceId", () => {
	it("setCampaignId sets then clears", () => {
		const { result } = renderHook(() => useFilterParams(), {
			wrapper: wrapperWithUrl("/"),
		});

		act(() => result.current.setCampaignId(123));
		expect(result.current.campaignId).toBe(123);

		act(() => result.current.setCampaignId(undefined));
		expect(result.current.campaignId).toBeUndefined();
	});

	it("setMarketplaceId writes to URL, overrides storage", () => {
		localStorage.setItem("amz_marketplace_id", "1");
		const { result } = renderHook(() => useFilterParams(), {
			wrapper: wrapperWithUrl("/"),
		});
		expect(result.current.marketplaceId).toBe(1); // from storage

		act(() => result.current.setMarketplaceId(5));
		expect(result.current.marketplaceId).toBe(5); // URL now wins
	});
});

describe("useFilterParams — clearFilters", () => {
	it("removes all params including date, campaign, marketplace", () => {
		const { result } = renderHook(() => useFilterParams(), {
			wrapper: wrapperWithUrl(
				"/?date_from=2026-01-01&date_to=2026-01-31&campaign_id=9&marketplace_id=3",
			),
		});
		expect(result.current.dateFrom).not.toBeNull();
		expect(result.current.campaignId).toBe(9);

		act(() => result.current.clearFilters());

		expect(result.current.dateFrom).toBeNull();
		expect(result.current.dateTo).toBeNull();
		expect(result.current.campaignId).toBeUndefined();
	});
});

describe("useFilterParams — buildQueryString", () => {
	it("returns empty string when no filters set", () => {
		const { result } = renderHook(() => useFilterParams(), {
			wrapper: wrapperWithUrl("/"),
		});
		expect(result.current.buildQueryString()).toBe("");
	});

	it("reconstructs query string with all set params", () => {
		const { result } = renderHook(() => useFilterParams(), {
			wrapper: wrapperWithUrl(
				"/?date_from=2026-01-01&date_to=2026-01-31&campaign_id=42&marketplace_id=2",
			),
		});
		const qs = result.current.buildQueryString();
		expect(qs.startsWith("?")).toBe(true);
		expect(qs).toContain("date_from=2026-01-01");
		expect(qs).toContain("date_to=2026-01-31");
		expect(qs).toContain("campaign_id=42");
		expect(qs).toContain("marketplace_id=2");
	});

	it("omits params that are not set", () => {
		const { result } = renderHook(() => useFilterParams(), {
			wrapper: wrapperWithUrl("/?campaign_id=7"),
		});
		const qs = result.current.buildQueryString();
		expect(qs).toBe("?campaign_id=7");
	});
});
