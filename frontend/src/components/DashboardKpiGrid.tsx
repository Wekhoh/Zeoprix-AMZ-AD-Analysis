import { useMemo } from "react";
import type { ReactNode } from "react";
import { Card, Col, Row, Statistic, Tooltip } from "antd";
import {
	DollarOutlined,
	PercentageOutlined,
	PieChartOutlined,
	RiseOutlined,
	ShoppingCartOutlined,
} from "@ant-design/icons";
import { DragDropProvider } from "@dnd-kit/react";
import { useSortable } from "@dnd-kit/react/sortable";
import { move } from "@dnd-kit/helpers";
import Sparkline from "./Sparkline";
import { useCardOrder } from "../hooks/useCardOrder";
import { WowIndicator, type WowDeltas } from "../utils/wowDeltas";
import type { DashboardData } from "../types/api";

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

interface DashboardKpiGridProps {
	data: DashboardData;
	wowDeltas: WowDeltas | null;
}

/**
 * Draggable KPI card grid for the Dashboard. Persists the card order to
 * localStorage under "dashboard_kpi_order" (via useCardOrder), which also
 * reconciles the stored order against the current default list on every
 * change (adds new cards, drops removed ones). Extracted from
 * Dashboard.tsx (F4-β).
 */
export default function DashboardKpiGrid({
	data,
	wowDeltas,
}: DashboardKpiGridProps) {
	const hasTacos = data.tacos?.has_data ?? false;
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

	return (
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
	);
}
