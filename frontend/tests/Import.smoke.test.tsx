import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import Import from "../src/pages/Import";

vi.mock("../src/api/client", () => ({
	default: { get: vi.fn(), post: vi.fn() },
}));

beforeEach(() => {
	localStorage.clear();
});

afterEach(() => {
	cleanup();
	localStorage.clear();
});

describe("Import page — smoke", () => {
	it("renders without crashing", () => {
		render(
			<MemoryRouter>
				<Import />
			</MemoryRouter>,
		);
		// Page title card from Import.tsx:315
		expect(screen.getByText("上传展示位置 CSV")).toBeInTheDocument();
	});

	it("renders all 3 upload sections (CSV / TXT log / inventory)", () => {
		render(
			<MemoryRouter>
				<Import />
			</MemoryRouter>,
		);

		expect(screen.getByText("上传展示位置 CSV")).toBeInTheDocument();
		expect(screen.getByText("上传操作日志 TXT")).toBeInTheDocument();
		expect(screen.getByText("上传库存健康报告 CSV")).toBeInTheDocument();
	});

	it("renders the Steps indicator for the CSV upload flow", () => {
		render(
			<MemoryRouter>
				<Import />
			</MemoryRouter>,
		);

		// Steps items from Import.tsx:321-326
		expect(screen.getByText("上传文件")).toBeInTheDocument();
		expect(screen.getByText("预览数据")).toBeInTheDocument();
		expect(screen.getByText("导入结果")).toBeInTheDocument();
	});
});
