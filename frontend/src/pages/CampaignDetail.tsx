import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { Card, Spin, Tabs, Typography } from "antd";
import { EditOutlined } from "@ant-design/icons";
import BidSimulator from "../components/BidSimulator";
import CampaignHeader from "../components/CampaignHeader";
import CampaignKpiCards from "../components/CampaignKpiCards";
import CampaignNotesTab from "../components/CampaignNotesTab";
import OperationLogsTab from "../components/OperationLogsTab";
import PlacementDetailsTab from "../components/PlacementDetailsTab";
import PlacementSummaryTab, {
	type PlacementSummary,
} from "../components/PlacementSummaryTab";
import AdGroupsTab, { type AdGroup } from "../components/AdGroupsTab";
import echarts from "../utils/echartsCore";
import ReactECharts from "../utils/reactEcharts";
import { withTheme } from "../utils/chartTheme";
import { calcWowDeltas } from "../utils/wowDeltas";
import api from "../api/client";
import { useTheme } from "../hooks/useTheme";
import type {
	CampaignDetail as CampaignDetailType,
	DailyTrend,
	PlacementRecord,
	OperationLog,
} from "../types/api";

const { Text } = Typography;

export default function CampaignDetail() {
	const { id } = useParams<{ id: string }>();
	const { isDark } = useTheme();
	const [campaign, setCampaign] = useState<CampaignDetailType | null>(null);
	const [trends, setTrends] = useState<DailyTrend[]>([]);
	const [placements, setPlacements] = useState<PlacementRecord[]>([]);
	const [logs, setLogs] = useState<OperationLog[]>([]);
	const [loading, setLoading] = useState(true);
	const [notes, setNotes] = useState<
		{
			id: number;
			content: string;
			note_type: string;
			created_at: string | null;
		}[]
	>([]);
	const [placementSummary, setPlacementSummary] = useState<PlacementSummary[]>(
		[],
	);
	const [adGroups, setAdGroups] = useState<AdGroup[]>([]);

	const fetchNotes = () => {
		if (!id) return;
		api.get(`/notes?campaign_id=${id}`).then((res) => setNotes(res.data));
	};

	useEffect(() => {
		if (!id) return;
		// eslint-disable-next-line react-hooks/set-state-in-effect -- canonical fetch-reset: clear prior loading state before the 7-endpoint Promise.all; same pattern as Campaigns.tsx:112
		setLoading(true);
		Promise.all([
			api.get<CampaignDetailType>(`/campaigns/${id}`),
			api.get<DailyTrend[]>(`/summaries/by-date?campaign_id=${id}`),
			api.get(`/placements?campaign_id=${id}`),
			api.get(`/operation-logs?campaign_id=${id}`),
			api.get(`/notes?campaign_id=${id}`),
			api.get(`/campaigns/${id}/placement-summary`),
			api.get(`/campaigns/${id}/ad-groups`),
		])
			.then(
				([campRes, trendRes, placeRes, logRes, noteRes, pSumRes, agRes]) => {
					setCampaign(campRes.data);
					// B6-D-14: Track recent campaigns for sidebar
					try {
						const RECENT_KEY = "amz_recent_campaigns";
						const recent: Array<{ id: number; name: string }> = JSON.parse(
							localStorage.getItem(RECENT_KEY) || "[]",
						);
						const campId = campRes.data.id;
						const campName = campRes.data.name;
						const filtered = recent.filter((r) => r.id !== campId);
						filtered.unshift({ id: campId, name: campName });
						localStorage.setItem(
							RECENT_KEY,
							JSON.stringify(filtered.slice(0, 5)),
						);
					} catch {
						/* localStorage full or parse error — non-critical */
					}
					setTrends(trendRes.data);
					setPlacements(placeRes.data?.data ?? placeRes.data);
					setLogs(logRes.data?.data ?? logRes.data);
					setNotes(noteRes.data);
					setPlacementSummary(pSumRes.data);
					setAdGroups(agRes.data);
				},
			)
			.catch(() => {})
			.finally(() => setLoading(false));
	}, [id]);

	const wowDeltas = useMemo(
		() => (trends.length > 0 ? calcWowDeltas(trends) : null),
		[trends],
	);

	// Build markLine data from operation logs (bid/budget/status changes)
	const changeMarkLines = useMemo(() => {
		const trendDates = new Set(trends.map((t) => t.date));
		const marks: {
			xAxis: string;
			label: { formatter: string };
			lineStyle: { color: string };
		}[] = [];
		const seen = new Set<string>();
		for (const log of logs) {
			const key = `${log.date}-${log.change_type}`;
			if (seen.has(key) || !trendDates.has(log.date)) continue;
			seen.add(key);
			const ct = (log.change_type || "").toLowerCase();
			let color = "#9CA3AF";
			let label = "";
			if (ct.includes("bid") || ct.includes("竞价")) {
				color = "#3B82F6";
				label = "竞价";
			} else if (ct.includes("budget") || ct.includes("预算")) {
				color = "#10B981";
				label = "预算";
			} else if (ct.includes("status") || ct.includes("状态")) {
				color = "#EF4444";
				label = "状态";
			} else {
				continue;
			}
			marks.push({
				xAxis: log.date,
				label: { formatter: label },
				lineStyle: { color },
			});
		}
		return marks;
	}, [logs, trends]);

	if (loading || !campaign) {
		return (
			<Spin size="large" style={{ display: "block", margin: "100px auto" }} />
		);
	}

	const ATTRIBUTION_WINDOW_MAP: Record<string, number> = {
		SP: 7,
		SB: 14,
		SD: 14,
		SBV: 14,
		DSP: 14,
	};
	const attributionDays = ATTRIBUTION_WINDOW_MAP[campaign.ad_type] ?? 7;
	const isDynamicUpDown =
		campaign.bidding_strategy?.includes("Dynamic") &&
		campaign.bidding_strategy?.includes("up and down");

	/* ---------- Section C: Daily Trend Chart ---------- */
	const trendOption = {
		tooltip: { trigger: "axis" as const },
		legend: { data: ["花费 ($)", "订单", "ROAS"] },
		xAxis: {
			type: "category" as const,
			data: trends.map((d) => d.date),
		},
		yAxis: [
			{ type: "value" as const, name: "金额 / 数量" },
			{ type: "value" as const, name: "ROAS", position: "right" as const },
		],
		series: [
			{
				name: "花费 ($)",
				type: "line",
				data: trends.map((d) => d.spend),
				smooth: true,
				markLine:
					changeMarkLines.length > 0
						? {
								symbol: "none",
								label: { fontSize: 10, position: "start" },
								data: changeMarkLines,
							}
						: undefined,
			},
			{
				name: "订单",
				type: "line",
				data: trends.map((d) => d.orders),
				smooth: true,
			},
			{
				name: "ROAS",
				type: "line",
				yAxisIndex: 1,
				data: trends.map((d) => d.roas),
				smooth: true,
			},
		],
	};

	const tabItems = [
		{
			key: "placement-compare",
			label: "展示位置对比",
			children: <PlacementSummaryTab data={placementSummary} />,
		},
		{
			key: "ad-groups",
			label: `广告组 (${adGroups.length})`,
			children: <AdGroupsTab data={adGroups} />,
		},
		{
			key: "placements",
			label: "展示位置明细",
			children: <PlacementDetailsTab data={placements} />,
		},
		{
			key: "logs",
			label: "操作日志",
			children: <OperationLogsTab data={logs} />,
		},
		{
			key: "notes",
			label: (
				<span>
					<EditOutlined /> 运营笔记 ({notes.length})
				</span>
			),
			children: id ? (
				<CampaignNotesTab campaignId={id} notes={notes} onChange={fetchNotes} />
			) : null,
		},
	];

	return (
		<div>
			<CampaignHeader
				campaign={campaign}
				isDark={isDark}
				attributionDays={attributionDays}
				isDynamicUpDown={Boolean(isDynamicUpDown)}
			/>
			<CampaignKpiCards campaign={campaign} wowDeltas={wowDeltas} />

			{/* Section C: Daily Trend */}
			<Card title="每日趋势" style={{ marginBottom: 24 }}>
				{trends.length > 0 ? (
					<ReactECharts
						echarts={echarts}
						option={withTheme(trendOption, isDark)}
						style={{ height: 350 }}
					/>
				) : (
					<Text type="secondary">暂无趋势数据</Text>
				)}
			</Card>

			{/* Section C2: Bid Simulator */}
			{campaign.base_bid && id && (
				<BidSimulator
					campaignId={id}
					baseBid={campaign.base_bid}
					isDark={isDark}
				/>
			)}

			{/* Section D: Tabs */}
			<Card>
				<Tabs items={tabItems} />
			</Card>
		</div>
	);
}
