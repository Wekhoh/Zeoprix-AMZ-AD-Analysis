import { useState, useEffect, useCallback } from "react";
import {
	Card,
	Upload,
	message,
	Table,
	Tabs,
	Tag,
	Space,
	InputNumber,
	Spin,
} from "antd";
import { UploadOutlined } from "@ant-design/icons";
import type { UploadFile, TableProps } from "antd";
import api from "../api/client";
import CampaignFilter from "../components/CampaignFilter";
import EmptyState from "../components/EmptyState";
import PageHelp from "../components/PageHelp";
import type { ImportResult } from "../types/api";

interface BucketItem {
	search_term: string;
	impressions: number;
	clicks: number;
	ctr: number | null;
	spend: number;
	cpc: number | null;
	orders: number;
	sales: number;
	roas: number | null;
	acos: number | null;
	cvr: number | null;
	bucket: string;
	action: string;
}

interface BucketStats {
	total: number;
	winners_count: number;
	potential_count: number;
	money_pits_count: number;
	low_data_count: number;
}

interface BucketResponse {
	winners: BucketItem[];
	potential: BucketItem[];
	money_pits: BucketItem[];
	low_data: BucketItem[];
	stats: BucketStats;
}

const formatPct = (val: number | null): string => {
	if (val === null || val === undefined) return "-";
	return `${(val * 100).toFixed(2)}%`;
};

const formatUsd = (val: number | null | undefined): string => {
	if (val === null || val === undefined) return "-";
	return `$${val.toFixed(2)}`;
};

const formatNum = (val: number | null | undefined): string => {
	if (val === null || val === undefined) return "-";
	return String(Math.round(val));
};

const BUCKET_COLORS: Record<string, string> = {
	winners: "#52c41a",
	potential: "#1677ff",
	money_pits: "#ff4d4f",
	low_data: "#8c8c8c",
};

const BUCKET_TAG_COLORS: Record<string, string> = {
	winners: "green",
	potential: "blue",
	money_pits: "red",
	low_data: "default",
};

function buildBucketColumns(
	bucketKey: string,
): TableProps<BucketItem>["columns"] {
	return [
		{
			title: "搜索词",
			dataIndex: "search_term",
			key: "search_term",
			fixed: "left" as const,
			width: 200,
		},
		{
			title: "曝光量",
			dataIndex: "impressions",
			key: "impressions",
			sorter: (a: BucketItem, b: BucketItem) => a.impressions - b.impressions,
			render: (v: number) => formatNum(v),
		},
		{
			title: "点击量",
			dataIndex: "clicks",
			key: "clicks",
			sorter: (a: BucketItem, b: BucketItem) => a.clicks - b.clicks,
			render: (v: number) => formatNum(v),
		},
		{
			title: "CTR",
			dataIndex: "ctr",
			key: "ctr",
			sorter: (a: BucketItem, b: BucketItem) => (a.ctr ?? 0) - (b.ctr ?? 0),
			render: (v: number | null) => formatPct(v),
		},
		{
			title: "花费",
			dataIndex: "spend",
			key: "spend",
			sorter: (a: BucketItem, b: BucketItem) => a.spend - b.spend,
			render: (v: number) => formatUsd(v),
		},
		{
			title: "CPC",
			dataIndex: "cpc",
			key: "cpc",
			sorter: (a: BucketItem, b: BucketItem) => (a.cpc ?? 0) - (b.cpc ?? 0),
			render: (v: number | null) => formatUsd(v),
		},
		{
			title: "订单",
			dataIndex: "orders",
			key: "orders",
			sorter: (a: BucketItem, b: BucketItem) => a.orders - b.orders,
			render: (v: number) => formatNum(v),
		},
		{
			title: "销售额",
			dataIndex: "sales",
			key: "sales",
			sorter: (a: BucketItem, b: BucketItem) => a.sales - b.sales,
			render: (v: number) => formatUsd(v),
		},
		{
			title: "ROAS",
			dataIndex: "roas",
			key: "roas",
			sorter: (a: BucketItem, b: BucketItem) => (a.roas ?? 0) - (b.roas ?? 0),
			render: (v: number | null) => (v !== null ? v.toFixed(2) : "-"),
		},
		{
			title: "ACOS",
			dataIndex: "acos",
			key: "acos",
			sorter: (a: BucketItem, b: BucketItem) => (a.acos ?? 0) - (b.acos ?? 0),
			render: (v: number | null) => formatPct(v),
		},
		{
			title: "建议操作",
			dataIndex: "action",
			key: "action",
			width: 260,
			render: (v: string) => (
				<Tag color={BUCKET_TAG_COLORS[bucketKey] ?? "default"}>{v}</Tag>
			),
		},
	];
}

