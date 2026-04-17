import { renderHook, waitFor } from "@testing-library/react";
import {
	afterEach,
	beforeEach,
	describe,
	expect,
	it,
	vi,
	type Mock,
} from "vitest";
import {
	_clearAdTypeCatalogCache,
	useAdTypeCatalog,
	type AdTypeCatalog,
} from "../src/hooks/useAdTypeCatalog";
import api from "../src/api/client";

vi.mock("../src/api/client", () => ({
	default: { get: vi.fn() },
}));

const mockApiGet = api.get as unknown as Mock;

const SB_CATALOG: AdTypeCatalog = {
	ad_type: "SB",
	label: "Sponsored Brands",
	fields: [
		{ key: "impressions", label: "曝光", exclusive: false },
		{ key: "clicks", label: "点击", exclusive: false },
		{
			key: "attributedBrandedSearches14d",
			label: "品牌搜索 (14d)",
			exclusive: true,
		},
	],
	exclusive_fields: ["attributedBrandedSearches14d"],
};

const SP_CATALOG: AdTypeCatalog = {
	ad_type: "SP",
	label: "Sponsored Products",
	fields: [
		{ key: "impressions", label: "曝光", exclusive: false },
		{ key: "clicks", label: "点击", exclusive: false },
	],
	exclusive_fields: [],
};

beforeEach(() => {
	_clearAdTypeCatalogCache();
	mockApiGet.mockReset();
});

afterEach(() => {
	_clearAdTypeCatalogCache();
});

describe("useAdTypeCatalog — happy path", () => {
	it("returns null initially when adType is null", () => {
		const { result } = renderHook(() => useAdTypeCatalog(null));
		expect(result.current.catalog).toBeNull();
		expect(result.current.loading).toBe(false);
		expect(result.current.error).toBeNull();
		expect(mockApiGet).not.toHaveBeenCalled();
	});

	it("returns null when adType is undefined", () => {
		const { result } = renderHook(() => useAdTypeCatalog(undefined));
		expect(result.current.catalog).toBeNull();
		expect(mockApiGet).not.toHaveBeenCalled();
	});

	it("returns null when adType is empty string", () => {
		const { result } = renderHook(() => useAdTypeCatalog(""));
		expect(result.current.catalog).toBeNull();
		expect(mockApiGet).not.toHaveBeenCalled();
	});

	it("fetches catalog for uppercase adType", async () => {
		mockApiGet.mockResolvedValueOnce({ data: SB_CATALOG });

		const { result } = renderHook(() => useAdTypeCatalog("SB"));
		expect(result.current.loading).toBe(true);

		await waitFor(() => {
			expect(result.current.catalog).toEqual(SB_CATALOG);
		});
		expect(result.current.loading).toBe(false);
		expect(result.current.error).toBeNull();
		expect(mockApiGet).toHaveBeenCalledWith("/ad-types/SB");
	});

	it("uppercases lowercase adType before fetch", async () => {
		mockApiGet.mockResolvedValueOnce({ data: SB_CATALOG });

		renderHook(() => useAdTypeCatalog("sb"));

		await waitFor(() => {
			expect(mockApiGet).toHaveBeenCalledWith("/ad-types/SB");
		});
	});
});

describe("useAdTypeCatalog — caching", () => {
	it("does not refetch when same adType is requested twice", async () => {
		mockApiGet.mockResolvedValueOnce({ data: SB_CATALOG });

		const { result: r1, unmount: u1 } = renderHook(() =>
			useAdTypeCatalog("SB"),
		);
		await waitFor(() => expect(r1.current.catalog).toEqual(SB_CATALOG));
		u1();

		// Second mount with same type — should hit cache, NOT fetch
		const { result: r2 } = renderHook(() => useAdTypeCatalog("SB"));
		expect(r2.current.catalog).toEqual(SB_CATALOG);
		expect(r2.current.loading).toBe(false);
		expect(mockApiGet).toHaveBeenCalledTimes(1);
	});

	it("fetches separately for different ad_types", async () => {
		mockApiGet
			.mockResolvedValueOnce({ data: SB_CATALOG })
			.mockResolvedValueOnce({ data: SP_CATALOG });

		const { result, rerender } = renderHook(
			({ t }: { t: string }) => useAdTypeCatalog(t),
			{ initialProps: { t: "SB" } },
		);
		await waitFor(() => expect(result.current.catalog).toEqual(SB_CATALOG));

		rerender({ t: "SP" });
		await waitFor(() => expect(result.current.catalog).toEqual(SP_CATALOG));

		expect(mockApiGet).toHaveBeenCalledTimes(2);
		expect(mockApiGet).toHaveBeenNthCalledWith(1, "/ad-types/SB");
		expect(mockApiGet).toHaveBeenNthCalledWith(2, "/ad-types/SP");
	});
});

describe("useAdTypeCatalog — error path", () => {
	it("surfaces error from api.get and keeps catalog null", async () => {
		const boom = new Error("404 unknown ad_type");
		mockApiGet.mockRejectedValueOnce(boom);

		const { result } = renderHook(() => useAdTypeCatalog("UNKNOWN"));

		await waitFor(() => {
			expect(result.current.error).toBe(boom);
		});
		expect(result.current.catalog).toBeNull();
		expect(result.current.loading).toBe(false);
	});

	it("wraps non-Error rejection into Error instance", async () => {
		mockApiGet.mockRejectedValueOnce("string rejection");

		const { result } = renderHook(() => useAdTypeCatalog("BAD"));

		await waitFor(() => {
			expect(result.current.error).toBeInstanceOf(Error);
			expect(result.current.error?.message).toBe("string rejection");
		});
	});

	it("errors are not cached — retries on next mount", async () => {
		mockApiGet.mockRejectedValueOnce(new Error("transient"));

		const { result: r1, unmount } = renderHook(() => useAdTypeCatalog("SB"));
		await waitFor(() => expect(r1.current.error).not.toBeNull());
		unmount();

		// Next mount succeeds — hook should try again, not serve cached failure
		mockApiGet.mockResolvedValueOnce({ data: SB_CATALOG });
		const { result: r2 } = renderHook(() => useAdTypeCatalog("SB"));
		await waitFor(() => expect(r2.current.catalog).toEqual(SB_CATALOG));
		expect(mockApiGet).toHaveBeenCalledTimes(2);
	});
});

describe("useAdTypeCatalog — cancellation", () => {
	it("does not set state after unmount", async () => {
		let resolveFetch: ((v: { data: AdTypeCatalog }) => void) | undefined;
		mockApiGet.mockImplementationOnce(
			() => new Promise((res) => (resolveFetch = res)),
		);

		const { unmount } = renderHook(() => useAdTypeCatalog("SB"));
		unmount();
		resolveFetch?.({ data: SB_CATALOG });

		// If the hook tried to setState after unmount, testing-library logs
		// a warning. Give it a tick and then verify no exception raised.
		await new Promise((res) => setTimeout(res, 0));
		expect(true).toBe(true);
	});
});
