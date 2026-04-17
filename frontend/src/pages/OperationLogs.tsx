import { useCallback, useEffect, useState } from "react";
import { Table, Button, Flex } from "antd";
import { DownloadOutlined } from "@ant-design/icons";
import { exportToCsv } from "../utils/exportCsv";
import api from "../api/client";
import FilterToolbar from "../components/FilterToolbar";
import PageSkeleton from "../components/PageSkeleton";
import ColumnSettingsButton, {
	type ColumnDescriptor,
} from "../components/ColumnSettingsButton";
import { useFilterParams } from "../hooks/useFilterParams";
import { useColumnVisibility } from "../hooks/useColumnVisibility";
import type { OperationLog } from "../types/api";

interface PaginatedResponse<T> {
	data: T[];
	total: number;
	page: number;
	page_size: number;
}

const DEFAULT_PAGE_SIZE = 50;

const OPLOG_COLUMN_DESCRIPTORS: ColumnDescriptor[] = [
	{ key: "date", label: "日期" },
	{ key: "time", label: "时间" },
	{ key: "campaign", label: "广告活动", required: true },
	{ key: "change", label: "变更类型" },
	{ key: "from", label: "修改前" },
	{ key: "to", label: "修改后" },
	{ key: "level", label: "层级" },
];
const OPLOG_COLUMN_KEYS = OPLOG_COLUMN_DESCRIPTORS.map((c) => c.key);

export default function OperationLogs() {
	const [data, setData] = useState<OperationLog[]>([]);
	const [loading, setLoading] = useState(true);
	const [total, setTotal] = useState(0);
	const [currentPage, setCurrentPage] = useState(1);
	const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
	const { dateFrom, dateTo, campaignId, buildQueryString } = useFilterParams();
	const [hiddenCols, toggleCol, resetCols] = useColumnVisibility(
		"operation_logs_hidden_cols",
		OPLOG_COLUMN_KEYS,
	);

	const fetchData = useCallback(
		(page: number, size: number) => {
			setLoading(true);
			const qs = buildQueryString();
			const separator = qs ? "&" : "?";
			const paginationParams = `${qs ? "" : "?"}page=${page}&page_size=${size}`;
			const url = `/operation-logs${qs}${separator}${paginationParams}`;
			api
				.get<PaginatedResponse<OperationLog>>(url)
				.then((res) => {
					setData(res.data.data);
					setTotal(res.data.total);
				})
				.finally(() => setLoading(false));
		},
		[buildQueryString],
	);

	useEffect(() => {
		setCurrentPage(1);
		fetchData(1, pageSize);
	}, [dateFrom, dateTo, campaignId, fetchData, pageSize]);

	const columns = [
		{ title: "日期", dataIndex: "date", key: "date", width: 110 },
		{ title: "时间", dataIndex: "time", key: "time", width: 70 },
		{
			title: "广告活动",
			dataIndex: "campaign_name",
			key: "campaign",
			ellipsis: true,
		},
		{ title: "变更类型", dataIndex: "change_type", key: "change", width: 200 },
		{ title: "修改前", dataIndex: "from_value", key: "from", width: 150 },
		{ title: "修改后", dataIndex: "to_value", key: "to", width: 150 },
		{ title: "层级", dataIndex: "level_type", key: "level", width: 90 },
	];

	const visibleColumns = columns.filter((c) => !hiddenCols.has(c.key));
	const exportColumns = visibleColumns.map((c) => ({
		title: c.title,
		dataIndex: c.dataIndex as string,
	}));

	if (loading && data.length === 0) return <PageSkeleton variant="table" />;

	return (
		<div>
			<Flex justify="space-between" align="center" style={{ marginBottom: 16 }}>
				<div style={{ display: "flex", alignItems: "center" }}>
					<FilterToolbar />
					<ColumnSettingsButton
						columns={OPLOG_COLUMN_DESCRIPTORS}
						hiddenKeys={hiddenCols}
						onToggle={toggleCol}
						onReset={resetCols}
					/>
				</div>
				<Button
					icon={<DownloadOutlined />}
					onClick={() => exportToCsv(data, exportColumns, "操作日志")}
				>
					导出 CSV
				</Button>
			</Flex>
			<Table<OperationLog>
				columns={visibleColumns}
				dataSource={data}
				rowKey="id"
				size="small"
				loading={loading}
				scroll={{ x: 1000 }}
				pagination={{
					current: currentPage,
					pageSize,
					total,
					showSizeChanger: true,
					showTotal: (t) => `共 ${t} 条`,
					pageSizeOptions: ["20", "50", "100"],
					onChange: (page, size) => {
						setCurrentPage(page);
						setPageSize(size);
						fetchData(page, size);
					},
				}}
			/>
		</div>
	);
}
