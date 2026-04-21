import { Card, Col, Row } from "antd";
import echarts from "../utils/echartsCore";
import ReactECharts from "../utils/reactEcharts";
import { CHART_COLORS, withTheme } from "../utils/chartTheme";
import type { DashboardData } from "../types/api";

interface DashboardTrendSectionProps {
	data: DashboardData;
	isDark: boolean;
}

/**
 * Row with 每日趋势 (bar+line chart, 8-col) and 广告活动状态分布 (pie chart,
 * 4-col) on the Dashboard. Extracted from Dashboard.tsx (F4-γ).
 */
export default function DashboardTrendSection({
	data,
	isDark,
}: DashboardTrendSectionProps) {
	const trendOption = {
		tooltip: { trigger: "axis" as const },
		legend: { data: ["花费 ($)", "订单", "ROAS"] },
		xAxis: {
			type: "category" as const,
			data: data.daily_trend.map((d) => d.date),
		},
		yAxis: [
			{ type: "value" as const, name: "金额 / 数量" },
			{ type: "value" as const, name: "ROAS", position: "right" as const },
		],
		series: [
			{
				name: "花费 ($)",
				type: "bar",
				data: data.daily_trend.map((d) => d.spend),
				color: CHART_COLORS[0],
			},
			{
				name: "订单",
				type: "bar",
				data: data.daily_trend.map((d) => d.orders),
				color: CHART_COLORS[1],
			},
			{
				name: "ROAS",
				type: "line",
				yAxisIndex: 1,
				data: data.daily_trend.map((d) => d.roas),
				color: CHART_COLORS[2],
			},
		],
	};

	return (
		<Row gutter={16} style={{ marginBottom: 24 }}>
			<Col xs={24} lg={16}>
				<Card title="每日趋势" style={{ height: "100%" }}>
					<ReactECharts
						echarts={echarts}
						option={withTheme(trendOption, isDark)}
						style={{ height: 350 }}
					/>
				</Card>
			</Col>
			<Col xs={24} lg={8}>
				<Card title="广告活动状态分布" style={{ height: "100%" }}>
					<ReactECharts
						echarts={echarts}
						option={{
							tooltip: {
								trigger: "item",
								formatter: "{b}: {c} ({d}%)",
								backgroundColor: isDark ? "#222730" : "#FFFFFF",
								borderColor: isDark ? "#2A2F3A" : "#E5E7EB",
								textStyle: { color: isDark ? "#D1D5DB" : "#1F2937" },
							},
							legend: {
								orient: "horizontal",
								bottom: 0,
								textStyle: { color: isDark ? "#9CA3AF" : "#6B7280" },
							},
							series: [
								{
									type: "pie",
									radius: ["40%", "70%"],
									avoidLabelOverlap: false,
									itemStyle: {
										borderRadius: 6,
										borderColor: isDark ? "#1A1D24" : "#FFFFFF",
										borderWidth: 2,
									},
									label: {
										show: true,
										formatter: "{b}\n{c}",
										color: isDark ? "#D1D5DB" : "#374151",
									},
									data: Object.entries(data.status_counts).map(
										([name, value]) => ({
											name,
											value,
											itemStyle: {
												color:
													name === "Delivering" || name === "Enabled"
														? "#10B981"
														: name === "Paused"
															? "#EF4444"
															: "#6B7280",
											},
										}),
									),
								},
							],
						}}
						style={{ height: 350 }}
					/>
				</Card>
			</Col>
		</Row>
	);
}
