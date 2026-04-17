import { useEffect, useState, useMemo, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
	Button,
	Dropdown,
	Input,
	message,
	Modal,
	Progress,
	Select,
	Space,
	Table,
	Tag,
	Tabs,
	Tooltip,
} from "antd";
import {
	BookOutlined,
	CloseCircleOutlined,
	TagsOutlined,
} from "@ant-design/icons";
import api from "../api/client";
import EmptyState from "../components/EmptyState";
import FilterToolbar from "../components/FilterToolbar";
import PageHelp from "../components/PageHelp";
import PageSkeleton from "../components/PageSkeleton";
import ColumnSettingsButton, {
	type ColumnDescriptor,
} from "../components/ColumnSettingsButton";
import { useFilterParams } from "../hooks/useFilterParams";
import { useColumnVisibility } from "../hooks/useColumnVisibility";
import { fmtUsd, fmtPct, fmtNum } from "../utils/formatters";
import type { Campaign } from "../types/api";

interface FilterPreset {
	name: string;
	adType: string;
	tags: string[];
}

const AD_TYPE_COLOR: Record<string, string> = {
	SP: "blue",
	SB: "purple",
	SD: "orange",
	SBV: "cyan",
};

const CAMPAIGN_COLUMN_DESCRIPTORS: ColumnDescriptor[] = [
	{ key: "name", label: "广告活动名称", required: true },
	{ key: "ad_type", label: "类型" },
	{ key: "status", label: "状态" },
	{ key: "spend", label: "花费" },
	{ key: "orders", label: "订单" },
	{ key: "acos", label: "ACOS" },
	{ key: "roas", label: "ROAS" },
	{ key: "budget", label: "日预算" },
	{ key: "bid", label: "出价" },
	{ key: "tags", label: "标签" },
];
const CAMPAIGN_COLUMN_KEYS = CAMPAIGN_COLUMN_DESCRIPTORS.map((c) => c.key);

const AD_TYPE_TABS = [
	{ key: "all", label: "全部" },
	{ key: "SP", label: "SP" },
	{ key: "SB", label: "SB" },
	{ key: "SD", label: "SD" },
	{ key: "SBV", label: "SBV" },
];

