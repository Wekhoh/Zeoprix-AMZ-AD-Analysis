import { cleanup, render, screen, waitFor } from "@testing-library/react";
import {
	afterEach,
	beforeEach,
	describe,
	expect,
	it,
	vi,
	type Mock,
} from "vitest";
import { MemoryRouter } from "react-router-dom";
import Summaries from "../src/pages/Summaries";
import api from "../src/api/client";

vi.mock("../src/api/client", () => ({
	default: { get: vi.fn() },
}));

const mockApiGet = api.get as unknown as Mock;

/**
 * Default mock: return an empty result for any GET. Individual tests can
 * override via `mockImplementation`. Using implementation-based (not
 * `mockResolvedValueOnce`) because Summaries fires Promise.all of 3
 * requests and the CampaignFilter inside FilterToolbar fires a 4th.
 */
function installDefaultApi() {
	mockApiGet.mockImplementation(() => Promise.resolve({ data: [] }));
}

beforeEach(() => {
	localStorage.clear();
	mockApiGet.mockReset();
	installDefaultApi();
});

afterEach(() => {
	cleanup();
	localStorage.clear();
});

describe("Summaries page — smoke", () => {
	it("renders without crashing and shows all 3 tab labels", async () => {
		render(
			<MemoryRouter>
				<Summaries />
			</MemoryRouter>,
		);

		// Tabs render synchronously; data fetch can still be pending
		expect(screen.getByText("按日期")).toBeInTheDocument();
		expect(screen.getByText("按广告活动")).toBeInTheDocument();
		expect(screen.getByText("按展示位置")).toBeInTheDocument();
	});

	it("renders both export buttons", async () => {
		render(
			<MemoryRouter>
				<Summaries />
			</MemoryRouter>,
		);

		expect(
			screen.getByRole("button", { name: /Excel 报告/ }),
		).toBeInTheDocument();
		expect(
			screen.getByRole("button", { name: /PDF 报告/ }),
		).toBeInTheDocument();
	});

	it("fires the 3 summary endpoint requests on mount", async () => {
		render(
			<MemoryRouter>
				<Summaries />
			</MemoryRouter>,
		);

		await waitFor(() => {
			const urls = mockApiGet.mock.calls.map((c: unknown[]) => c[0]);
			expect(urls).toEqual(
				expect.arrayContaining([
					expect.stringContaining("/summaries/by-date"),
					expect.stringContaining("/summaries/by-campaign"),
					expect.stringContaining("/summaries/by-placement"),
				]),
			);
		});
	});

	it("renders a row when by-date returns data", async () => {
		mockApiGet.mockImplementation((url: string) => {
			if (url.startsWith("/summaries/by-date")) {
				return Promise.resolve({
					data: [
						{
							date: "2026-04-10",
							impressions: 1000,
							clicks: 50,
							spend: 12.5,
							orders: 3,
							sales: 45.0,
							roas: 3.6,
							acos: 0.278,
						},
					],
				});
			}
			return Promise.resolve({ data: [] });
		});

		render(
			<MemoryRouter>
				<Summaries />
			</MemoryRouter>,
		);

		// Wait for fetch to settle and the date row to render inside the
		// default-active "按日期" tab
		await waitFor(() => {
			expect(screen.getByText("2026-04-10")).toBeInTheDocument();
		});
	});
});
