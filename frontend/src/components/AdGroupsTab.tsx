import { useState } from "react";
import { Table, Tag } from "antd";
import api from "../api/client";
import { fmtPct, fmtUsd } from "../utils/formatters";

export interface AdGroup {
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
}

interface KeywordRow {
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
}

interface AdGroupsTabProps {
	data: AdGroup[];
}

const adGroupColumns = [
	{ title: "广告组", dataIndex: "name", key: "name", ellipsis: true },
	{
		title: "状态",
		dataIndex: "status",
		key: "status",
		width: 90,
		render: (s: string) => (
			<Tag
				color={s === "Enabled" ? "green" : s === "Paused" ? "red" : "default"}
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
		sorter: (a: { spend: number }, b: { spend: number }) => a.spend - b.spend,
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
						color: v > 0.5 ? "#ff4d4f" : v < 0.25 ? "#52c41a" : undefined,
					}}
				>
					{fmtPct(v, 2)}
				</span>
			);
		},
	},
];

const keywordColumns = [
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
			<Tag color={v === "enabled" ? "green" : "default"}>{v}</Tag>
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
		render: (v: number | null) => (v != null ? fmtPct(v, 2) : "-"),
	},
	{
		title: "ROAS",
		dataIndex: "roas",
		key: "roas",
		width: 70,
		render: (v: number | null) => (v != null ? v.toFixed(2) : "-"),
	},
];

type KeywordState = Record<number, { loading: boolean; data: KeywordRow[] }>;

/**
 * Ad-groups tab body for CampaignDetail — ad-group table with expandable
 * keyword sub-rows loaded lazily on first expand. Owns its own keyword
 * cache keyed by ad-group id. Extracted from CampaignDetail.tsx (F2-γ3).
 */
export default function AdGroupsTab({ data }: AdGroupsTabProps) {
	const [expandedKeywords, setExpandedKeywords] = useState<KeywordState>({});

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

	return (
		<Table<AdGroup>
			columns={adGroupColumns}
			dataSource={data}
			rowKey="id"
			size="middle"
			pagination={false}
			expandable={{
				expandedRowRender: (record) => {
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
							columns={keywordColumns}
							dataSource={kwState.data}
							rowKey="id"
							size="small"
							pagination={false}
						/>
					);
				},
				onExpand: (expanded, record) => {
					if (expanded) fetchKeywordsForAdGroup(record.id);
				},
			}}
		/>
	);
}
