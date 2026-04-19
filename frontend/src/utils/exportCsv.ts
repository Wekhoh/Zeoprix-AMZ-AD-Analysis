/**
 * CSV 导出工具
 * 将表格数据导出为 CSV 文件并触发浏览器下载
 */

interface ColumnDef {
	title: string;
	dataIndex: string;
	render?: (
		value: unknown,
		record: Record<string, unknown>,
	) => string | number | null | undefined;
}

// Characters that trigger formula interpretation in Excel / LibreOffice /
// Google Sheets. Mirrors backend/services/formatters.py:_FORMULA_TRIGGERS.
const FORMULA_TRIGGERS = new Set(["=", "+", "-", "@", "\t", "\r", "\x00"]);

/**
 * Guard against Excel/CSV formula injection. Strings whose first char is a
 * formula trigger get a leading single quote — spreadsheet apps strip it on
 * display but no longer parse the cell as a formula.
 *
 * Protects against malicious values (e.g. a campaign name starting with
 * `=cmd|'/c calc'!A1`) that can flow from Amazon seller central → CSV import
 * → exported CSV → user's Excel, executing code on open.
 */
export function safeCsvCell(value: unknown): string {
	if (value === null || value === undefined) return "";
	const str = String(value);
	if (str.length > 0 && FORMULA_TRIGGERS.has(str[0])) {
		return "'" + str;
	}
	return str;
}

export function exportToCsv<T extends object>(
	data: T[],
	columns: ColumnDef[],
	filename: string,
) {
	if (!data.length) return;

	// BOM for Excel to recognize UTF-8
	const BOM = "\uFEFF";

	// Header row — titles are developer-controlled but safe-cell them for
	// defense in depth (costs nothing, covers future reuse).
	const header = columns
		.map((col) => `"${safeCsvCell(col.title).replace(/"/g, '""')}"`)
		.join(",");

	// Data rows
	const rows = data.map((record) =>
		columns
			.map((col) => {
				const raw = (record as Record<string, unknown>)[col.dataIndex];
				const safe = safeCsvCell(raw);
				const escaped = safe.replace(/"/g, '""');
				return `"${escaped}"`;
			})
			.join(","),
	);

	const csv = BOM + [header, ...rows].join("\n");
	const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
	const url = URL.createObjectURL(blob);

	const link = document.createElement("a");
	link.href = url;
	link.download = `${filename}.csv`;
	link.click();

	URL.revokeObjectURL(url);
}
