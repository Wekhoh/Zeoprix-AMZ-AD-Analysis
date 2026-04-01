import { useEffect, useState } from "react";
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
import ReactECharts from "echarts-for-react";
import { withTheme } from "../utils/chartTheme";
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

	const fetchNotes = () => {
		if (!id) return;
		api.get(`/notes?campaign_id=${id}`).then((res) => setNotes(res.data));
	};

	useEffect(() => {
		if (!id) return;
		setLoading(true);
		Promise.all([
			api.get<CampaignDetailType>(`/campaigns/${id}`),
			api.get<DailyTrend[]>(`/summaries/by-date?campaign_id=${id}`),
			api.get<PlacementRecord[]>(`/placements?campaign_id=${id}`),
			api.get<OperationLog[]>(`/operation-logs?campaign_id=${id}`),
			api.get(`/notes?campaign_id=${id}`),
		])
			.then(([campRes, trendRes, placeRes, logRes, noteRes]) => {
				setCampaign(campRes.data);
				setTrends(trendRes.data);
				setPlacements(placeRes.data);
				setLogs(logRes.data);
				setNotes(noteRes.data);
			})
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
		await api.delete(`/notes/${noteId}`);
		message.success("笔记已删除");
		fetchNotes();
	};

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

	const tabItems = [
		{
			key: "placements",
			label: "展示位置分布",
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
					{campaign.base_bid != null && (
						<Text>基础出价: ${campaign.base_bid}</Text>
					)}
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
				<Col span={6}>
					<Card>
						<Statistic
							title="总花费"
							value={campaign.total_spend}
							precision={2}
							prefix={<DollarOutlined />}
							suffix="USD"
						/>
					</Card>
				</Col>
				<Col span={6}>
					<Card>
						<Statistic
							title="总订单"
							value={campaign.total_orders}
							prefix={<ShoppingCartOutlined />}
						/>
					</Card>
				</Col>
				<Col span={6}>
					<Card>
						<Statistic
							title="ROAS"
							value={campaign.roas ?? 0}
							precision={2}
							prefix={<RiseOutlined />}
						/>
					</Card>
				</Col>
				<Col span={6}>
					<Card>
						<Statistic
							title="ACOS"
							value={campaign.acos ? campaign.acos * 100 : 0}
							precision={2}
							prefix={<PercentageOutlined />}
							suffix="%"
						/>
					</Card>
				</Col>
			</Row>

			{/* Section C: Daily Trend */}
			<Card title="每日趋势" style={{ marginBottom: 24 }}>
				{trends.length > 0 ? (
					<ReactECharts
						option={withTheme(trendOption, isDark)}
						style={{ height: 350 }}
					/>
				) : (
					<Text type="secondary">暂无趋势数据</Text>
				)}
			</Card>

			{/* Section D: Tabs */}
			<Card>
				<Tabs items={tabItems} />
			</Card>
		</div>
	);
}
