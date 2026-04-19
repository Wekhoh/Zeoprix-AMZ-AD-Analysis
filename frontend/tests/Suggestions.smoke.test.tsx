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
import Suggestions from "../src/pages/Suggestions";
import api from "../src/api/client";

vi.mock("../src/api/client", () => ({
	default: { get: vi.fn(), post: vi.fn() },
}));

const mockApiGet = api.get as unknown as Mock;

const twoSuggestions = {
	data: [
		{
			type: "acos_too_high",
			severity: "high",
			priority: 1,
			title: "ACOS 偏高告警",
			campaign_id: 42,
			campaign_name: "US-Summer-Sale",
			description: "过去 7 天 ACOS 55%，超出目标 30% 上限",
			action: "降低关键词出价 15%",
			metric: { acos: 0.55, target: 0.3 },
			hash: "abc123",
		},
		{
			type: "bid_too_low",
			severity: "opportunity",
			priority: 2,
			title: "出价机会",
			campaign_id: 99,
			campaign_name: "DE-Launch",
			description: "展示份额仅 12%，存在增长空间",
			action: "提高默认出价 20%",
			metric: { impression_share: 0.12 },
			hash: "def456",
		},
	],
};

function installApi(response: { data: unknown[] }) {
	mockApiGet.mockImplementation((url: string) => {
		if (url.startsWith("/analysis/suggestions")) {
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

describe("Suggestions page — smoke", () => {
	it("fires /analysis/suggestions GET on mount", async () => {
		installApi({ data: [] });

		render(
			<MemoryRouter>
				<Suggestions />
			</MemoryRouter>,
		);

		await waitFor(() => {
			const urls = mockApiGet.mock.calls.map((c: unknown[]) => c[0]);
			expect(
				urls.some(
					(u) => typeof u === "string" && u.startsWith("/analysis/suggestions"),
				),
			).toBe(true);
		});
	});

	it("shows empty state when no suggestions returned", async () => {
		installApi({ data: [] });

		render(
			<MemoryRouter>
				<Suggestions />
			</MemoryRouter>,
		);

		// Empty-state copy from the page (see Suggestions.tsx:245)
		expect(
			await screen.findByText(/当前日期范围内数据不足以生成建议/),
		).toBeInTheDocument();
	});

	it("renders both severity groups when suggestions are present", async () => {
		installApi(twoSuggestions);

		render(
			<MemoryRouter>
				<Suggestions />
			</MemoryRouter>,
		);

		// Severity group headers: "高 (1)" and "机会 (1)"
		expect(await screen.findByText(/高 \(1\)/)).toBeInTheDocument();
		expect(await screen.findByText(/机会 \(1\)/)).toBeInTheDocument();
	});

	it("renders the suggestion titles and at least one campaign name", async () => {
		installApi(twoSuggestions);

		render(
			<MemoryRouter>
				<Suggestions />
			</MemoryRouter>,
		);

		expect(await screen.findByText("ACOS 偏高告警")).toBeInTheDocument();
		expect(await screen.findByText("出价机会")).toBeInTheDocument();
		expect(screen.getByText("US-Summer-Sale")).toBeInTheDocument();
	});
});
