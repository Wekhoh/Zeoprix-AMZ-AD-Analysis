import { useState, useEffect, useCallback } from "react";
import {
	Alert,
	Button,
	Card,
	Upload,
	message,
	Table,
	Tabs,
	Tag,
	Space,
	InputNumber,
} from "antd";
import { UploadOutlined, DownloadOutlined } from "@ant-design/icons";
import type { UploadFile, TableProps } from "antd";
import api from "../api/client";
import CampaignFilter from "../components/CampaignFilter";
import EmptyState from "../components/EmptyState";
import PageHelp from "../components/PageHelp";
import type { ImportResult } from "../types/api";

interface BucketItem {
	search_term: string;
	campaign_id: number | null;
	campaign_name: string;
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
	suggested_bid?: number | null;
	whitelisted?: boolean;
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

function exportNegativeKeywords(moneyPits: BucketItem[]) {
	if (!moneyPits.length) {
		message.warning("暂无 Money Pits 数据可导出");
		return;
	}
	const header = "Keyword,Match Type\n";
	const rows = moneyPits
		.map((item) => `"${item.search_term.replace(/"/g, '""')}",Negative Exact`)
		.join("\n");
	const csv = "\uFEFF" + header + rows;
	const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
	const url = URL.createObjectURL(blob);
	const link = document.createElement("a");
	link.href = url;
	link.download = `negative_keywords_${new Date().toISOString().slice(0, 10)}.csv`;
	link.click();
	URL.revokeObjectURL(url);
}

function exportHarvestKeywords(winners: BucketItem[]) {
	if (!winners.length) {
		message.warning("暂无 Winners 数据可导出");
		return;
	}
	const header = "Campaign,Keyword,Match Type,Suggested Bid\n";
	const rows = winners
		.map((item) => {
			const term = item.search_term.replace(/"/g, '""');
			const campaign = (item.campaign_name || "").replace(/"/g, '""');
			const bid = item.cpc != null ? item.cpc.toFixed(2) : "";
			return `"${campaign}","${term}",Exact,${bid}`;
		})
		.join("\n");
	const csv = "\uFEFF" + header + rows;
	const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
	const url = URL.createObjectURL(blob);
	const link = document.createElement("a");
	link.href = url;
	link.download = `harvest_keywords_${new Date().toISOString().slice(0, 10)}.csv`;
	link.click();
	URL.revokeObjectURL(url);
}

function downloadBulkUploadExcel() {
	api
		.get("/search-terms/bulk-upload-export", { responseType: "blob" })
		.then((res) => {
			const blob = new Blob([res.data], {
				type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
			});
			const url = URL.createObjectURL(blob);
			const link = document.createElement("a");
			link.href = url;
			link.download = `amazon_bulk_upload_${new Date().toISOString().slice(0, 10)}.xlsx`;
			link.click();
			URL.revokeObjectURL(url);
		})
		.catch(() => message.error("Bulk Upload 导出失败"));
}

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
	processedTerms?: Record<string, string>,
	onMark?: (
		term: string,
		action: string,
		campName?: string,
		campId?: number | null,
	) => void,
	onWhitelist?: (term: string) => void,
): TableProps<BucketItem>["columns"] {
	return [
		{
			title: "来源活动",
			dataIndex: "campaign_name",
			key: "campaign_name",
			width: 160,
			ellipsis: true,
		},
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
		...(bucketKey === "winners" || bucketKey === "potential"
			? [
					{
						title: "建议竞价",
						dataIndex: "suggested_bid",
						key: "suggested_bid",
						width: 100,
						render: (v: number | null | undefined) =>
							v != null ? `$${v.toFixed(2)}` : "-",
					},
				]
			: []),
		{
			title: "建议操作",
			dataIndex: "action",
			key: "action",
			width: 280,
			render: (v: string, record: BucketItem) => {
				if (bucketKey === "money_pits" && record.whitelisted) {
					return (
						<Space size={4}>
							<Tag color="gold">白名单</Tag>
							<Tag color="default">{v}</Tag>
						</Space>
					);
				}
				return <Tag color={BUCKET_TAG_COLORS[bucketKey] ?? "default"}>{v}</Tag>;
			},
		},
		...(processedTerms && onMark
			? [
					{
						title: "状态",
						key: "processed",
						width: 100,
						render: (_: unknown, record: BucketItem) => {
							const status = processedTerms[record.search_term];
							if (status) {
								return (
									<Tag color="green">
										{status === "harvest_exact" ? "已收割" : "已否定"}
									</Tag>
								);
							}
							const action =
								bucketKey === "money_pits" ? "negate_exact" : "harvest_exact";
							const label = bucketKey === "money_pits" ? "否定" : "收割";
							return (
								<Space size={4}>
									<Button
										size="small"
										onClick={() =>
											onMark(
												record.search_term,
												action,
												record.campaign_name,
												record.campaign_id,
											)
										}
									>
										{label}
									</Button>
									{bucketKey === "money_pits" &&
										!record.whitelisted &&
										onWhitelist && (
											<Button
												size="small"
												type="dashed"
												onClick={() => onWhitelist(record.search_term)}
											>
												白名单
											</Button>
										)}
								</Space>
							);
						},
					},
				]
			: []),
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
	const [processedTerms, setProcessedTerms] = useState<Record<string, string>>(
		{},
	);

	useEffect(() => {
		api
			.get<Record<string, string>>("/search-terms/processed-terms")
			.then((res) => setProcessedTerms(res.data))
			.catch(() => {});
	}, []);

	const markAsProcessed = async (
		term: string,
		actionType: string,
		campaignName?: string,
		campaignId?: number | null,
	) => {
		await api.post("/search-terms/actions", {
			search_term: term,
			action_type: actionType,
			from_campaign_id: campaignId,
			from_campaign_name: campaignName,
		});
		setProcessedTerms((prev) => ({ ...prev, [term]: actionType }));
		message.success(`已标记「${term}」为 ${actionType}`);
	};

	const addToWhitelist = async (term: string) => {
		try {
			await api.post("/search-terms/whitelist", {
				terms: [term],
				reason: "从 Money Pits 加入",
			});
			message.success(`「${term}」已加入白名单`);
			void fetchData();
		} catch {
			message.error("加入白名单失败");
		}
	};

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
				<>
					<div style={{ marginBottom: 12, textAlign: "right" }}>
						<Space>
							<Button
								icon={<DownloadOutlined />}
								onClick={() => exportHarvestKeywords(bucketData?.winners ?? [])}
								disabled={!bucketData?.winners?.length}
							>
								Harvest 导出 CSV
							</Button>
							<Button
								type="primary"
								icon={<DownloadOutlined />}
								onClick={downloadBulkUploadExcel}
							>
								Amazon Bulk Upload Excel
							</Button>
						</Space>
					</div>
					<Table<BucketItem>
						columns={buildBucketColumns(
							"winners",
							processedTerms,
							markAsProcessed,
						)}
						dataSource={bucketData?.winners ?? []}
						rowKey={(r) => `${r.campaign_id}-${r.search_term}`}
						loading={loading}
						size="middle"
						scroll={{ x: 1600 }}
						pagination={{ pageSize: 20, showSizeChanger: true }}
						rowClassName={() => "row-green-tint"}
					/>
				</>
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
					columns={buildBucketColumns(
						"potential",
						processedTerms,
						markAsProcessed,
					)}
					dataSource={bucketData?.potential ?? []}
					rowKey={(r) => `${r.campaign_id}-${r.search_term}`}
					loading={loading}
					size="middle"
					scroll={{ x: 1600 }}
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
				<>
					<div style={{ marginBottom: 12, textAlign: "right" }}>
						<Button
							icon={<DownloadOutlined />}
							onClick={() =>
								exportNegativeKeywords(bucketData?.money_pits ?? [])
							}
							disabled={!bucketData?.money_pits?.length}
						>
							导出否定关键词列表
						</Button>
					</div>
					<Table<BucketItem>
						columns={buildBucketColumns(
							"money_pits",
							processedTerms,
							markAsProcessed,
							addToWhitelist,
						)}
						dataSource={bucketData?.money_pits ?? []}
						rowKey={(r) => `${r.campaign_id}-${r.search_term}`}
						loading={loading}
						size="middle"
						scroll={{ x: 1600 }}
						pagination={{ pageSize: 20, showSizeChanger: true }}
						rowClassName={() => "row-red-tint"}
					/>
				</>
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
					columns={buildBucketColumns(
						"low_data",
						processedTerms,
						markAsProcessed,
					)}
					dataSource={bucketData?.low_data ?? []}
					rowKey={(r) => `${r.campaign_id}-${r.search_term}`}
					loading={loading}
					size="middle"
					scroll={{ x: 1600 }}
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
					content={
						<div>
							<p>
								搜索词按 4-Bucket
								框架分类：Winners（高转化词）、Potential（有潜力）、Money
								Pits（浪费预算）、Low Data（数据不足）。
							</p>
							<p style={{ fontWeight: 600, marginTop: 12 }}>
								关键词匹配类型说明：
							</p>
							<ul style={{ paddingLeft: 20 }}>
								<li>
									<strong>Broad（广泛匹配）</strong>
									：词序不限，匹配同义词。关键词可能完全不出现在搜索词中。
								</li>
								<li>
									<strong>Phrase（短语匹配）</strong>
									：必须保持关键词词序。允许前后缀。
								</li>
								<li>
									<strong>Exact（精确匹配）</strong>
									：精确匹配，但也匹配近义词和近似变体。
								</li>
								<li>
									<strong>Negative Phrase（否定短语）</strong>
									：包含该短语即排除。最多 4 词，80 字符。
								</li>
								<li>
									<strong>Negative Exact（否定精确）</strong>
									：完全一致才排除。最多 10 词，80 字符。
								</li>
							</ul>
							<p style={{ marginTop: 12, color: "#faad14" }}>
								否定关键词需 72 小时生效，否定 ASIN 需 96 小时。
							</p>
						</div>
					}
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
					{activeTab === "money_pits" && (
						<Alert
							type="info"
							showIcon
							style={{ marginTop: 16 }}
							title="添加否定关键词后需要 72 小时才能生效（否定 ASIN 需 96 小时）。请耐心等待效果显现。"
						/>
					)}
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
