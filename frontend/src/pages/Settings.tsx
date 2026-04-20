import { useEffect, useState } from "react";
import { Tabs } from "antd";
import {
	ClearOutlined,
	DatabaseOutlined,
	DollarOutlined,
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
import SettingsDataManageTab from "../components/SettingsDataManageTab";
import type { OrganicSalesRecord, BenchmarkCategory } from "../types/api";

export default function Settings() {
	const [backups, setBackups] = useState<BackupItem[]>([]);
	const [products, setProducts] = useState<ProductItem[]>([]);
	const [organicSales, setOrganicSales] = useState<OrganicSalesRecord[]>([]);
	const [categories, setCategories] = useState<BenchmarkCategory[]>([]);
	const [importHistory, setImportHistory] = useState<ImportHistoryItem[]>([]);
	const [loading, setLoading] = useState(true);
	const [dataStats, setDataStats] = useState<Record<string, number>>({});

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

	// eslint-disable-next-line react-hooks/set-state-in-effect -- canonical fetch-reset: clear loading state before the 6-endpoint Promise.all; same pattern as Campaigns.tsx / CampaignDetail.tsx
	useEffect(fetchData, []);

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
				<SettingsDataManageTab dataStats={dataStats} onRefresh={fetchData} />
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
