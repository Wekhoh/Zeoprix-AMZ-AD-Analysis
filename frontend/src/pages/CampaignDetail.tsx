import { useEffect, useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
	Card,
	Col,
	Row,
	Spin,
	Statistic,
	Table,
	Tabs,
	Tag,
	Typography,
	Button,
	Input,
	List,
	Popconfirm,
	message,
	Space,
} from "antd";
import {
	ArrowLeftOutlined,
	DollarOutlined,
	ShoppingCartOutlined,
	RiseOutlined,
	PercentageOutlined,
	EditOutlined,
	DeleteOutlined,
} from "@ant-design/icons";
import ReactECharts from "echarts-for-react/lib/core";
import BidSimulator from "../components/BidSimulator";
import echarts from "../utils/echartsCore";
import { withTheme } from "../utils/chartTheme";
import { fmtPct, fmtUsd } from "../utils/formatters";
import { calcWowDeltas, WowIndicator } from "../utils/wowDeltas";
import api from "../api/client";
import { useTheme } from "../hooks/useTheme";
import type {
	CampaignDetail as CampaignDetailType,
	DailyTrend,
	PlacementRecord,
	OperationLog,
} from "../types/api";

const { Title, Text } = Typography;

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
	const [newNote, setNewNote] = useState("");
	const [placementSummary, setPlacementSummary] = useState<
		{
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
		}[]
	>([]);
	const [adGroups, setAdGroups] = useState<
		{
			id: number;
			name: string;
			status: string;
			default_bid: number | null;
			keyword_count: number;
			impressions: number;
			clicks: number;
			spend: number;
			orders: number;
			sales: number;
			roas: number | null;
			acos: number | null;
		}[]
	>([]);
	const [expandedKeywords, setExpandedKeywords] = useState<
		Record<
			number,
			{
				loading: boolean;
				data: Array<{
					id: number;
					keyword_text: string;
					match_type: string;
					bid: number | null;
					state: string;
					impressions: number;
					clicks: number;
					spend: number;
					orders: number;
					sales: number;
					ctr: number | null;
					cpc: number | null;
					acos: number | null;
					roas: number | null;
				}>;
			}
		>
	>({});

	const fetchKeywordsForAdGroup = (adGroupId: number) => {
		if (expandedKeywords[adGroupId]?.data) return;
		setExpandedKeywords((prev) => ({
			...prev,
			[adGroupId]: { loading: true, data: [] },
		}));
		api.get(`/ad-groups/${adGroupId}/keywords`).then((res) => {
			setExpandedKeywords((prev) => ({
				...prev,
				[adGroupId]: { loading: false, data: res.data },
			}));
		});
	};

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

	const handleAddNote = async () => {
		if (!newNote.trim() || !id) return;
		await api.post("/notes", {
			campaign_id: Number(id),
			content: newNote.trim(),
			note_type: "decision",
		});
		setNewNote("");
		message.success("笔记已添加");
		fetchNotes();
	};

	const handleDeleteNote = async (noteId: number) => {
		try {
			await api.delete(`/notes/${noteId}`);
			fetchNotes();
			// Show undo toast (soft delete allows restore)
			message.open({
				type: "success",
				content: (
					<span>
						笔记已删除{" "}
						<Button
							type="link"
							size="small"
							style={{ padding: 0, marginLeft: 8 }}
							onClick={async () => {
								try {
									await api.post(`/notes/${noteId}/restore`);
									message.success("已恢复");
									fetchNotes();
								} catch {
									message.error("恢复失败，笔记可能已被永久删除");
								}
							}}
						>
							撤销
						</Button>
					</span>
				),
				duration: 5,
			});
		} catch {
			message.error("删除失败");
		}
	};

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

	const statusColor =
		campaign.status === "Delivering"
			? "green"
			: campaign.status === "Paused"
				? "red"
				: "default";

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

	/* ---------- Section D: Tab columns ---------- */
	const placementColumns = [
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

	const logColumns = [
		{ title: "日期", dataIndex: "date", key: "date", width: 110 },
		{ title: "时间", dataIndex: "time", key: "time", width: 70 },
		{ title: "变更类型", dataIndex: "change_type", key: "change", width: 200 },
		{ title: "修改前", dataIndex: "from_value", key: "from", width: 150 },
		{ title: "修改后", dataIndex: "to_value", key: "to", width: 150 },
		{ title: "层级", dataIndex: "level_type", key: "level", width: 90 },
	];

	const placementSummaryColumns = [
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

	const tabItems = [
		{
			key: "placement-compare",
			label: "展示位置对比",
			children: (
				<Table
					columns={placementSummaryColumns}
					dataSource={placementSummary}
					rowKey="placement_type"
					size="middle"
					pagination={false}
				/>
			),
		},
		{
			key: "ad-groups",
			label: `广告组 (${adGroups.length})`,
			children: (
				<Table<(typeof adGroups)[number]>
					columns={[
						{ title: "广告组", dataIndex: "name", key: "name", ellipsis: true },
						{
							title: "状态",
							dataIndex: "status",
							key: "status",
							width: 90,
							render: (s: string) => (
								<Tag
									color={
										s === "Enabled"
											? "green"
											: s === "Paused"
												? "red"
												: "default"
									}
								>
									{s}
								</Tag>
							),
						},
						{
							title: "出价",
							dataIndex: "default_bid",
							key: "bid",
							width: 80,
							render: (v: number | null) => (v != null ? `$${v}` : "-"),
						},
						{
							title: "关键词",
							dataIndex: "keyword_count",
							key: "kw_count",
							width: 70,
							render: (v: number) => v || 0,
						},
						{
							title: "花费",
							dataIndex: "spend",
							key: "spend",
							width: 90,
							sorter: (a: { spend: number }, b: { spend: number }) =>
								a.spend - b.spend,
							render: (v: number) => fmtUsd(v),
						},
						{
							title: "订单",
							dataIndex: "orders",
							key: "orders",
							width: 70,
							sorter: (a: { orders: number }, b: { orders: number }) =>
								a.orders - b.orders,
						},
						{
							title: "ROAS",
							dataIndex: "roas",
							key: "roas",
							width: 80,
							render: (v: number | null) =>
								v != null ? (
									<span style={{ color: v >= 3 ? "#52c41a" : undefined }}>
										{v.toFixed(2)}
									</span>
								) : (
									"-"
								),
						},
						{
							title: "ACOS",
							dataIndex: "acos",
							key: "acos",
							width: 90,
							render: (v: number | null) => {
								if (v == null) return "-";
								return (
									<span
										style={{
											color:
												v > 0.5 ? "#ff4d4f" : v < 0.25 ? "#52c41a" : undefined,
										}}
									>
										{fmtPct(v, 2)}
									</span>
								);
							},
						},
					]}
					dataSource={adGroups}
					rowKey="id"
					size="middle"
					pagination={false}
					expandable={{
						expandedRowRender: (record: { id: number }) => {
							const kwState = expandedKeywords[record.id];
							if (!kwState || kwState.loading) {
								return <span style={{ color: "#999" }}>加载关键词...</span>;
							}
							if (kwState.data.length === 0) {
								return (
									<span style={{ color: "#999" }}>
										暂无关键词数据（需导入 Keyword Report）
									</span>
								);
							}
							return (
								<Table
									columns={[
										{
											title: "关键词",
											dataIndex: "keyword_text",
											key: "kw",
											ellipsis: true,
										},
										{
											title: "匹配",
											dataIndex: "match_type",
											key: "mt",
											width: 80,
											render: (v: string) => <Tag>{v}</Tag>,
										},
										{
											title: "竞价",
											dataIndex: "bid",
											key: "bid",
											width: 70,
											render: (v: number | null) => (v != null ? `$${v}` : "-"),
										},
										{
											title: "状态",
											dataIndex: "state",
											key: "st",
											width: 80,
											render: (v: string) => (
												<Tag color={v === "enabled" ? "green" : "default"}>
													{v}
												</Tag>
											),
										},
										{
											title: "花费",
											dataIndex: "spend",
											key: "sp",
											width: 80,
											render: (v: number) => fmtUsd(v),
										},
										{
											title: "订单",
											dataIndex: "orders",
											key: "ord",
											width: 60,
										},
										{
											title: "ACOS",
											dataIndex: "acos",
											key: "acos",
											width: 80,
											render: (v: number | null) =>
												v != null ? fmtPct(v, 2) : "-",
										},
										{
											title: "ROAS",
											dataIndex: "roas",
											key: "roas",
											width: 70,
											render: (v: number | null) =>
												v != null ? v.toFixed(2) : "-",
										},
									]}
									dataSource={kwState.data}
									rowKey="id"
									size="small"
									pagination={false}
								/>
							);
						},
						onExpand: (expanded: boolean, record: { id: number }) => {
							if (expanded) fetchKeywordsForAdGroup(record.id);
						},
					}}
				/>
			),
		},
		{
			key: "placements",
			label: "展示位置明细",
			children: (
				<Table<PlacementRecord>
					columns={placementColumns}
					dataSource={placements}
					rowKey="id"
					size="small"
					scroll={{ x: 1200 }}
				/>
			),
		},
		{
			key: "logs",
			label: "操作日志",
			children: (
				<Table<OperationLog>
					columns={logColumns}
					dataSource={logs}
					rowKey="id"
					size="small"
					scroll={{ x: 1000 }}
				/>
			),
		},
		{
			key: "notes",
			label: (
				<span>
					<EditOutlined /> 运营笔记 ({notes.length})
				</span>
			),
			children: (
				<div>
					<Space.Compact style={{ width: "100%", marginBottom: 16 }}>
						<Input
							placeholder="记录优化决策、观察、提醒..."
							value={newNote}
							onChange={(e) => setNewNote(e.target.value)}
							onPressEnter={handleAddNote}
						/>
						<Button type="primary" onClick={handleAddNote}>
							添加笔记
						</Button>
					</Space.Compact>
					<List
						dataSource={notes}
						locale={{ emptyText: "暂无笔记" }}
						renderItem={(note) => (
							<List.Item
								actions={[
									<Popconfirm
										key="del"
										title="确定删除？"
										onConfirm={() => handleDeleteNote(note.id)}
									>
										<Button
											type="text"
											danger
											icon={<DeleteOutlined />}
											size="small"
											aria-label="删除笔记"
										/>
									</Popconfirm>,
								]}
							>
								<List.Item.Meta
									title={note.content}
									description={
										note.created_at ? note.created_at.slice(0, 19) : ""
									}
								/>
							</List.Item>
						)}
					/>
				</div>
			),
		},
	];

	return (
		<div>
			{/* Section A: Header */}
			<div style={{ marginBottom: 16 }}>
				<Link
					to="/campaigns"
					style={{ color: "#1677ff", marginBottom: 8, display: "inline-block" }}
				>
					<ArrowLeftOutlined /> 返回广告活动列表
				</Link>
				<div
					style={{
						display: "flex",
						alignItems: "center",
						gap: 12,
						marginBottom: 8,
					}}
				>
					<Title level={2} style={{ margin: 0 }}>
						{campaign.name}
					</Title>
					<Tag color={statusColor}>{campaign.status}</Tag>
				</div>
				<div
					style={{
						display: "flex",
						gap: 24,
						color: isDark ? "#9CA3AF" : "#6B7280",
					}}
				>
					<Text>类型: {campaign.ad_type}</Text>
					<Text>竞价策略: {campaign.bidding_strategy}</Text>
					{isDynamicUpDown && <Tag color="orange">竞价可翻倍</Tag>}
					{campaign.base_bid != null && (
						<Text>基础出价: ${campaign.base_bid}</Text>
					)}
					<Text>归因窗口: {attributionDays} 天</Text>
					{campaign.portfolio && <Text>组合: {campaign.portfolio}</Text>}
					{campaign.first_date && campaign.last_date && (
						<Text>
							数据范围: {campaign.first_date} ~ {campaign.last_date}
						</Text>
					)}
				</div>
			</div>

			{/* Section B: KPI Cards */}
			<Row gutter={16} style={{ marginBottom: 24 }}>
				<Col xs={24} sm={12} lg={6}>
					<Card>
						<Statistic
							title="总花费"
							value={campaign.total_spend}
							precision={2}
							prefix={<DollarOutlined />}
							suffix="USD"
						/>
						{wowDeltas && <WowIndicator delta={wowDeltas.spend} />}
					</Card>
				</Col>
				<Col xs={24} sm={12} lg={6}>
					<Card>
						<Statistic
							title="总订单"
							value={campaign.total_orders}
							prefix={<ShoppingCartOutlined />}
						/>
						{wowDeltas && <WowIndicator delta={wowDeltas.orders} />}
					</Card>
				</Col>
				<Col xs={24} sm={12} lg={6}>
					<Card>
						<Statistic
							title="ROAS"
							value={campaign.roas ?? 0}
							precision={2}
							prefix={<RiseOutlined />}
						/>
						{wowDeltas && <WowIndicator delta={wowDeltas.roas} />}
					</Card>
				</Col>
				<Col xs={24} sm={12} lg={6}>
					<Card>
						<Statistic
							title="ACOS"
							value={campaign.acos ? campaign.acos * 100 : 0}
							precision={2}
							prefix={<PercentageOutlined />}
							suffix="%"
						/>
						{wowDeltas && <WowIndicator delta={wowDeltas.acos} invertColor />}
					</Card>
				</Col>
			</Row>

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
