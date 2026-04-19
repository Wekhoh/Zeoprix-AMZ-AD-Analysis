import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
	Alert,
	Button,
	Card,
	Col,
	Progress,
	Row,
	Statistic,
	Table,
	Tooltip,
} from "antd";
import {
	DollarOutlined,
	ShoppingCartOutlined,
	PercentageOutlined,
	RiseOutlined,
	CalculatorOutlined,
	AimOutlined,
	PieChartOutlined,
} from "@ant-design/icons";
import ReactECharts from "echarts-for-react/lib/core";
import { DragDropProvider } from "@dnd-kit/react";
import { useSortable } from "@dnd-kit/react/sortable";
import { move } from "@dnd-kit/helpers";
import echarts from "../utils/echartsCore";
import { withTheme, CHART_COLORS } from "../utils/chartTheme";
import api from "../api/client";
import FilterToolbar from "../components/FilterToolbar";
import EmptyState from "../components/EmptyState";
import PageHelp from "../components/PageHelp";
import OnboardingGuide from "../components/OnboardingGuide";
import { isOnboardingDismissed } from "../utils/onboarding";
import { useFilterParams } from "../hooks/useFilterParams";
import { useTheme } from "../hooks/useTheme";
import { useCardOrder } from "../hooks/useCardOrder";
import PageSkeleton from "../components/PageSkeleton";
import Sparkline from "../components/Sparkline";
import { calcWowDeltas, WowIndicator } from "../utils/wowDeltas";

function SortableKpiCard({
	id,
	index,
	children,
}: {
	id: string;
	index: number;
	children: ReactNode;
}) {
	const { ref, isDragging } = useSortable({ id, index });
	return (
		<div
			ref={ref}
			style={{
				opacity: isDragging ? 0.4 : 1,
				cursor: "grab",
				touchAction: "none",
				height: "100%",
			}}
		>
			{children}
		</div>
	);
}
import type {
	DashboardAlert,
	DashboardData,
	TopCampaign,
	BenchmarkResult,
} from "../types/api";

