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
import Rules from "../src/pages/Rules";
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

const oneRule = {
	data: [
		{
			id: 1,
			name: "ACOS 过高预警",
			description: "监控 ACOS 超过 40%",
			condition_field: "acos",
			condition_operator: ">",
			condition_value: 0.4,
			condition_min_data: 7,
			period_days: 7,
			action_type: "alert",
			is_active: 1,
			last_run_at: "2026-04-18T08:00:00Z",
			created_at: "2026-04-01T00:00:00Z",
		},
	],
};

function installApi(response: { data: unknown[] }) {
	mockApiGet.mockImplementation((url: string) => {
		if (url === "/rules") {
			return Promise.resolve(response);
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

describe("Rules page — smoke", () => {
	it("fires /rules GET on mount", async () => {
		installApi({ data: [] });

		render(
			<MemoryRouter>
				<Rules />
			</MemoryRouter>,
		);

		await waitFor(() => {
			const urls = mockApiGet.mock.calls.map((c: unknown[]) => c[0]);
			expect(urls).toContain("/rules");
		});
	});

	it("renders the page title", async () => {
		installApi({ data: [] });

		render(
			<MemoryRouter>
				<Rules />
			</MemoryRouter>,
		);

		expect(await screen.findByText("自动化规则")).toBeInTheDocument();
	});

	it("renders the empty state when no rules exist", async () => {
		installApi({ data: [] });

		render(
			<MemoryRouter>
				<Rules />
			</MemoryRouter>,
		);

		// Empty-state copy from Rules.tsx:404
		expect(await screen.findByText("暂无自动化规则")).toBeInTheDocument();
	});

	it("renders the rule row when a rule exists", async () => {
		installApi(oneRule);

		render(
			<MemoryRouter>
				<Rules />
			</MemoryRouter>,
		);

		// Rule name and period_days column (rendered as `${n} 天` per Rules.tsx:234)
		expect(await screen.findByText("ACOS 过高预警")).toBeInTheDocument();
		expect(screen.getByText("7 天")).toBeInTheDocument();
	});
});