export default function Campaigns() {
	const [campaigns, setCampaigns] = useState<Campaign[]>([]);
	const [loading, setLoading] = useState(true);
	const [adTypeFilter, setAdTypeFilter] = useState("all");
	const [allTags, setAllTags] = useState<string[]>([]);
	const [tagFilter, setTagFilter] = useState<string[]>([]);
	const [editingCampaign, setEditingCampaign] = useState<Campaign | null>(null);
	const [editingTags, setEditingTags] = useState<string[]>([]);
	const [hiddenCols, toggleCol, resetCols] = useColumnVisibility(
		"campaigns_hidden_cols",
		CAMPAIGN_COLUMN_KEYS,
	);
	const [presets, setPresets] = useState<FilterPreset[]>(() => {
		try {
			const saved = localStorage.getItem("campaigns_filter_presets");
			return saved ? JSON.parse(saved) : [];
		} catch {
			return [];
		}
	});
	const [savePresetOpen, setSavePresetOpen] = useState(false);
	const [newPresetName, setNewPresetName] = useState("");
	const navigate = useNavigate();
	const { dateFrom, dateTo, marketplaceId, buildQueryString } =
		useFilterParams();

	const fetchData = useCallback(() => {
		setLoading(true);
		api
			.get(`/campaigns${buildQueryString()}`)
			.then((res) => setCampaigns(res.data))
			.catch(() => {})
			.finally(() => setLoading(false));
	}, [buildQueryString]);

	const fetchTags = useCallback(() => {
		api
			.get<string[]>("/campaigns/tags/all")
			.then((res) => setAllTags(res.data))
			.catch(() => {});
	}, []);

	// eslint-disable-next-line react-hooks/set-state-in-effect -- canonical data-fetch-on-filter-change; setState happens inside fetchData (async)
	useEffect(fetchData, [dateFrom, dateTo, marketplaceId, fetchData]);
	useEffect(fetchTags, [fetchTags]);

	const filteredCampaigns = useMemo(() => {
		return campaigns.filter((c) => {
			if (adTypeFilter !== "all" && c.ad_type !== adTypeFilter) return false;
			if (tagFilter.length > 0) {
				const cTags = c.tags || [];
				if (!tagFilter.some((t) => cTags.includes(t))) return false;
			}
			return true;
		});
	}, [campaigns, adTypeFilter, tagFilter]);

	const openTagEditor = (campaign: Campaign) => {
		setEditingCampaign(campaign);
		setEditingTags(campaign.tags || []);
	};

	const saveCampaignTags = async () => {
		if (!editingCampaign) return;
		try {
			await api.put(`/campaigns/${editingCampaign.id}/tags`, {
				tags: editingTags,
			});
			message.success("标签已保存");
			setEditingCampaign(null);
			fetchData();
			fetchTags();
		} catch {
			message.error("保存失败");
		}
	};

	const persistPresets = (next: FilterPreset[]) => {
		setPresets(next);
		localStorage.setItem("campaigns_filter_presets", JSON.stringify(next));
	};

	const saveCurrentAsPreset = () => {
		if (!newPresetName.trim()) {
			message.warning("请输入预设名称");
			return;
		}
		const preset: FilterPreset = {
			name: newPresetName.trim(),
			adType: adTypeFilter,
			tags: tagFilter,
		};
		const existing = presets.filter((p) => p.name !== preset.name);
		persistPresets([...existing, preset]);
		message.success(`已保存预设「${preset.name}」`);
		setSavePresetOpen(false);
		setNewPresetName("");
	};

	const applyPreset = (preset: FilterPreset) => {
		setAdTypeFilter(preset.adType);
		setTagFilter(preset.tags);
		message.success(`已应用「${preset.name}」`);
	};

	const deletePreset = (name: string) => {
		persistPresets(presets.filter((p) => p.name !== name));
		message.success(`已删除预设「${name}」`);
	};

	const columns = [
		{
			title: "广告活动名称",
			dataIndex: "name",
			key: "name",
			ellipsis: true,
			fixed: "left" as const,
			width: 220,
			render: (text: string, record: Campaign) => (
				<Link to={`/campaigns/${record.id}`} style={{ color: "#1677ff" }}>
					{text}
				</Link>
			),
		},
		{
			title: "类型",
			dataIndex: "ad_type",
			key: "ad_type",
			width: 70,
			render: (v: string) => (
				<Tag color={AD_TYPE_COLOR[v] ?? "default"}>{v}</Tag>
			),
		},
		{
			title: "状态",
			dataIndex: "status",
			key: "status",
			width: 90,
			render: (s: string) => (
				<Tag
					color={
						s === "Delivering" ? "green" : s === "Paused" ? "red" : "default"
					}
				>
					{s}
				</Tag>
			),
		},
		{
			title: "花费",
			dataIndex: "spend",
			key: "spend",
			width: 100,
			sorter: (a: Campaign, b: Campaign) => (a.spend ?? 0) - (b.spend ?? 0),
			render: (v: number) => fmtUsd(v),
		},
		{
			title: "订单",
			dataIndex: "orders",
			key: "orders",
			width: 80,
			sorter: (a: Campaign, b: Campaign) => (a.orders ?? 0) - (b.orders ?? 0),
			render: (v: number) => fmtNum(v),
		},
		{
			title: "ACOS",
			dataIndex: "acos",
			key: "acos",
			width: 90,
			sorter: (a: Campaign, b: Campaign) => (a.acos ?? 0) - (b.acos ?? 0),
			render: (v: number | null) => {
				const text = fmtPct(v);
				const color =
					v != null && v > 0.5
						? "#ff4d4f"
						: v != null && v < 0.25
							? "#52c41a"
							: undefined;
				return <span style={{ color }}>{text}</span>;
			},
		},
		{
			title: "ROAS",
			dataIndex: "roas",
			key: "roas",
			width: 80,
			sorter: (a: Campaign, b: Campaign) => (a.roas ?? 0) - (b.roas ?? 0),
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
			title: "日预算",
			dataIndex: "daily_budget",
			key: "budget",
			width: 130,
			sorter: (a: Campaign, b: Campaign) =>
				(a.daily_budget ?? 0) - (b.daily_budget ?? 0),
			render: (budget: number | null, record: Campaign) => {
				if (budget == null) return "-";
				const spend = record.spend ?? 0;
				const pct = budget > 0 ? Math.min((spend / budget) * 100, 100) : 0;
				const strokeColor =
					pct > 90 ? "#ff4d4f" : pct > 70 ? "#faad14" : "#52c41a";
				return (
					<Tooltip
						title={`花费 $${spend.toFixed(2)} / 日预算 $${budget.toFixed(2)}`}
					>
						<div style={{ minWidth: 80 }}>
							<div style={{ fontSize: 12 }}>${budget.toFixed(0)}/天</div>
							<Progress
								percent={pct}
								size="small"
								strokeColor={strokeColor}
								showInfo={false}
							/>
						</div>
					</Tooltip>
				);
			},
		},
		{
			title: "出价",
			dataIndex: "base_bid",
			key: "bid",
			width: 80,
			render: (v: number | null) => (v ? `$${v}` : "-"),
		},
		{
			title: "标签",
			dataIndex: "tags",
			key: "tags",
			width: 180,
			render: (tags: string[] | undefined, record: Campaign) => (
				<div
					style={{ cursor: "pointer", minHeight: 22 }}
					onClick={() => openTagEditor(record)}
				>
					{tags && tags.length > 0 ? (
						<Space size={4} wrap>
							{tags.map((t) => (
								<Tag key={t} color="purple" style={{ margin: 0 }}>
									{t}
								</Tag>
							))}
						</Space>
					) : (
						<Button size="small" type="text" icon={<TagsOutlined />}>
							添加标签
						</Button>
					)}
				</div>
			),
		},
	];

	if (loading) return <PageSkeleton variant="table" />;

	if (campaigns.length === 0) {
		return (
			<EmptyState
				title="暂无广告活动"
				description="导入展示位置数据后，系统会自动创建广告活动"
				actionText="去导入数据"
				onAction={() => navigate("/import")}
			/>
		);
	}

	return (
		<div>
			<div style={{ display: "flex", alignItems: "center", marginBottom: 16 }}>
				<Tabs
					activeKey={adTypeFilter}
					onChange={setAdTypeFilter}
					items={AD_TYPE_TABS}
					style={{ marginBottom: 0, flex: 1 }}
				/>
				<FilterToolbar showCampaignFilter={false} />
				<ColumnSettingsButton
					columns={CAMPAIGN_COLUMN_DESCRIPTORS}
					hiddenKeys={hiddenCols}
					onToggle={toggleCol}
					onReset={resetCols}
				/>
				<PageHelp
					title="广告活动帮助"
					content="显示所有已导入的广告活动及其绩效指标。点击活动名称查看详情。ACOS 红色表示 >50%，绿色表示 <25%。ROAS 绿色表示 >3。点击标签列编辑标签。"
				/>
			</div>
			<div style={{ marginBottom: 12 }}>
				<Space size="small" align="center" wrap>
					{allTags.length > 0 && (
						<>
							<TagsOutlined style={{ color: "#9CA3AF" }} />
							<span style={{ fontSize: 13 }}>按标签筛选:</span>
							<Select
								mode="multiple"
								allowClear
								placeholder="选择标签"
								value={tagFilter}
								onChange={setTagFilter}
								style={{ minWidth: 280 }}
								options={allTags.map((t) => ({ label: t, value: t }))}
							/>
						</>
					)}
					<Dropdown
						menu={{
							items: [
								{
									key: "save",
									icon: <BookOutlined />,
									label: "保存当前筛选为预设...",
									onClick: () => setSavePresetOpen(true),
								},
								...(presets.length > 0
									? [
											{ type: "divider" as const },
											...presets.map((p) => ({
												key: p.name,
												label: (
													<Space>
														<span>{p.name}</span>
														<CloseCircleOutlined
															style={{ color: "#ff4d4f" }}
															onClick={(e: React.MouseEvent) => {
																e.stopPropagation();
																deletePreset(p.name);
															}}
														/>
													</Space>
												),
												onClick: () => applyPreset(p),
											})),
										]
									: []),
							],
						}}
					>
						<Button icon={<BookOutlined />}>
							筛选预设 {presets.length > 0 ? `(${presets.length})` : ""}
						</Button>
					</Dropdown>
				</Space>
			</div>

			<Modal
				title="保存筛选预设"
				open={savePresetOpen}
				onOk={saveCurrentAsPreset}
				onCancel={() => {
					setSavePresetOpen(false);
					setNewPresetName("");
				}}
				okText="保存"
				cancelText="取消"
			>
				<p style={{ fontSize: 12, color: "#9CA3AF", marginBottom: 8 }}>
					当前筛选: {adTypeFilter === "all" ? "全部类型" : adTypeFilter}
					{tagFilter.length > 0 ? ` + 标签 [${tagFilter.join(", ")}]` : ""}
				</p>
				<Input
					placeholder="预设名称，例如: 高花费 SP 活动"
					value={newPresetName}
					onChange={(e) => setNewPresetName(e.target.value)}
					onPressEnter={saveCurrentAsPreset}
					autoFocus
				/>
			</Modal>
			<Table
				columns={columns.filter((c) => !hiddenCols.has(c.key))}
				dataSource={filteredCampaigns}
				rowKey="id"
				size="middle"
				scroll={{ x: 1280 }}
			/>
			<Modal
				title={`编辑标签 — ${editingCampaign?.name || ""}`}
				open={editingCampaign !== null}
				onOk={saveCampaignTags}
				onCancel={() => setEditingCampaign(null)}
				okText="保存"
				cancelText="取消"
			>
				<p style={{ color: "#9CA3AF", fontSize: 12, marginBottom: 8 }}>
					输入标签名称，回车添加。可选择已有标签或创建新标签。
				</p>
				<Select
					mode="tags"
					style={{ width: "100%" }}
					placeholder="例如: 新品, 清库存, 夏季款"
					value={editingTags}
					onChange={setEditingTags}
					options={allTags.map((t) => ({ label: t, value: t }))}
				/>
			</Modal>
		</div>
	);
}
