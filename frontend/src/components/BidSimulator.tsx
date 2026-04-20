import { useState } from "react";
import { Button, Card, Input, Space, Table, Typography, message } from "antd";
import api from "../api/client";

const { Text } = Typography;

interface SimResult {
	current: {
		base_bid: number;
		cpc: number;
		spend: number;
		orders: number;
		acos: number | null;
		roas: number | null;
	};
	projected: {
		base_bid: number;
		cpc: number;
		spend: number;
		orders: number;
		acos: number | null;
		roas: number | null;
	};
	deltas: {
		spend_pct: number | null;
		orders_pct: number | null;
		acos_pct: number | null;
	};
	disclaimer: string;
}

interface BidSimulatorProps {
	/** Campaign id used in the POST /campaigns/:id/simulate-bid endpoint */
	campaignId: string;
	/** Current base_bid displayed for reference */
	baseBid: number;
	/** Dark mode flag — only used to pick the disclaimer text color */
	isDark: boolean;
}

/**
 * Bid simulator card — extracted from CampaignDetail.tsx to isolate its
 * self-contained state (simBid / simResult / simLoading) and the
 * corresponding handleSimulate async call.
 *
 * Runs a linear-projection simulation via the backend
 * `/campaigns/{id}/simulate-bid` endpoint with a 30-day lookback.
 */
export default function BidSimulator({
	campaignId,
	baseBid,
	isDark,
}: BidSimulatorProps) {
	const [simBid, setSimBid] = useState<number | null>(null);
	const [simResult, setSimResult] = useState<SimResult | null>(null);
	const [simLoading, setSimLoading] = useState(false);

	const handleSimulate = async () => {
		if (!simBid || simBid <= 0 || !campaignId) {
			message.warning("请输入有效的新竞价");
			return;
		}
		setSimLoading(true);
		try {
			const res = await api.post<SimResult>(
				`/campaigns/${campaignId}/simulate-bid`,
				{
					new_base_bid: simBid,
					lookback_days: 30,
				},
			);
			setSimResult(res.data);
		} catch {
			// axios interceptor surfaces the error toast
		} finally {
			setSimLoading(false);
		}
	};

	return (
		<Card
			title="竞价模拟器"
			size="small"
			style={{ marginBottom: 24 }}
			extra={
				<Text type="secondary" style={{ fontSize: 12 }}>
					基于最近 30 天线性估算
				</Text>
			}
		>
			<Space align="center" wrap>
				<span>当前基础出价: </span>
				<strong>${baseBid}</strong>
				<span style={{ marginLeft: 16 }}>模拟新出价: </span>
				<Input
					type="number"
					step="0.01"
					min={0.02}
					placeholder="例如 1.50"
					style={{ width: 120 }}
					value={simBid ?? ""}
					onChange={(e) => setSimBid(parseFloat(e.target.value) || null)}
					prefix="$"
				/>
				<Button
					type="primary"
					onClick={handleSimulate}
					loading={simLoading}
					disabled={!simBid}
				>
					模拟
				</Button>
			</Space>
			{simResult && (
				<div style={{ marginTop: 16 }}>
					<Table
						size="small"
						pagination={false}
						columns={[
							{
								title: "指标",
								dataIndex: "metric",
								key: "metric",
								width: 100,
							},
							{ title: "当前", dataIndex: "current", key: "current" },
							{ title: "预估", dataIndex: "projected", key: "projected" },
							{
								title: "变化",
								dataIndex: "delta",
								key: "delta",
								render: (v: string | null) => {
									if (!v) return "-";
									const isUp = v.startsWith("+");
									return (
										<span style={{ color: isUp ? "#ff4d4f" : "#52c41a" }}>
											{v}
										</span>
									);
								},
							},
						]}
						dataSource={[
							{
								key: "bid",
								metric: "基础出价",
								current: `$${simResult.current.base_bid.toFixed(2)}`,
								projected: `$${simResult.projected.base_bid.toFixed(2)}`,
								delta: null,
							},
							{
								key: "cpc",
								metric: "CPC",
								current: `$${simResult.current.cpc.toFixed(2)}`,
								projected: `$${simResult.projected.cpc.toFixed(2)}`,
								delta: null,
							},
							{
								key: "spend",
								metric: "花费",
								current: `$${simResult.current.spend.toFixed(2)}`,
								projected: `$${simResult.projected.spend.toFixed(2)}`,
								delta:
									simResult.deltas.spend_pct !== null
										? `${simResult.deltas.spend_pct > 0 ? "+" : ""}${simResult.deltas.spend_pct}%`
										: null,
							},
							{
								key: "orders",
								metric: "订单",
								current: simResult.current.orders,
								projected: simResult.projected.orders,
								delta:
									simResult.deltas.orders_pct !== null
										? `${simResult.deltas.orders_pct > 0 ? "+" : ""}${simResult.deltas.orders_pct}%`
										: null,
							},
							{
								key: "acos",
								metric: "ACOS",
								current:
									simResult.current.acos != null
										? `${(simResult.current.acos * 100).toFixed(1)}%`
										: "-",
								projected:
									simResult.projected.acos != null
										? `${(simResult.projected.acos * 100).toFixed(1)}%`
										: "-",
								delta:
									simResult.deltas.acos_pct !== null
										? `${simResult.deltas.acos_pct > 0 ? "+" : ""}${simResult.deltas.acos_pct}%`
										: null,
							},
						]}
					/>
					<div
						style={{
							marginTop: 12,
							fontSize: 11,
							color: isDark ? "#6B7280" : "#9CA3AF",
							fontStyle: "italic",
						}}
					>
						{simResult.disclaimer}
					</div>
				</div>
			)}
		</Card>
	);
}
