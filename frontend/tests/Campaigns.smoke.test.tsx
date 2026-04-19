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
import Campaigns from "../src/pages/Campaigns";
import api from "../src/api/client";

vi.mock("../src/api/client", () => ({
	default: { get: vi.fn(), put: vi.fn() },
}));

const mockApiGet = api.get as unknown as Mock;

const campaignRows = [
	{
		id: 1,
		name: "US-Summer-Sale",
		ad_type: "SP",
		targeting_type: "manual",
		match_type: "exact",
		bidding_strategy: "Dynamic bidding (down only)",
		base_bid: 1.5,
		portfolio: "Default",
		status: "Delivering",
		status_updated_at: "2026-04-18T10:00:00Z",
		spend: 150,
		orders: 12,
		sales: 480,
		acos: 0.3125,
		roas: 3.2,
		impressions: 5000,
		clicks: 180,
		daily_budget: 25,
		tags: ["seasonal"],
	},
	{
		id: 2,
		name: "DE-Launch",
		ad_type: "SB",
		targeting_type: "auto",
		match_type: null,
		bidding_strategy: "Fixed bids",
		base_bid: 2.0,
		portfolio: null,
		status: "Paused",
		status_updated_at: null,
		spend: 50,
		orders: 0,
		sales: 0,
		acos: null,
		roas: null,
		impressions: 1200,
		clicks: 40,
		daily_budget: null,
		tags: [],
	},
];

function installApi() {
	mockApiGet.mockImplementation((url: string) => {
		if (url.startsWith("/campaigns/tags/all")) {
			return Promise.resolve({ data: ["seasonal", "evergreen"] });
		}
		// The /campaigns list — Campaigns page AND FilterToolbar's CampaignFilter
		// both hit this; same payload works for both.
		if (url.startsWith("/campaigns")) {
			return Promise.resolve({ data: campaignRows });
		}
		return Promise.resolve({ data: [] });
	});
}

beforeEach(() => {
	localStorage.clear();
	mockApiGet.mockReset();
});

afterEach(() => {
	cleanup();
	localStorage.clear();
});

describe("Campaigns page — smoke", () => {
	it("fires /campaigns and /campaigns/tags/all on mount", async () => {
		installApi();

		render(
			<MemoryRouter>
				<Campaigns />
			</MemoryRouter>,
		);

		await waitFor(() => {
			const urls = mockApiGet.mock.calls.map((c: unknown[]) => c[0]);
			expect(
				urls.some(
					(u) => typeof u === "string" && u.startsWith("/campaigns/tags/all"),
				),
			).toBe(true);
			// The list endpoint starts with "/campaigns" but not "/campaigns/tags"
			expect(
				urls.some(
					(u) =>
						typeof u === "string" &&
						u.startsWith("/campaigns") &&
						!u.startsWith("/campaigns/tags"),
				),
			).toBe(true);
		});
	});

	it("renders ad-type filter tabs", async () => {
		installApi();

		render(
			<MemoryRouter>
				<Campaigns />
			</MemoryRouter>,
		);

		// Tabs in Campaigns.tsx:62 — all / SP / SB / SD / SBV.
		// "SP" and "SB" also appear as ad_type badges in rows, so
		// getAllByText is needed for those (at least tab instance exists).
		expect(await screen.findByText("全部")).toBeInTheDocument();
		expect(screen.getAllByText("SP").length).toBeGreaterThanOrEqual(1);
		expect(screen.getAllByText("SB").length).toBeGreaterThanOrEqual(1);
		// SD and SBV only exist as tabs in this test (no rows with those types)
		expect(screen.getByText("SD")).toBeInTheDocument();
		expect(screen.getByText("SBV")).toBeInTheDocument();
	});

	it("renders campaign rows with their names as links", async () => {
		installApi();

		render(
			<MemoryRouter>
				<Campaigns />
			</MemoryRouter>,
		);

		// Campaign name cells render as <Link to=/campaigns/:id>
		const row1 = await screen.findByRole("link", { name: "US-Summer-Sale" });
		expect(row1).toHaveAttribute("href", "/campaigns/1");

		const row2 = screen.getByRole("link", { name: "DE-Launch" });
		expect(row2).toHaveAttribute("href", "/campaigns/2");
	});

	it("renders an ad_type badge for each campaign row", async () => {
		installApi();

		render(
			<MemoryRouter>
				<Campaigns />
			</MemoryRouter>,
		);

		// Tag cell renders the ad_type. Multiple "SP" instances (tab + cell)
		// so assert at least two are present.
		await screen.findByRole("link", { name: "US-Summer-Sale" });
		const spBadges = screen.getAllByText("SP");
		expect(spBadges.length).toBeGreaterThanOrEqual(2); // tab + row badge
	});
});
