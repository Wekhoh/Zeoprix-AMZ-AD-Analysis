import { useEffect, useState, useMemo } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Table, Tag, Spin, Tabs } from "antd";
import api from "../api/client";
import EmptyState from "../components/EmptyState";
import PageHelp from "../components/PageHelp";
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

export default function Campaigns() {
	const [campaigns, setCampaigns] = useState<Campaign[]>([]);
	const [loading, setLoading] = useState(true);
	const [adTypeFilter, setAdTypeFilter] = useState("all");
	const navigate = useNavigate();

	useEffect(() => {
		api.get("/campaigns").then((res) => {
			setCampaigns(res.data);
			setLoading(false);
		});
	}, []);

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
			width: 80,
			render: (v: string) => (
				<Tag color={AD_TYPE_COLOR[v] ?? "default"}>{v}</Tag>
			),
		},
		{
			title: "竞价策略",
			dataIndex: "bidding_strategy",
			key: "strategy",
			width: 200,
		},
		{
			title: "基础出价",
			dataIndex: "base_bid",
			key: "bid",
			width: 90,
			render: (v: number | null) => (v ? `$${v}` : "-"),
		},
		{
			title: "状态",
			dataIndex: "status",
			key: "status",
			width: 100,
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
	];

	if (!loading && campaigns.length === 0) {
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
		<Spin spinning={loading}>
			<div style={{ display: "flex", alignItems: "center", marginBottom: 16 }}>
				<Tabs
					activeKey={adTypeFilter}
					onChange={setAdTypeFilter}
					items={AD_TYPE_TABS}
					style={{ marginBottom: 0, flex: 1 }}
				/>
				<PageHelp
					title="广告活动帮助"
					content="显示所有已导入的广告活动。点击活动名称查看详细数据和趋势图。使用顶部 Tab 按广告类型筛选。"
				/>
			</div>
			<Table
				columns={columns}
				dataSource={filteredCampaigns}
				rowKey="id"
				size="middle"
			/>
		</Spin>
	);
}
