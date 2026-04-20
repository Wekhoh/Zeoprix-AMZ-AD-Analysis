import { useEffect, useState } from "react";
import { Button, Card, Input, Modal, Tabs, message } from "antd";
import {
	ClearOutlined,
	DatabaseOutlined,
	DeleteOutlined,
	DollarOutlined,
	ExclamationCircleOutlined,
	HistoryOutlined,
	ShopOutlined,
} from "@ant-design/icons";
import api from "../api/client";
import PageHelp from "../components/PageHelp";
import PageSkeleton from "../components/PageSkeleton";
import SettingsBackupTab, {
	type BackupItem,
} from "../components/SettingsBackupTab";
import SettingsImportHistoryTab, {
	type ImportHistoryItem,
} from "../components/SettingsImportHistoryTab";
import SettingsProductsTab, {
	type ProductItem,
} from "../components/SettingsProductsTab";
import SettingsOrganicSalesTab from "../components/SettingsOrganicSalesTab";
import type { OrganicSalesRecord, BenchmarkCategory } from "../types/api";

export default function Settings() {
	const [backups, setBackups] = useState<BackupItem[]>([]);
	const [products, setProducts] = useState<ProductItem[]>([]);
	const [organicSales, setOrganicSales] = useState<OrganicSalesRecord[]>([]);
	const [categories, setCategories] = useState<BenchmarkCategory[]>([]);
	const [importHistory, setImportHistory] = useState<ImportHistoryItem[]>([]);
	const [loading, setLoading] = useState(true);
	const [dataStats, setDataStats] = useState<Record<string, number>>({});
	const [clearConfirmText, setClearConfirmText] = useState("");
	const [clearModalOpen, setClearModalOpen] = useState(false);
	const [clearLoading, setClearLoading] = useState(false);

	const fetchData = () => {
		setLoading(true);
		Promise.all([
			api.get<BackupItem[]>("/settings/backups"),
			api.get<ProductItem[]>("/settings/products"),
			api.get<OrganicSalesRecord[]>("/settings/organic-sales"),
			api.get<BenchmarkCategory[]>("/benchmarks/categories"),
			api.get<ImportHistoryItem[]>("/settings/import-history"),
			api.get<Record<string, number>>("/settings/data-stats"),
		])
			.then(([b, p, s, c, h, stats]) => {
				setBackups(b.data);
				setProducts(p.data);
				setOrganicSales(s.data);
				setCategories(c.data);
				setImportHistory(h.data);
				setDataStats(stats.data);
			})
			.catch(() => {})
			.finally(() => setLoading(false));
	};

	useEffect(fetchData, []);

	const handleClearData = async () => {
		setClearLoading(true);
		try {
			const res = await api.delete<{
				success: boolean;
				deleted: Record<string, number>;
				backup_id: number;
			}>("/settings/clear-data");
			const total = Object.values(res.data.deleted).reduce((s, n) => s + n, 0);
			message.success(
				`已清空 ${total} 条数据（备份 #${res.data.backup_id} 已自动创建）`,
			);
			setClearModalOpen(false);
			setClearConfirmText("");
			fetchData();
		} catch {
			message.error("清空数据失败");
		} finally {
			setClearLoading(false);
		}
	};

	const tabs = [
		{
			key: "backup",
			label: (
				<span>
					<DatabaseOutlined /> 数据备份
				</span>
			),
			children: <SettingsBackupTab backups={backups} onRefresh={fetchData} />,
		},
		{
			key: "products",
			label: (
				<span>
					<ShopOutlined /> 产品管理
				</span>
			),
			children: (
				<SettingsProductsTab
					products={products}
					categories={categories}
					onRefresh={fetchData}
				/>
			),
		},
		{
			key: "organic-sales",
			label: (
				<span>
					<DollarOutlined /> 销售数据
				</span>
			),
			children: (
				<SettingsOrganicSalesTab sales={organicSales} onRefresh={fetchData} />
			),
		},
		{
			key: "import-history",
			label: (
				<span>
					<HistoryOutlined /> 导入历史
				</span>
			),
			children: <SettingsImportHistoryTab history={importHistory} />,
		},
		{
			key: "data-manage",
			label: (
				<span>
					<ClearOutlined /> 数据管理
				</span>
			),
			children: (
				<div>
					<Card title="数据统计" size="small" style={{ marginBottom: 24 }}>
						<table style={{ width: "100%", borderCollapse: "collapse" }}>
							<tbody>
								{[
									["广告活动", dataStats.campaigns],
									["广告组", dataStats.ad_groups],
									["展示位置记录", dataStats.placement_records],
									["操作日志", dataStats.operation_logs],
									["活动日报", dataStats.campaign_daily],
									["广告组日报", dataStats.ad_group_daily],
									["搜索词报告", dataStats.search_terms],
									["笔记", dataStats.notes],
									["有机销售", dataStats.organic_sales],
									["导入历史", dataStats.import_history],
								].map(([label, count]) => (
									<tr key={String(label)}>
										<td style={{ padding: "6px 12px" }}>{label}</td>
										<td
											style={{
												padding: "6px 12px",
												fontWeight: 600,
												textAlign: "right",
											}}
										>
											{(count as number)?.toLocaleString() ?? 0}
										</td>
									</tr>
								))}
							</tbody>
						</table>
					</Card>
					<Card
						title={
							<span style={{ color: "#ff4d4f" }}>
								<ExclamationCircleOutlined /> 危险操作
							</span>
						}
						size="small"
					>
						<p style={{ marginBottom: 16, color: "#9CA3AF" }}>
							清空所有广告数据（活动、展示位置、搜索词、操作日志、有机销售等）。
							产品配置、自动化规则和备份文件将被保留。清空前会自动创建备份。
						</p>
						<Button
							danger
							icon={<DeleteOutlined />}
							onClick={() => setClearModalOpen(true)}
						>
							清空广告数据
						</Button>
					</Card>
					<Modal
						title="确认清空所有广告数据"
						open={clearModalOpen}
						onCancel={() => {
							setClearModalOpen(false);
							setClearConfirmText("");
						}}
						footer={[
							<Button
								key="cancel"
								onClick={() => {
									setClearModalOpen(false);
									setClearConfirmText("");
								}}
							>
								取消
							</Button>,
							<Button
								key="confirm"
								danger
								type="primary"
								loading={clearLoading}
								disabled={clearConfirmText !== "确认清空"}
								onClick={handleClearData}
							>
								确认清空
							</Button>,
						]}
					>
						<p>此操作将删除以下所有数据：</p>
						<ul style={{ paddingLeft: 20, marginBottom: 16 }}>
							<li>广告活动及广告组</li>
							<li>展示位置记录、活动/广告组日报</li>
							<li>搜索词报告</li>
							<li>操作日志、笔记</li>
							<li>有机销售数据、导入历史</li>
						</ul>
						<p style={{ fontWeight: 600, marginBottom: 8 }}>
							请输入「确认清空」以继续：
						</p>
						<Input
							value={clearConfirmText}
							onChange={(e) => setClearConfirmText(e.target.value)}
							placeholder="确认清空"
						/>
					</Modal>
				</div>
			),
		},
	];

	if (loading) return <PageSkeleton variant="cards" />;

	return (
		<div>
			<div style={{ display: "flex", alignItems: "center", marginBottom: 16 }}>
				<span style={{ fontSize: 16, fontWeight: 600 }}>系统设置</span>
				<PageHelp
					title="系统设置帮助"
					content="管理产品成本信息（用于利润计算）、数据备份、有机销售数据和导入历史。"
				/>
			</div>
			<Tabs items={tabs} />
		</div>
	);
}
