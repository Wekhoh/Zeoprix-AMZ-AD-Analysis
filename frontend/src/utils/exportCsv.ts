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

export function exportToCsv(
	data: Record<string, unknown>[],
	columns: ColumnDef[],
	filename: string,
) {
	if (!data.length) return;

	// BOM for Excel to recognize UTF-8
	const BOM = "\uFEFF";

	// Header row
	const header = columns.map((col) => `"${col.title}"`).join(",");

	// Data rows
	const rows = data.map((record) =>
		columns
			.map((col) => {
				const raw = record[col.dataIndex];
				// Format the value: use render if provided, otherwise raw value
				const value = raw ?? "";
				const str = String(value).replace(/"/g, '""');
				return `"${str}"`;
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
