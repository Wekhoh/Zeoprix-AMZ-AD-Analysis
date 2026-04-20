import { Table, Tag } from "antd";

export interface ImportHistoryItem {
	id: number;
	import_type: string;
	file_name: string | null;
	records_imported: number;
	records_updated: number;
	records_skipped: number;
	status: string;
	created_at: string;
}

interface SettingsImportHistoryTabProps {
	history: ImportHistoryItem[];
}

const IMPORT_TYPE_LABELS: Record<string, string> = {
	placement_csv: "展示位置 CSV",
	operation_log: "操作日志",
	search_term: "搜索词报告",
	migration: "数据迁移",
};

const IMPORT_STATUS_COLORS: Record<string, string> = {
	success: "green",
	partial: "orange",
	error: "red",
};

const columns = [
	{
		title: "时间",
		dataIndex: "created_at",
		key: "time",
		width: 180,
	},
	{
		title: "类型",
		dataIndex: "import_type",
		key: "type",
		width: 140,
		render: (v: string) => <Tag color="blue">{IMPORT_TYPE_LABELS[v] ?? v}</Tag>,
	},
	{
		title: "文件名",
		dataIndex: "file_name",
		key: "file",
		ellipsis: true,
		render: (v: string | null) => v ?? "-",
	},
	{
		title: "新增",
		dataIndex: "records_imported",
		key: "imported",
		width: 80,
	},
	{
		title: "更新",
		dataIndex: "records_updated",
		key: "updated",
		width: 80,
	},
	{
		title: "跳过",
		dataIndex: "records_skipped",
		key: "skipped",
		width: 80,
	},
	{
		title: "状态",
		dataIndex: "status",
		key: "status",
		width: 80,
		render: (v: string) => (
			<Tag color={IMPORT_STATUS_COLORS[v] ?? "default"}>
				{v === "success" ? "成功" : v === "error" ? "失败" : v}
			</Tag>
		),
	},
];

/**
 * 导入历史 tab — readonly list of past import runs.
 * Extracted from Settings.tsx (F3-α).
 */
export default function SettingsImportHistoryTab({
	history,
}: SettingsImportHistoryTabProps) {
	return (
		<Table
			columns={columns}
			dataSource={history}
			rowKey="id"
			size="small"
			pagination={{ pageSize: 20 }}
			locale={{ emptyText: "暂无导入记录" }}
		/>
	);
}
