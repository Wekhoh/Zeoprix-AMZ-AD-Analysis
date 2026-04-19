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
import OperationLogs from "../src/pages/OperationLogs";
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
				time: "10:30",
				campaign_name: "US-Summer-Sale",
				campaign_id: 42,
				change_type: "base_bid",
				from_value: "$1.50",
				to_value: "$1.75",
				level_type: "Campaign",
				operator: "Jack",
			},
		],
		total: 1,
		page: 1,
		page_size: 50,
	},
};

function installApi(mainResponse: object) {
	mockApiGet.mockImplementation((url: string) => {
		if (url.startsWith("/operation-logs")) {
			return Promise.resolve(mainResponse);
		}
		// Fall-through for embedded CampaignFilter's /campaigns fetch
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

describe("OperationLogs page — smoke", () => {
	it("fires paginated /operation-logs GET on mount", async () => {
		installApi(paginatedEmpty);

		render(
			<MemoryRouter>
				<OperationLogs />
			</MemoryRouter>,
		);

		await waitFor(() => {
			const urls = mockApiGet.mock.calls.map((c: unknown[]) => c[0]);
			expect(
				urls.some(
					(u) =>
						typeof u === "string" &&
						u.startsWith("/operation-logs") &&
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
				<OperationLogs />
			</MemoryRouter>,
		);

		expect(
			await screen.findByRole("button", { name: /导出 CSV/ }),
		).toBeInTheDocument();
	});

	it("renders a campaign name cell from the response", async () => {
		installApi(paginatedOne);

		render(
			<MemoryRouter>
				<OperationLogs />
			</MemoryRouter>,
		);

		expect(await screen.findByText("US-Summer-Sale")).toBeInTheDocument();
	});
});
