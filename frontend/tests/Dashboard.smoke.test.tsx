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
import Dashboard from "../src/pages/Dashboard";
import api from "../src/api/client";

vi.mock("../src/api/client", () => ({
	default: { get: vi.fn() },
}));

// ECharts can't render in jsdom (no canvas). Stub the wrapper — smoke
// tests assert Card titles + API wiring, not the chart internals.
vi.mock("echarts-for-react/lib/core", () => ({
	default: () => null,
}));

const mockApiGet = api.get as unknown as Mock;

const dashboardPayload = {
	data: {
		kpi: {
			impressions: 50000,
			clicks: 1200,
			spend: 240.5,
			orders: 48,
			sales: 1920.0,
			ctr: 0.024,
			cpc: 0.2,
			roas: 7.98,
			acos: 0.125,
		},
		daily_trend: [],
		top_campaigns: [],
		status_counts: { Delivering: 3, Paused: 1 },
		alerts: [],
		profit: { has_cost_data: false },
		tacos: { value: null, has_data: false },
	},
};

function installApi() {
	mockApiGet.mockImplementation((url: string) => {
		if (url.startsWith("/summaries/dashboard")) {
			return Promise.resolve(dashboardPayload);
		}
		// /settings/products returns empty → benchmark fetch short-circuits
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

describe("Dashboard page — smoke", () => {
	it("fires /summaries/dashboard GET on mount", async () => {
		installApi();

		render(
			<MemoryRouter>
				<Dashboard />
			</MemoryRouter>,
		);

		await waitFor(() => {
			const urls = mockApiGet.mock.calls.map((c: unknown[]) => c[0]);
			expect(
				urls.some(
					(u) => typeof u === "string" && u.startsWith("/summaries/dashboard"),
				),
			).toBe(true);
		});
	});

	it("also fires /settings/products for benchmark lookup", async () => {
		installApi();

		render(
			<MemoryRouter>
				<Dashboard />
			</MemoryRouter>,
		);

		await waitFor(() => {
			const urls = mockApiGet.mock.calls.map((c: unknown[]) => c[0]);
			expect(urls).toContain("/settings/products");
		});
	});

	it("renders the core KPI card titles once data loads", async () => {
		installApi();

		render(
			<MemoryRouter>
				<Dashboard />
			</MemoryRouter>,
		);

		// The 4 default KPI cards when TACoS is absent (Dashboard.tsx:94)
		expect(await screen.findByText("总花费")).toBeInTheDocument();
		expect(screen.getByText("总订单")).toBeInTheDocument();
		expect(screen.getByText("平均 ACOS")).toBeInTheDocument();
		expect(screen.getByText("平均 ROAS")).toBeInTheDocument();
	});

	it("renders the trend + status chart card titles", async () => {
		installApi();

		render(
			<MemoryRouter>
				<Dashboard />
			</MemoryRouter>,
		);

		// Card titles above the ECharts instances (Dashboard.tsx:633, 640)
		expect(await screen.findByText("每日趋势")).toBeInTheDocument();
		expect(screen.getByText("广告活动状态分布")).toBeInTheDocument();
	});
});
