import { useEffect, useState, useMemo, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Table, Tag, Tabs } from "antd";
import api from "../api/client";
import EmptyState from "../components/EmptyState";
import FilterToolbar from "../components/FilterToolbar";
import PageHelp from "../components/PageHelp";
import PageSkeleton from "../components/PageSkeleton";
import { useFilterParams } from "../hooks/useFilterParams";
import type { Campaign } from "../types/api";

const AD_TYPE_COLOR: Record<string, string> = {
	SP: "blue",
	SB: "purple",
	SD: "orange",
	SBV: "cyan",
};

const AD_TYPE_TABS = [
	{ key: "all", label: "全部" },
	{ key: "SP", label: "SP" },
	{ key: "SB", label: "SB" },
	{ key: "SD", label: "SD" },
	{ key: "SBV", label: "SBV" },
];

const fmtUsd = (v: number | undefined) =>
	v != null ? `$${v.toFixed(2)}` : "-";
const fmtPct = (v: number | null | undefined) =>
	v != null ? `${(v * 100).toFixed(1)}%` : "-";
const fmtNum = (v: number | undefined) =>
	v != null ? v.toLocaleString() : "-";

export default function Campaigns() {
	const [campaigns, setCampaigns] = useState<Campaign[]>([]);
	const [loading, setLoading] = useState(true);
	const [adTypeFilter, setAdTypeFilter] = useState("all");
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

	useEffect(fetchData, [dateFrom, dateTo, marketplaceId, fetchData]);

	const filteredCampaigns = useMemo(() => {
		if (adTypeFilter === "all") return campaigns;
		return campaigns.filter((c) => c.ad_type === adTypeFilter);
	}, [campaigns, adTypeFilter]);

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
			title: "出价",
			dataIndex: "base_bid",
			key: "bid",
			width: 80,
			render: (v: number | null) => (v ? `$${v}` : "-"),
		},
		{
			title: "竞价策略",
			dataIndex: "bidding_strategy",
			key: "strategy",
			width: 180,
			ellipsis: true,
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
				<PageHelp
					title="广告活��帮助"
					content="显示所有已导入的广告活动及其绩效指标。点击活动名称查看详情。ACOS 红色表示 >50%，绿色表示 <25%。ROAS 绿色表示 >3。"
				/>
			</div>
			<Table
				columns={columns}
				dataSource={filteredCampaigns}
				rowKey="id"
				size="middle"
				scroll={{ x: 1100 }}
			/>
		</div>
	);
}
