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
import Analysis from "../src/pages/Analysis";
import api from "../src/api/client";

vi.mock("../src/api/client", () => ({
	default: { get: vi.fn() },
}));

// ECharts stub — jsdom lacks canvas.getContext. Analysis only mounts a
// chart after a user comparison, but stub for safety.
vi.mock("echarts-for-react/lib/core", () => ({
	default: () => null,
}));

const mockApiGet = api.get as unknown as Mock;

function installEmptyApi() {
	mockApiGet.mockImplementation(() => Promise.resolve({ data: [] }));
}

beforeEach(() => {
	localStorage.clear();
	mockApiGet.mockReset();
});

afterEach(() => {
	cleanup();
	localStorage.clear();
});

describe("Analysis page — smoke", () => {
	it("fires /campaigns GET on mount (for campaign dropdown options)", async () => {
		installEmptyApi();

		render(
			<MemoryRouter>
				<Analysis />
			</MemoryRouter>,
		);

		await waitFor(() => {
			const urls = mockApiGet.mock.calls.map((c: unknown[]) => c[0]);
			expect(urls).toContain("/campaigns");
		});
	});

	it("renders all 3 comparison-mode tab labels", async () => {
		installEmptyApi();

		render(
			<MemoryRouter>
				<Analysis />
			</MemoryRouter>,
		);

		// Tabs from Analysis.tsx:289 — 周期对比 / 活动对比 / 连续对比
		expect(await screen.findByText("周期对比")).toBeInTheDocument();
		expect(screen.getByText("活动对比")).toBeInTheDocument();
		expect(screen.getByText("连续对比")).toBeInTheDocument();
	});
});
