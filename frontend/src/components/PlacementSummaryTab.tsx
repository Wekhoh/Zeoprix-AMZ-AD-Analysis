import { Table } from "antd";
import { fmtPct, fmtUsd } from "../utils/formatters";

export interface PlacementSummary {
	placement_type: string;
	impressions: number;
	clicks: number;
	spend: number;
	orders: number;
	sales: number;
	ctr: number | null;
	cpc: number | null;
	roas: number | null;
	acos: number | null;
}

interface PlacementSummaryTabProps {
	data: PlacementSummary[];
}

const columns = [
	{
		title: "展示位置",
		dataIndex: "placement_type",
		key: "type",
		width: 180,
	},
	{
		title: "曝光",
		dataIndex: "impressions",
		key: "imp",
		render: (v: number) => v.toLocaleString(),
	},
	{
		title: "点击",
		dataIndex: "clicks",
		key: "clk",
		render: (v: number) => v.toLocaleString(),
	},
	{
		title: "花费",
		dataIndex: "spend",
		key: "spend",
		render: (v: number) => fmtUsd(v),
	},
	{
		title: "订单",
		dataIndex: "orders",
		key: "ord",
	},
	{
		title: "ROAS",
		dataIndex: "roas",
		key: "roas",
		render: (v: number | null) => {
			if (v == null) return "-";
			return (
				<span
					style={{
						color: v >= 3 ? "#52c41a" : v < 1 ? "#ff4d4f" : undefined,
					}}
				>
					{v.toFixed(2)}
				</span>
			);
		},
	},
	{
		title: "ACOS",
		dataIndex: "acos",
		key: "acos",
		render: (v: number | null) => {
			if (v == null) return "-";
			return (
				<span
					style={{
						color: v > 0.5 ? "#ff4d4f" : v < 0.25 ? "#52c41a" : undefined,
					}}
				>
					{fmtPct(v, 2)}
				</span>
			);
		},
	},
	{
		title: "CTR",
		dataIndex: "ctr",
		key: "ctr",
		render: (v: number | null) => fmtPct(v, 2),
	},
	{
		title: "CPC",
		dataIndex: "cpc",
		key: "cpc",
		render: (v: number | null) => fmtUsd(v),
	},
];

/**
 * Placement-comparison tab body for CampaignDetail — aggregated placement
 * performance with threshold-colored ROAS/ACOS. Extracted from
 * CampaignDetail.tsx (F2-γ3).
 */
export default function PlacementSummaryTab({
	data,
}: PlacementSummaryTabProps) {
	return (
		<Table
			columns={columns}
			dataSource={data}
			rowKey="placement_type"
			size="middle"
			pagination={false}
		/>
	);
}