export default function Dashboard() {
	const [data, setData] = useState<DashboardData | null>(null);
	const [benchmarkData, setBenchmarkData] = useState<BenchmarkResult | null>(
		null,
	);
	const [loading, setLoading] = useState(true);
	const [showOnboarding, setShowOnboarding] = useState(false);
	const { dateFrom, dateTo, marketplaceId, buildQueryString } =
		useFilterParams();
	const { isDark } = useTheme();
	const navigate = useNavigate();

	// B6 (a): persistent KPI card order. TACoS only appears when cost data exists,
	// so the default list depends on `data` — useCardOrder reconciles stored order
	// against this list on every change (adds new cards, drops removed ones).
	const hasTacos = data?.tacos?.has_data ?? false;
	const defaultKpiOrder = useMemo<string[]>(
		() =>
			hasTacos
				? ["spend", "orders", "acos", "roas", "tacos"]
				: ["spend", "orders", "acos", "roas"],
		[hasTacos],
	);
	const [kpiOrder, setKpiOrder] = useCardOrder(
		"dashboard_kpi_order",
		defaultKpiOrder,
	);

	useEffect(() => {
		// eslint-disable-next-line react-hooks/set-state-in-effect -- loading indicator for async fetch
		setLoading(true);
		api
			.get<DashboardData>(`/summaries/dashboard${buildQueryString()}`)
			.then((res) => {
				setData(res.data);
			})
			.finally(() => setLoading(false));
	}, [dateFrom, dateTo, marketplaceId, buildQueryString]);

	// Fetch benchmark comparison if product has category_key
	useEffect(() => {
		api
			.get<{ id: number; category_key: string | null }[]>("/settings/products")
			.then((res) => {
				const products = res.data;
				const withCategory = products.find(
					(p: { category_key: string | null }) => p.category_key,
				);
				if (withCategory?.category_key) {
					const qs = buildQueryString();
					const sep = qs ? "&" : "?";
					api
						.get<BenchmarkResult>(
							`/benchmarks/compare${qs}${sep}category=${withCategory.category_key}`,
						)
						.then((r) => setBenchmarkData(r.data))
						.catch(() => setBenchmarkData(null));
				} else {
					setBenchmarkData(null);
				}
			});
	}, [buildQueryString]);

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

			<DragDropProvider
				onDragEnd={(event) => {
					if (!event.canceled) {
						setKpiOrder(move(kpiOrder, event));
					}
				}}
			>
				<Row gutter={16} style={{ marginBottom: 24 }}>
					{kpiOrder.map((id, index) => {
						let span: number;
						let content: ReactNode;
						switch (id) {
							case "spend":
								span = hasTacos ? 4 : 6;
								content = (
									<Card>
										<Statistic
											title={
												<Tooltip title="选定时间范围内的广告总花费">
													总花费
												</Tooltip>
											}
											value={data.kpi.spend}
											precision={2}
											prefix={<DollarOutlined />}
											suffix="USD"
										/>
										<Sparkline data={data.daily_trend.map((d) => d.spend)} />
										{wowDeltas && (
											<WowIndicator
												delta={wowDeltas.spend}
												dodDelta={wowDeltas.dod_spend}
											/>
										)}
									</Card>
								);
								break;
							case "orders":
								span = hasTacos ? 4 : 6;
								content = (
									<Card>
										<Statistic
											title={
												<Tooltip title="广告带来的总订单数（SP 7天/SB 14天归因窗口）">
													总订单
												</Tooltip>
											}
											value={data.kpi.orders}
											prefix={<ShoppingCartOutlined />}
										/>
										<Sparkline data={data.daily_trend.map((d) => d.orders)} />
										{wowDeltas && (
											<WowIndicator
												delta={wowDeltas.orders}
												dodDelta={wowDeltas.dod_orders}
											/>
										)}
									</Card>
								);
								break;
							case "acos":
								span = hasTacos ? 5 : 6;
								content = (
									<Card>
										<Statistic
											title={
												<Tooltip title="ACOS = 花费 / 销售额。越低越好，低于盈亏平衡 ACOS 即盈利">
													平均 ACOS
												</Tooltip>
											}
											value={data.kpi.acos ? data.kpi.acos * 100 : 0}
											precision={2}
											prefix={<PercentageOutlined />}
											suffix="%"
										/>
										<Sparkline
											data={data.daily_trend.map((d) => (d.acos ?? 0) * 100)}
											color="#faad14"
										/>
										{wowDeltas && (
											<WowIndicator
												delta={wowDeltas.acos}
												dodDelta={wowDeltas.dod_acos}
												invertColor
											/>
										)}
									</Card>
								);
								break;
							case "roas":
								span = hasTacos ? 5 : 6;
								content = (
									<Card>
										<Statistic
											title={
												<Tooltip title="ROAS = 销售额 / 花费。越高越好，>1 表示广告收益大于投入">
													平均 ROAS
												</Tooltip>
											}
											value={data.kpi.roas ?? 0}
											precision={2}
											prefix={<RiseOutlined />}
										/>
										<Sparkline
											data={data.daily_trend.map((d) => d.roas ?? 0)}
											color="#52c41a"
										/>
										{wowDeltas && (
											<WowIndicator
												delta={wowDeltas.roas}
												dodDelta={wowDeltas.dod_roas}
											/>
										)}
									</Card>
								);
								break;
							case "tacos":
								if (!hasTacos || !data.tacos) return null;
								span = 6;
								content = (
									<Card>
										<Statistic
											title={
												<Tooltip title="TACoS = 广告花费 / 总销售额（含有机）。衡量广告对整体营收的依赖度">
													TACoS
												</Tooltip>
											}
											value={
												data.tacos.value != null ? data.tacos.value * 100 : 0
											}
											precision={2}
											prefix={<PieChartOutlined />}
											suffix="%"
											valueStyle={{ color: "#722ed1" }}
										/>
									</Card>
								);
								break;
							default:
								return null;
						}
						return (
							<Col xs={24} sm={12} lg={span} key={id}>
								<SortableKpiCard id={id} index={index}>
									{content}
								</SortableKpiCard>
							</Col>
						);
					})}
				</Row>
			</DragDropProvider>

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

			{benchmarkData && benchmarkData.comparisons.length > 0 && (
				<Card
					title={`品类基准对比 - ${benchmarkData.category_label}`}
					style={{ marginBottom: 24 }}
				>
					<Row gutter={[24, 16]}>
						{benchmarkData.comparisons.map((item) => {
							const isGood =
								item.metric === "ACOS" || item.metric === "CPC"
									? item.status === "below"
									: item.status === "above";
							const maxVal = Math.max(item.actual, item.benchmark) * 1.2;
							const actualPct = maxVal > 0 ? (item.actual / maxVal) * 100 : 0;
							const benchPct = maxVal > 0 ? (item.benchmark / maxVal) * 100 : 0;
							const formatVal = (v: number) =>
								item.metric === "CTR" ||
								item.metric === "CVR" ||
								item.metric === "ACOS"
									? `${(v * 100).toFixed(2)}%`
									: `$${v.toFixed(2)}`;
							return (
								<Col xs={24} sm={12} md={12} lg={6} key={item.metric}>
									<div style={{ marginBottom: 8 }}>
										<strong>{item.metric}</strong>
										<span
											style={{
												float: "right",
												color: isGood ? "#52c41a" : "#ff4d4f",
												fontSize: 12,
											}}
										>
											{item.diff_pct > 0 ? "+" : ""}
											{item.diff_pct}%
										</span>
									</div>
									<div
										style={{ marginBottom: 4, fontSize: 12, color: "#9CA3AF" }}
									>
										实际: {formatVal(item.actual)}
									</div>
									<Progress
										percent={actualPct}
										strokeColor={isGood ? "#52c41a" : "#ff4d4f"}
										showInfo={false}
										size="small"
									/>
									<div
										style={{
											marginBottom: 4,
											marginTop: 4,
											fontSize: 12,
											color: "#9CA3AF",
										}}
									>
										基准: {formatVal(item.benchmark)}
									</div>
									<Progress
										percent={benchPct}
										strokeColor="#d9d9d9"
										showInfo={false}
										size="small"
									/>
								</Col>
							);
						})}
					</Row>
				</Card>
			)}
		</div>
	);
}