export default function SearchTerms() {
	const [campaignId, setCampaignId] = useState<number | undefined>(undefined);
	const [activeTab, setActiveTab] = useState("winners");
	const [targetAcos, setTargetAcos] = useState(30);
	const [importResult, setImportResult] = useState<ImportResult | null>(null);
	const [uploading, setUploading] = useState(false);

	const [bucketData, setBucketData] = useState<BucketResponse | null>(null);
	const [loading, setLoading] = useState(false);

	const fetchData = useCallback(async () => {
		setLoading(true);
		try {
			const params = new URLSearchParams();
			if (campaignId !== undefined) {
				params.set("campaign_id", String(campaignId));
			}
			params.set("target_acos", String(targetAcos / 100));
			const qs = params.toString();
			const res = await api.get<BucketResponse>(
				`/search-terms/buckets${qs ? `?${qs}` : ""}`,
			);
			setBucketData(res.data);
		} finally {
			setLoading(false);
		}
	}, [campaignId, targetAcos]);

	useEffect(() => {
		void fetchData();
	}, [fetchData]);

	const handleUpload = async (fileList: UploadFile[]) => {
		if (!fileList.length) return;
		setUploading(true);
		const formData = new FormData();
		for (const f of fileList) {
			if (f.originFileObj) formData.append("files", f.originFileObj);
		}
		try {
			const res = await api.post<ImportResult>(
				"/search-terms/import",
				formData,
			);
			setImportResult(res.data);
			message.success(
				`导入完成: ${res.data.imported} 条新增, ${res.data.skipped} 条跳过`,
			);
			void fetchData();
		} catch {
			message.error("搜索词报告导入失败");
		} finally {
			setUploading(false);
		}
	};

	const stats = bucketData?.stats;

	const tabItems = [
		{
			key: "winners",
			label: (
				<span style={{ color: BUCKET_COLORS.winners }}>
					Winners ({stats?.winners_count ?? 0})
				</span>
			),
			children: (
				<Table<BucketItem>
					columns={buildBucketColumns("winners")}
					dataSource={bucketData?.winners ?? []}
					rowKey="search_term"
					loading={loading}
					size="middle"
					scroll={{ x: 1400 }}
					pagination={{ pageSize: 20, showSizeChanger: true }}
					rowClassName={() => "row-green-tint"}
				/>
			),
		},
		{
			key: "potential",
			label: (
				<span style={{ color: BUCKET_COLORS.potential }}>
					Potential ({stats?.potential_count ?? 0})
				</span>
			),
			children: (
				<Table<BucketItem>
					columns={buildBucketColumns("potential")}
					dataSource={bucketData?.potential ?? []}
					rowKey="search_term"
					loading={loading}
					size="middle"
					scroll={{ x: 1400 }}
					pagination={{ pageSize: 20, showSizeChanger: true }}
					rowClassName={() => "row-blue-tint"}
				/>
			),
		},
		{
			key: "money_pits",
			label: (
				<span style={{ color: BUCKET_COLORS.money_pits }}>
					Money Pits ({stats?.money_pits_count ?? 0})
				</span>
			),
			children: (
				<Table<BucketItem>
					columns={buildBucketColumns("money_pits")}
					dataSource={bucketData?.money_pits ?? []}
					rowKey="search_term"
					loading={loading}
					size="middle"
					scroll={{ x: 1400 }}
					pagination={{ pageSize: 20, showSizeChanger: true }}
					rowClassName={() => "row-red-tint"}
				/>
			),
		},
		{
			key: "low_data",
			label: (
				<span style={{ color: BUCKET_COLORS.low_data }}>
					Low Data ({stats?.low_data_count ?? 0})
				</span>
			),
			children: (
				<Table<BucketItem>
					columns={buildBucketColumns("low_data")}
					dataSource={bucketData?.low_data ?? []}
					rowKey="search_term"
					loading={loading}
					size="middle"
					scroll={{ x: 1400 }}
					pagination={{ pageSize: 20, showSizeChanger: true }}
				/>
			),
		},
	];

	return (
		<div>
			<div style={{ display: "flex", alignItems: "center", marginBottom: 16 }}>
				<span style={{ fontSize: 16, fontWeight: 600 }}>搜索词分析</span>
				<PageHelp
					title="搜索词分析帮助"
					content="搜索词按 4-Bucket 框架分类：Winners（高转化词）、Potential（有潜力）、Money Pits（浪费预算）、Low Data（数据不足）。"
				/>
			</div>
			{/* Section A: CSV Upload */}
			<Card title="上传搜索词报告" style={{ marginBottom: 24 }}>
				<Upload.Dragger
					multiple
					accept=".csv"
					beforeUpload={() => false}
					onChange={({ fileList }) => handleUpload(fileList)}
					showUploadList={false}
				>
					<p className="ant-upload-drag-icon">
						<UploadOutlined style={{ fontSize: 48, color: "#1677ff" }} />
					</p>
					<p>点击或拖拽搜索词报告 CSV 文件到此区域</p>
					<p style={{ color: "#9CA3AF" }}>支持同时上传多个文件</p>
				</Upload.Dragger>
				{uploading && <p style={{ marginTop: 16 }}>导入中...</p>}
				{importResult && (
					<div style={{ marginTop: 16 }}>
						<Space>
							<Tag color="green">新增: {importResult.imported}</Tag>
							<Tag color="orange">跳过: {importResult.skipped}</Tag>
							{importResult.errors > 0 && (
								<Tag color="red">错误: {importResult.errors}</Tag>
							)}
						</Space>
					</div>
				)}
			</Card>

			{/* Filters: Campaign + Target ACOS */}
			<Card style={{ marginBottom: 24 }}>
				<Space size="large">
					<Space>
						<span>筛选广告活动:</span>
						<CampaignFilter value={campaignId} onChange={setCampaignId} />
					</Space>
					<Space>
						<span>目标 ACOS:</span>
						<InputNumber
							value={targetAcos}
							onChange={(v) => setTargetAcos(v ?? 30)}
							min={1}
							max={100}
							suffix="%"
							style={{ width: 100 }}
						/>
					</Space>
				</Space>
			</Card>

			{/* Stats Summary Bar */}
			{stats && (
				<Card size="small" style={{ marginBottom: 24 }}>
					<Spin spinning={loading}>
						<Space size="large" style={{ fontSize: 14 }}>
							<span>
								总计 <strong>{stats.total}</strong> 词
							</span>
							<span style={{ color: BUCKET_COLORS.winners }}>
								Winners <strong>{stats.winners_count}</strong>
							</span>
							<span style={{ color: BUCKET_COLORS.potential }}>
								Potential <strong>{stats.potential_count}</strong>
							</span>
							<span style={{ color: BUCKET_COLORS.money_pits }}>
								Money Pits <strong>{stats.money_pits_count}</strong>
							</span>
							<span style={{ color: BUCKET_COLORS.low_data }}>
								Low Data <strong>{stats.low_data_count}</strong>
							</span>
						</Space>
					</Spin>
				</Card>
			)}

			{/* 4-Bucket Tabs */}
			{!loading && stats?.total === 0 ? (
				<EmptyState
					title="暂无搜索词数据"
					description="请先上传搜索词报告 CSV 文件，上传后系统将自动分析搜索词表现"
				/>
			) : (
				<Card>
					<Tabs
						activeKey={activeTab}
						onChange={setActiveTab}
						items={tabItems}
					/>
				</Card>
			)}

			{/* Row tint styles — dark theme compatible */}
			<style>{`
				.row-green-tint td { background-color: rgba(16,185,129,0.08) !important; }
				.row-green-tint:hover td { background-color: rgba(16,185,129,0.15) !important; }
				.row-blue-tint td { background-color: rgba(59,130,246,0.08) !important; }
				.row-blue-tint:hover td { background-color: rgba(59,130,246,0.15) !important; }
				.row-red-tint td { background-color: rgba(239,68,68,0.08) !important; }
				.row-red-tint:hover td { background-color: rgba(239,68,68,0.15) !important; }
			`}</style>
		</div>
	);
}
