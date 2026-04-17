import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Table, Button, Flex } from "antd";
import { DownloadOutlined } from "@ant-design/icons";
import { exportToCsv } from "../utils/exportCsv";
import api from "../api/client";
import FilterToolbar from "../components/FilterToolbar";
import PageHelp from "../components/PageHelp";
import ColumnSettingsButton, {
	type ColumnDescriptor,
} from "../components/ColumnSettingsButton";
import { useColumnVisibility } from "../hooks/useColumnVisibility";
import PageSkeleton from "../components/PageSkeleton";
import { useFilterParams } from "../hooks/useFilterParams";
import type { PlacementRecord } from "../types/api";

interface PaginatedResponse<T> {
	data: T[];
	total: number;
	page: number;
	page_size: number;
}

const DEFAULT_PAGE_SIZE = 50;

const PLACEMENTS_COLUMN_DESCRIPTORS: ColumnDescriptor[] = [
	{ key: "date", label: "日期" },
	{ key: "campaign", label: "广告活动", required: true },
	{ key: "placement", label: "展示位置" },
	{ key: "imp", label: "曝光量" },
	{ key: "clk", label: "点击量" },
	{ key: "ctr", label: "CTR" },
	{ key: "spend", label: "花费" },
	{ key: "cpc", label: "CPC" },
	{ key: "ord", label: "订单" },
	{ key: "sales", label: "销售额" },
	{ key: "roas", label: "ROAS" },
	{ key: "acos", label: "ACOS" },
];
const PLACEMENTS_COLUMN_KEYS = PLACEMENTS_COLUMN_DESCRIPTORS.map((c) => c.key);

export default function Placements() {
	const [data, setData] = useState<PlacementRecord[]>([]);
	const [loading, setLoading] = useState(true);
	const [total, setTotal] = useState(0);
	const [currentPage, setCurrentPage] = useState(1);
	const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
	const { dateFrom, dateTo, campaignId, buildQueryString } = useFilterParams();
	const [hiddenCols, toggleCol, resetCols] = useColumnVisibility(
		"placements_hidden_cols",
		PLACEMENTS_COLUMN_KEYS,
	);

	const fetchData = useCallback(
		(page: number, size: number) => {
			setLoading(true);
			const qs = buildQueryString();
			const separator = qs ? "&" : "?";
			const paginationParams = `${qs ? "" : "?"}page=${page}&page_size=${size}`;
			const url = `/placements${qs}${separator}${paginationParams}`;
			api
				.get<PaginatedResponse<PlacementRecord>>(url)
				.then((res) => {
					setData(res.data.data);
					setTotal(res.data.total);
				})
				.finally(() => setLoading(false));
		},
		[buildQueryString],
	);

	useEffect(() => {
		// eslint-disable-next-line react-hooks/set-state-in-effect -- reset to page 1 + refetch on filter change; cannot be derived from props
		setCurrentPage(1);
		fetchData(1, pageSize);
	}, [dateFrom, dateTo, campaignId, fetchData, pageSize]);

	const columns = [
		{ title: "日期", dataIndex: "date", key: "date", width: 110 },
		{
			title: "广告活动",
			dataIndex: "campaign_name",
			key: "campaign",
			ellipsis: true,
			render: (text: string | null, record: PlacementRecord) => (
				<Link
					to={`/campaigns/${record.campaign_id}`}
					style={{ color: "#1677ff" }}
				>
					{text ?? "-"}
				</Link>
			),
		},
		{
			title: "展示位置",
			dataIndex: "placement_type",
			key: "placement",
			width: 130,
		},
		{ title: "曝光量", dataIndex: "impressions", key: "imp", width: 90 },
		{ title: "点击量", dataIndex: "clicks", key: "clk", width: 80 },
		{
			title: "CTR",
			dataIndex: "ctr",
			key: "ctr",
			width: 80,
			render: (v: number | null) => (v ? `${(v * 100).toFixed(2)}%` : "-"),
		},
		{
			title: "花费",
			dataIndex: "spend",
			key: "spend",
			width: 90,
			render: (v: number) => `$${v?.toFixed(2)}`,
		},
		{
			title: "CPC",
			dataIndex: "cpc",
			key: "cpc",
			width: 80,
			render: (v: number | null) => (v ? `$${v.toFixed(2)}` : "-"),
		},
		{ title: "订单", dataIndex: "orders", key: "ord", width: 70 },
		{
			title: "销售额",
			dataIndex: "sales",
			key: "sales",
			width: 90,
			render: (v: number) => `$${v?.toFixed(2)}`,
		},
		{
			title: "ROAS",
			dataIndex: "roas",
			key: "roas",
			width: 80,
			render: (v: number | null) => v?.toFixed(2) ?? "-",
		},
		{
			title: "ACOS",
			dataIndex: "acos",
			key: "acos",
			width: 80,
			render: (v: number | null) => (v ? `${(v * 100).toFixed(2)}%` : "-"),
		},
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
						columns={PLACEMENTS_COLUMN_DESCRIPTORS}
						hiddenKeys={hiddenCols}
						onToggle={toggleCol}
						onReset={resetCols}
					/>
					<PageHelp
						title="展示位置帮助"
						content="展示位置数据按日期降序排列。使用筛选器按日期范围和广告活动过滤。点击「导出 CSV」下载当前筛选结果。"
					/>
				</div>
				<Button
					icon={<DownloadOutlined />}
					onClick={() => exportToCsv(data, exportColumns, "展示位置数据")}
				>
					导出 CSV
				</Button>
			</Flex>
			<Table<PlacementRecord>
				columns={visibleColumns}
				dataSource={data}
				rowKey="id"
				size="small"
				loading={loading}
				scroll={{ x: 1200 }}
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
