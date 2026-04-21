import { Card, Col, Row, Table } from "antd";
import { Link } from "react-router-dom";
import echarts from "../utils/echartsCore";
import ReactECharts from "../utils/reactEcharts";
import type { DashboardData, TopCampaign } from "../types/api";

interface DashboardFunnelAndTopProps {
	data: DashboardData;
	isDark: boolean;
}

const topColumns = [
	{
		title: "广告活动",
		dataIndex: "campaign_name",
		key: "name",
		ellipsis: true,
		render: (text: string, record: TopCampaign) => (
			<Link
				to={`/campaigns/${record.campaign_id}`}
				style={{ color: "#1677ff" }}
			>
				{text}
			</Link>
		),
	},
	{
		title: "花费 ($)",
		dataIndex: "spend",
		key: "spend",
		render: (v: number) => v?.toFixed(2),
	},
	{ title: "订单", dataIndex: "orders", key: "orders" },
	{
		title: "ROAS",
		dataIndex: "roas",
		key: "roas",
		render: (v: number | null) => v?.toFixed(2) ?? "-",
	},
];

/**
 * Row with 转化漏斗 (funnel chart, 8-col) + TOP 花费广告活动 (Table, 16-col).
 * Extracted from Dashboard.tsx (F4-δ).
 */
export default function DashboardFunnelAndTop({
	data,
	isDark,
}: DashboardFunnelAndTopProps) {
	const imp = data.kpi.impressions || 1;
	const clk = data.kpi.clicks || 0;
	const ord = data.kpi.orders || 0;
	const ctr = imp > 0 ? ((clk / imp) * 100).toFixed(2) : "0";
	const cvr = clk > 0 ? ((ord / clk) * 100).toFixed(2) : "0";
	// Use visual-friendly values: 100/30/15 as minimum widths so all layers are visible
	const visualData = [
		{ name: "曝光", value: 100 },
		{
			name: "点击",
			value: Math.max(30, Math.round((clk / imp) * 100)),
		},
		{
			name: "订单",
			value: Math.max(15, Math.round((ord / imp) * 100)),
		},
	];

	return (
		<Row gutter={16} style={{ marginBottom: 24 }}>
			<Col xs={24} lg={8}>
				<Card title="转化漏斗" style={{ height: "100%" }}>
					<ReactECharts
						echarts={echarts}
						option={{
							tooltip: {
								trigger: "item",
								formatter: (params: { name: string }) => {
									if (params.name === "曝光")
										return `曝光: ${imp.toLocaleString()}`;
									if (params.name === "点击")
										return `点击: ${clk.toLocaleString()} (CTR ${ctr}%)`;
									return `订单: ${ord.toLocaleString()} (CVR ${cvr}%)`;
								},
								backgroundColor: isDark ? "#222730" : "#FFFFFF",
								borderColor: isDark ? "#2A2F3A" : "#E5E7EB",
								textStyle: { color: isDark ? "#D1D5DB" : "#1F2937" },
							},
							series: [
								{
									type: "funnel",
									left: "10%",
									width: "80%",
									sort: "descending",
									gap: 8,
									minSize: "15%",
									label: {
										show: true,
										position: "inside",
										formatter: (params: { name: string }) => {
											if (params.name === "曝光")
												return `曝光\n${imp.toLocaleString()}`;
											if (params.name === "点击")
												return `点击\n${clk.toLocaleString()} (${ctr}%)`;
											return `订单\n${ord.toLocaleString()} (${cvr}%)`;
										},
										color: isDark ? "#FFFFFF" : "#1F2937",
										fontSize: 13,
										fontWeight: 600,
										lineHeight: 20,
									},
									data: visualData,
									itemStyle: { borderWidth: 0 },
									color: ["#3B82F6", "#F59E0B", "#10B981"],
								},
							],
						}}
						style={{ height: 280 }}
					/>
				</Card>
			</Col>
			<Col xs={24} lg={16}>
				<Card title="TOP 花费广告活动" style={{ height: "100%" }}>
					<Table<TopCampaign>
						columns={topColumns}
						dataSource={data.top_campaigns}
						rowKey="campaign_name"
						pagination={false}
						size="small"
					/>
				</Card>
			</Col>
		</Row>
	);
}
