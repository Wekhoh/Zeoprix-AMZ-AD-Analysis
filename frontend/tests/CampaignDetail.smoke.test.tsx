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
import { MemoryRouter, Route, Routes } from "react-router-dom";
import CampaignDetail from "../src/pages/CampaignDetail";
import api from "../src/api/client";

vi.mock("../src/api/client", () => ({
	default: { get: vi.fn(), put: vi.fn(), post: vi.fn(), delete: vi.fn() },
}));

// ECharts stub — jsdom lacks canvas.getContext
vi.mock("echarts-for-react/lib/core", () => ({
	default: () => null,
}));

const mockApiGet = api.get as unknown as Mock;

const campaignDetail = {
	data: {
		id: 42,
		name: "US-Summer-Sale",
		ad_type: "SP",
		targeting_type: "manual",
		match_type: "exact",
		bidding_strategy: "Dynamic bidding (down only)",
		base_bid: 1.5,
		portfolio: "Default",
		status: "Delivering",
		status_updated_at: "2026-04-18T10:00:00Z",
		total_impressions: 50000,
		total_clicks: 1200,
		total_spend: 240.5,
		total_orders: 48,
		total_sales: 1920.0,
		ctr: 0.024,
		cpc: 0.2,
		roas: 7.98,
		acos: 0.125,
		first_date: "2026-03-01",
		last_date: "2026-04-18",
	},
};

function installApi() {
	mockApiGet.mockImplementation((url: string) => {
		if (/^\/campaigns\/\d+$/.test(url)) {
			return Promise.resolve(campaignDetail);
		}
		return Promise.resolve({ data: [] });
	});
}

function renderRoute() {
	return render(
		<MemoryRouter initialEntries={["/campaigns/42"]}>
			<Routes>
				<Route path="/campaigns/:id" element={<CampaignDetail />} />
			</Routes>
		</MemoryRouter>,
	);
}

beforeEach(() => {
	localStorage.clear();
	mockApiGet.mockReset();
});

afterEach(() => {
	cleanup();
	localStorage.clear();
});

describe("CampaignDetail page — smoke", () => {
	it("fires the 7 parallel mount fetches", async () => {
		installApi();
		renderRoute();

		await waitFor(() => {
			const urls = mockApiGet.mock.calls.map((c: unknown[]) => c[0]);
			expect(urls).toEqual(
				expect.arrayContaining([
					"/campaigns/42",
					expect.stringContaining("/summaries/by-date?campaign_id=42"),
					expect.stringContaining("/placements?campaign_id=42"),
					expect.stringContaining("/operation-logs?campaign_id=42"),
					expect.stringContaining("/notes?campaign_id=42"),
					"/campaigns/42/placement-summary",
					"/campaigns/42/ad-groups",
				]),
			);
		});
	});

	it("renders the campaign name in the header once loaded", async () => {
		installApi();
		renderRoute();

		expect(await screen.findByText("US-Summer-Sale")).toBeInTheDocument();
	});

	it("renders the 4 KPI card titles", async () => {
		installApi();
		renderRoute();

		expect(await screen.findByText("总花费")).toBeInTheDocument();
		expect(screen.getByText("总订单")).toBeInTheDocument();
		// ROAS / ACOS may appear multiple times (KPI card + header badges)
		expect(screen.getAllByText("ROAS").length).toBeGreaterThanOrEqual(1);
		expect(screen.getAllByText("ACOS").length).toBeGreaterThanOrEqual(1);
	});
});
