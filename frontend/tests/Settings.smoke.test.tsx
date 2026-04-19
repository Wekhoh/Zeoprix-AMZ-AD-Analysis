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
import Settings from "../src/pages/Settings";
import api from "../src/api/client";

vi.mock("../src/api/client", () => ({
	default: {
		get: vi.fn(),
		post: vi.fn(),
		put: vi.fn(),
		delete: vi.fn(),
	},
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

describe("Settings page — smoke", () => {
	it("fires the 6 mount fetches", async () => {
		installEmptyApi();

		render(
			<MemoryRouter>
				<Settings />
			</MemoryRouter>,
		);

		await waitFor(() => {
			const urls = mockApiGet.mock.calls.map((c: unknown[]) => c[0]);
			expect(urls).toEqual(
				expect.arrayContaining([
					"/settings/backups",
					"/settings/products",
					"/settings/organic-sales",
					"/benchmarks/categories",
					"/settings/import-history",
					"/settings/data-stats",
				]),
			);
		});
	});

	it("renders all 5 tab labels", async () => {
		installEmptyApi();

		render(
			<MemoryRouter>
				<Settings />
			</MemoryRouter>,
		);

		// Tab labels from Settings.tsx Tabs items (lines 454 / 484 / 570 / 667 / 737)
		expect(await screen.findByText("数据备份")).toBeInTheDocument();
		expect(screen.getByText("产品管理")).toBeInTheDocument();
		expect(screen.getByText("销售数据")).toBeInTheDocument();
		expect(screen.getByText("导入历史")).toBeInTheDocument();
		expect(screen.getByText("数据管理")).toBeInTheDocument();
	});
});
