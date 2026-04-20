import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Alert, Button, Card, Col, Row, Statistic, Table } from "antd";
import { CalculatorOutlined, AimOutlined } from "@ant-design/icons";
import ReactECharts from "echarts-for-react/lib/core";
import echarts from "../utils/echartsCore";
import api from "../api/client";
import FilterToolbar from "../components/FilterToolbar";
import EmptyState from "../components/EmptyState";
import PageHelp from "../components/PageHelp";
import OnboardingGuide from "../components/OnboardingGuide";
import { isOnboardingDismissed } from "../utils/onboarding";
import { useFetchData } from "../hooks/useFetchData";
import { useFilterParams } from "../hooks/useFilterParams";
import { useTheme } from "../hooks/useTheme";
import PageSkeleton from "../components/PageSkeleton";
import DashboardBenchmarkComparison from "../components/DashboardBenchmarkComparison";
import DashboardKpiGrid from "../components/DashboardKpiGrid";
import DashboardTrendSection from "../components/DashboardTrendSection";
import { calcWowDeltas } from "../utils/wowDeltas";
import type { DashboardAlert, DashboardData, TopCampaign } from "../types/api";

export default function Dashboard() {
	const [showOnboarding, setShowOnboarding] = useState(false);
	const { dateFrom, dateTo, marketplaceId, buildQueryString } =
		useFilterParams();
	const { isDark } = useTheme();
	const navigate = useNavigate();

	const { data, loading } = useFetchData<DashboardData>(
		() =>
			api
				.get<DashboardData>(`/summaries/dashboard${buildQueryString()}`)
				.then((r) => r.data),
		[dateFrom, dateTo, marketplaceId, buildQueryString],
	);

	const isEmpty =
		!data ||
		(data.kpi.spend === 0 &&
			data.kpi.orders === 0 &&
			data.kpi.impressions === 0 &&
			(data.top_campaigns?.length ?? 0) === 0);

	const wowDeltas = useMemo(
		() => (data ? calcWowDeltas(data.daily_trend) : null),
		[data],
	);

	// Show onboarding when no data and not dismissed (must be before any conditional return)
	useEffect(() => {
		if (!loading && isEmpty && !isOnboardingDismissed()) {
			// eslint-disable-next-line react-hooks/set-state-in-effect -- one-shot hint trigger; depends on async loading and localStorage check, cannot be derived
			setShowOnboarding(true);
		}
	}, [loading, isEmpty]);

	if (loading) return <PageSkeleton variant="dashboard" />;

	if (isEmpty) {
		return (
			<>
				<EmptyState
					title="暂无广告数据"
					description="请先到「数据导入」页面上传展示位置 CSV 文件"
					actionText="去导入数据"
					onAction={() => navigate("/import")}
				/>
				<OnboardingGuide
					open={showOnboarding}
					onClose={() => setShowOnboarding(false)}
				/>
			</>
		);
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

	return (
		<div>
			<div style={{ display: "flex", alignItems: "center", marginBottom: 16 }}>
				<FilterToolbar showCampaignFilter={false} />
				<PageHelp
					title="仪表盘帮助"
					content={
						<div>
							<p>仪表盘显示所有广告活动的汇总 KPI。</p>
							<p style={{ fontWeight: 600, marginTop: 12 }}>KPI 说明：</p>
							<ul style={{ paddingLeft: 20 }}>
								<li>ACOS = 花费 / 销售额（越低越好）</li>
								<li>ROAS = 销售额 / 花费（越高越好）</li>
								<li>TACoS = 广告花费 / 总销售额（含有机）</li>
							</ul>
							<p style={{ fontWeight: 600, marginTop: 12 }}>归因窗口：</p>
							<p>
								SP 广告 7 天，SB/SD 广告 14 天。数据会在归因窗口内回溯更新。
							</p>
							<p style={{ fontWeight: 600, marginTop: 12 }}>预算：</p>
							<p>
								亚马逊允许单日超支最多 100%，月度总花费受「日预算 x 天数」保护。
							</p>
						</div>
					}
				/>
			</div>

			{data.freshness && data.freshness.level !== "empty" && (
				<Alert
					type={
						data.freshness.level === "fresh"
							? "success"
							: data.freshness.level === "warning"
								? "warning"
								: data.freshness.level === "stale"
									? "error"
									: "info"
					}
					showIcon
					message={data.freshness.message}
					description={
						data.freshness.last_import_at
							? `最后导入: ${data.freshness.last_import_at.slice(0, 19)}${
									data.freshness.last_import_file
										? ` (${data.freshness.last_import_file})`
										: ""
								}`
							: undefined
					}
					action={
						data.freshness.level !== "fresh" && (
							<Link to="/import">
								<Button size="small" type="primary">
									去导入
								</Button>
							</Link>
						)
					}
					style={{ marginBottom: 16 }}
					closable
				/>
			)}

			{data.inventory_status?.has_data && data.inventory_status.message && (
				<Alert
					type={data.inventory_status.critical_count > 0 ? "error" : "warning"}
					showIcon
					message={data.inventory_status.message}
					description={
						data.inventory_status.last_import_date
							? `库存快照日期: ${data.inventory_status.last_import_date}`
							: undefined
					}
					action={
						<Link to="/import">
							<Button size="small" type="primary">
								更新库存
							</Button>
						</Link>
					}
					style={{ marginBottom: 16 }}
					closable
				/>
			)}

			{data.budget_pacing?.enabled && data.budget_pacing.message && (
				<Alert
					type={data.budget_pacing.level === "danger" ? "error" : "warning"}
					showIcon
					message={data.budget_pacing.message}
					description={`本月已花费 $${data.budget_pacing.current_spend?.toFixed(0)} / 预算 $${data.budget_pacing.monthly_budget?.toFixed(0)}（第 ${data.budget_pacing.days_elapsed} / ${data.budget_pacing.days_total} 天）`}
					style={{ marginBottom: 16 }}
					closable
				/>
			)}

			<DashboardKpiGrid data={data} wowDeltas={wowDeltas} />

			{data.profit?.has_cost_data && (
				<Row gutter={16} style={{ marginBottom: 24 }}>
					<Col xs={24} sm={12} lg={6}>
						<Card>
							<Statistic
								title="预估利润"
								value={data.profit.estimated_profit ?? 0}
								precision={2}
								prefix={<CalculatorOutlined />}
								suffix="USD"
								valueStyle={{
									color:
										(data.profit.estimated_profit ?? 0) >= 0
											? "#52c41a"
											: "#ff4d4f",
								}}
							/>
						</Card>
					</Col>
					<Col xs={24} sm={12} lg={6}>
						<Card>
							<Statistic
								title="盈亏平衡 ACOS"
								value={
									data.profit.break_even_acos != null
										? data.profit.break_even_acos * 100
										: 0
								}
								precision={1}
								prefix={<AimOutlined />}
								suffix="%"
							/>
						</Card>
					</Col>
				</Row>
			)}

			{data.alerts &&
				data.alerts.length > 0 &&
				(() => {
					const groups = {
						danger: data.alerts.filter(
							(a: DashboardAlert) => a.severity === "danger",
						),
						warning: data.alerts.filter(
							(a: DashboardAlert) => a.severity === "warning",
						),
						success: data.alerts.filter(
							(a: DashboardAlert) => a.severity === "success",
						),
					};
					const sections: {
						key: "danger" | "warning" | "success";
						title: string;
						color: string;
						items: DashboardAlert[];
					}[] = [
						{
							key: "danger" as const,
							title: "立即处理",
							color: "#ff4d4f",
							items: groups.danger,
						},
						{
							key: "warning" as const,
							title: "今天处理",
							color: "#faad14",
							items: groups.warning,
						},
						{
							key: "success" as const,
							title: "扩量机会",
							color: "#52c41a",
							items: groups.success,
						},
					].filter((s) => s.items.length > 0);

					const formatAlertMsg = (alert: DashboardAlert): string => {
						const metric =
							alert.type === "high_acos"
								? `ACOS ${(alert.value * 100).toFixed(1)}%`
								: alert.type === "high_roas"
									? `ROAS ${alert.value}`
									: alert.type === "inventory_risk"
										? `库存 ${alert.value} 天`
										: `花费 $${alert.value}`;
						return `${alert.campaign_name} · ${metric}`;
					};

					return (
						<Card
							title={`今日行动清单 (${data.alerts.length})`}
							size="small"
							style={{ marginBottom: 24 }}
							styles={{ body: { paddingBottom: 8 } }}
						>
							{sections.map((section) => (
								<div key={section.key} style={{ marginBottom: 12 }}>
									<div
										style={{
											fontSize: 13,
											fontWeight: 600,
											color: section.color,
											marginBottom: 6,
											borderLeft: `3px solid ${section.color}`,
											paddingLeft: 8,
										}}
									>
										{section.title} ({section.items.length})
									</div>
									<div style={{ paddingLeft: 11 }}>
										{section.items.slice(0, 5).map((alert, idx) => (
											<div
												key={`${alert.type}-${alert.campaign_name}-${idx}`}
												style={{
													fontSize: 12,
													color: isDark ? "#D1D5DB" : "#4B5563",
													padding: "2px 0",
													lineHeight: 1.6,
												}}
											>
												• {formatAlertMsg(alert)} — {alert.message}
											</div>
										))}
										{section.items.length > 5 && (
											<div
												style={{
													fontSize: 11,
													color: isDark ? "#9CA3AF" : "#6B7280",
													paddingTop: 4,
												}}
											>
												还有 {section.items.length - 5} 条
											</div>
										)}
									</div>
								</div>
							))}
						</Card>
					);
				})()}

			<DashboardTrendSection data={data} isDark={isDark} />

			<Row gutter={16} style={{ marginBottom: 24 }}>
				<Col xs={24} lg={8}>
					<Card title="转化漏斗" style={{ height: "100%" }}>
						{(() => {
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
							);
						})()}
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

			<DashboardBenchmarkComparison buildQueryString={buildQueryString} />
		</div>
	);
}
