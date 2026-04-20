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
import SearchTerms from "../src/pages/SearchTerms";
import api from "../src/api/client";

vi.mock("../src/api/client", () => ({
	default: { get: vi.fn(), post: vi.fn() },
}));

const mockApiGet = api.get as unknown as Mock;

const emptyBuckets = {
	data: {
		winners: [],
		potential: [],
		money_pits: [],
		low_data: [],
		stats: {
			total: 0,
			winners_count: 0,
			potential_count: 0,
			money_pits_count: 0,
			low_data_count: 0,
		},
	},
};

const oneWinner = {
	data: {
		winners: [
			{
				search_term: "memory foam mattress",
				campaign_id: 42,
				campaign_name: "US-Summer-Sale",
				impressions: 500,
				clicks: 30,
				ctr: 0.06,
				spend: 6.0,
				cpc: 0.2,
				orders: 5,
				sales: 100.0,
				roas: 16.67,
				acos: 0.06,
				cvr: 0.167,
				bucket: "winners",
				action: "harvest",
				suggested_bid: 0.5,
				whitelisted: false,
			},
		],
		potential: [],
		money_pits: [],
		low_data: [],
		stats: {
			total: 1,
			winners_count: 1,
			potential_count: 0,
			money_pits_count: 0,
			low_data_count: 0,
		},
	},
};

function installApi(bucketsResponse: object) {
	mockApiGet.mockImplementation((url: string) => {
		if (url.startsWith("/search-terms/buckets")) {
			return Promise.resolve(bucketsResponse);
		}
		// Fall-through for embedded CampaignFilter /campaigns
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

describe("SearchTerms page — smoke", () => {
	it("fires /search-terms/buckets on mount", async () => {
		installApi(emptyBuckets);

		render(
			<MemoryRouter>
				<SearchTerms />
			</MemoryRouter>,
		);

		await waitFor(() => {
			const urls = mockApiGet.mock.calls.map((c: unknown[]) => c[0]);
			expect(
				urls.some(
					(u) => typeof u === "string" && u.startsWith("/search-terms/buckets"),
				),
			).toBe(true);
		});
	});

	it("shows empty state when no search term data exists", async () => {
		installApi(emptyBuckets);

		render(
			<MemoryRouter>
				<SearchTerms />
			</MemoryRouter>,
		);

		// Empty-state copy from SearchTerms.tsx:668
		expect(await screen.findByText("暂无搜索词数据")).toBeInTheDocument();
	});

	it("always renders the upload card title", async () => {
		installApi(emptyBuckets);

		render(
			<MemoryRouter>
				<SearchTerms />
			</MemoryRouter>,
		);

		expect(await screen.findByText("上传搜索词报告")).toBeInTheDocument();
	});

	it("renders all 4 bucket tab labels when data is present", async () => {
		installApi(oneWinner);

		render(
			<MemoryRouter>
				<SearchTerms />
			</MemoryRouter>,
		);

		// Tab labels include dynamic counts. Regex matches "Winners (1)" etc.
		expect(await screen.findByText(/Winners \(1\)/)).toBeInTheDocument();
		expect(screen.getByText(/Potential \(0\)/)).toBeInTheDocument();
		expect(screen.getByText(/Money Pits \(0\)/)).toBeInTheDocument();
		expect(screen.getByText(/Low Data \(0\)/)).toBeInTheDocument();
	});
});
