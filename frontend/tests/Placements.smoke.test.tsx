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
import Placements from "../src/pages/Placements";
import api from "../src/api/client";

vi.mock("../src/api/client", () => ({
	default: { get: vi.fn() },
}));

const mockApiGet = api.get as unknown as Mock;

const paginatedEmpty = {
	data: { data: [], total: 0, page: 1, page_size: 50 },
};

const paginatedOne = {
	data: {
		data: [
			{
				id: 1,
				date: "2026-04-18",
				campaign_name: "US-Summer-Sale",
				campaign_id: 42,
				placement_type: "搜索顶部",
				impressions: 1000,
				clicks: 50,
				ctr: 0.05,
				spend: 12.5,
				cpc: 0.25,
				orders: 3,
				sales: 45.0,
				roas: 3.6,
				acos: 0.278,
			},
		],
		total: 1,
		page: 1,
		page_size: 50,
	},
};

function installApi(mainResponse: object) {
	mockApiGet.mockImplementation((url: string) => {
		if (url.startsWith("/placements")) {
			return Promise.resolve(mainResponse);
		}
		// Fall-through for CampaignFilter's /campaigns fetch
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

describe("Placements page — smoke", () => {
	it("fires paginated /placements GET on mount", async () => {
		installApi(paginatedEmpty);

		render(
			<MemoryRouter>
				<Placements />
			</MemoryRouter>,
		);

		await waitFor(() => {
			const urls = mockApiGet.mock.calls.map((c: unknown[]) => c[0]);
			expect(
				urls.some(
					(u) =>
						typeof u === "string" &&
						u.startsWith("/placements") &&
						u.includes("page=1") &&
						u.includes("page_size=50"),
				),
			).toBe(true);
		});
	});

	it("renders the export button once data loads", async () => {
		installApi(paginatedOne);

		render(
			<MemoryRouter>
				<Placements />
			</MemoryRouter>,
		);

		expect(
			await screen.findByRole("button", { name: /导出 CSV/ }),
		).toBeInTheDocument();
	});

	it("renders the campaign name as a clickable link to the detail page", async () => {
		installApi(paginatedOne);

		render(
			<MemoryRouter>
				<Placements />
			</MemoryRouter>,
		);

		const link = await screen.findByRole("link", { name: "US-Summer-Sale" });
		expect(link).toHaveAttribute("href", "/campaigns/42");
	});

	it("renders placement_type in the table", async () => {
		installApi(paginatedOne);

		render(
			<MemoryRouter>
				<Placements />
			</MemoryRouter>,
		);

		expect(await screen.findByText("搜索顶部")).toBeInTheDocument();
	});
});
