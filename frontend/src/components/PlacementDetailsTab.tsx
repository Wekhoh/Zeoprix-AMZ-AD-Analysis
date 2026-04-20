import { Table } from "antd";
import type { PlacementRecord } from "../types/api";

interface PlacementDetailsTabProps {
	data: PlacementRecord[];
}

const columns = [
	{ title: "日期", dataIndex: "date", key: "date", width: 110 },
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

/**
 * Placement-details tab body for CampaignDetail — per-day × per-placement
 * breakdown table. Extracted from CampaignDetail.tsx (F2-γ2).
 */
export default function PlacementDetailsTab({
	data,
}: PlacementDetailsTabProps) {
	return (
		<Table<PlacementRecord>
			columns={columns}
			dataSource={data}
			rowKey="id"
			size="small"
			scroll={{ x: 1200 }}
		/>
	);
}
