import { useEffect, useState } from "react";
import {
	Tabs,
	Card,
	Button,
	Table,
	message,
	Popconfirm,
	Space,
	Tag,
	Spin,
	InputNumber,
	Modal,
	DatePicker,
	Input,
	Select,
} from "antd";
import {
	CheckCircleOutlined,
	CloudUploadOutlined,
	DeleteOutlined,
	DatabaseOutlined,
	ShopOutlined,
	DollarOutlined,
	PlusOutlined,
	HistoryOutlined,
} from "@ant-design/icons";
import dayjs from "dayjs";
import api from "../api/client";
import PageHelp from "../components/PageHelp";
import type { OrganicSalesRecord, BenchmarkCategory } from "../types/api";

interface BackupItem {
	id: number;
	file_path: string;
	file_size: number;
	backup_type: string;
	created_at: string;
}

interface VariantItem {
	id: number;
	variant_code: string;
	variant_name: string;
	asin: string | null;
	unit_cost: number | null;
	fba_fee: number | null;
	referral_fee_pct: number | null;
}

interface ProductItem {
	id: number;
	sku: string;
	name: string;
	category: string;
	category_key: string | null;
	variants: VariantItem[];
}

interface ImportHistoryItem {
	id: number;
	import_type: string;
	file_name: string | null;
	records_imported: number;
	records_updated: number;
	records_skipped: number;
	status: string;
	created_at: string;
}

const IMPORT_TYPE_LABELS: Record<string, string> = {
	placement_csv: "展示位置 CSV",
	operation_log: "操作日志",
	search_term: "搜索词报告",
	migration: "数据迁移",
};

const IMPORT_STATUS_COLORS: Record<string, string> = {
	success: "green",
	partial: "orange",
	error: "red",
};

export default function Settings() {
	const [backups, setBackups] = useState<BackupItem[]>([]);
	const [products, setProducts] = useState<ProductItem[]>([]);
	const [organicSales, setOrganicSales] = useState<OrganicSalesRecord[]>([]);
	const [categories, setCategories] = useState<BenchmarkCategory[]>([]);
	const [importHistory, setImportHistory] = useState<ImportHistoryItem[]>([]);
	const [loading, setLoading] = useState(true);
	const [backupLoading, setBackupLoading] = useState(false);
	const [salesModalOpen, setSalesModalOpen] = useState(false);
	const [salesForm, setSalesForm] = useState({
		date: "",
		total_sales: 0,
		total_orders: 0,
		notes: "",
	});

	const fetchData = () => {
		setLoading(true);
		Promise.all([
			api.get<BackupItem[]>("/settings/backups"),
			api.get<ProductItem[]>("/settings/products"),
			api.get<OrganicSalesRecord[]>("/settings/organic-sales"),
			api.get<BenchmarkCategory[]>("/benchmarks/categories"),
			api.get<ImportHistoryItem[]>("/settings/import-history"),
		]).then(([b, p, s, c, h]) => {
			setBackups(b.data);
			setProducts(p.data);
			setOrganicSales(s.data);
			setCategories(c.data);
			setImportHistory(h.data);
			setLoading(false);
		});
	};

	useEffect(fetchData, []);

	const handleCreateBackup = async () => {
		setBackupLoading(true);
		try {
			await api.post("/settings/backups");
			message.success("备份创建成功");
			fetchData();
		} catch {
			message.error("备份失败");
		} finally {
			setBackupLoading(false);
		}
	};

	const handleDeleteBackup = async (id: number) => {
		await api.delete(`/settings/backups/${id}`);
		message.success("备份已删除");
		fetchData();
	};

	const handleUpdateVariantCost = async (
		variantId: number,
		field: string,
		value: string | number | null,
	) => {
		try {
			await api.put(`/settings/products/${variantId}`, { [field]: value });
			message.success("已保存");
			fetchData();
		} catch {
			message.error("保存失败");
		}
	};

	const handleAddOrganicSales = async () => {
		if (!salesForm.date) {
			message.warning("请选择日期");
			return;
		}
		try {
			await api.post("/settings/organic-sales", [salesForm]);
			message.success("销售数据已保存");
			setSalesModalOpen(false);
			setSalesForm({ date: "", total_sales: 0, total_orders: 0, notes: "" });
			fetchData();
		} catch {
			message.error("保存失败");
		}
	};

	const handleDeleteOrganicSales = async (id: number) => {
		await api.delete(`/settings/organic-sales/${id}`);
		message.success("记录已删除");
		fetchData();
	};

	const handleUpdateCategoryKey = async (
		productId: number,
		categoryKey: string | null,
	) => {
		try {
			await api.put(`/settings/products/${productId}/category-key`, {
				category_key: categoryKey,
			});
			message.success("品类已更新");
			fetchData();
		} catch {
			message.error("更新失败");
		}
	};

	const formatSize = (bytes: number) => {
		if (bytes < 1024) return `${bytes} B`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
		return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
	};

	const backupColumns = [
		{ title: "文件名", dataIndex: "file_path", key: "file" },
		{
			title: "大小",
			dataIndex: "file_size",
			key: "size",
			render: (v: number) => formatSize(v),
			width: 100,
		},
		{
			title: "类型",
			dataIndex: "backup_type",
			key: "type",
			width: 80,
			render: (t: string) => (
				<Tag color={t === "auto" ? "blue" : "green"}>
					{t === "auto" ? "自动" : "手动"}
				</Tag>
			),
		},
		{ title: "创建时间", dataIndex: "created_at", key: "time", width: 180 },
		{
			title: "操作",
			key: "action",
			width: 80,
			render: (_: unknown, record: BackupItem) => (
				<Popconfirm
					title="确定删除此备份？"
					onConfirm={() => handleDeleteBackup(record.id)}
				>
					<Button type="text" danger icon={<DeleteOutlined />} size="small" />
				</Popconfirm>
			),
		},
	];

	const variantColumns = [
		{
			title: "变体代码",
			dataIndex: "variant_code",
			key: "code",
			width: 120,
			render: (v: string, record: VariantItem) => (
				<Input
					defaultValue={v}
					size="small"
					style={{ width: 100 }}
					onBlur={(e) => {
						if (e.target.value !== v) {
							handleUpdateVariantCost(
								record.id,
								"variant_code",
								e.target.value,
							);
						}
					}}
					onPressEnter={(e) => (e.target as HTMLInputElement).blur()}
				/>
			),
		},
		{
			title: "变体名称",
			dataIndex: "variant_name",
			key: "name",
			render: (v: string, record: VariantItem) => (
				<Input
					defaultValue={v}
					size="small"
					style={{ width: 120 }}
					onBlur={(e) => {
						if (e.target.value !== v) {
							handleUpdateVariantCost(
								record.id,
								"variant_name",
								e.target.value,
							);
						}
					}}
					onPressEnter={(e) => (e.target as HTMLInputElement).blur()}
				/>
			),
		},
		{
			title: "ASIN",
			dataIndex: "asin",
			key: "asin",
			width: 140,
			render: (v: string | null, record: VariantItem) => (
				<Input
					defaultValue={v || ""}
					size="small"
					style={{ width: 130 }}
					placeholder="B0XXXXXXXX"
					onBlur={(e) => {
						const newVal = e.target.value || null;
						if (newVal !== v) {
							handleUpdateVariantCost(record.id, "asin", newVal);
						}
					}}
					onPressEnter={(e) => (e.target as HTMLInputElement).blur()}
				/>
			),
		},
		{
			title: "产品成本 ($)",
			dataIndex: "unit_cost",
			key: "unit_cost",
			width: 130,
			render: (v: number | null, record: VariantItem) => (
				<InputNumber
					value={v}
					min={0}
					step={0.01}
					precision={2}
					size="small"
					style={{ width: 110 }}
					placeholder="0.00"
					onBlur={(e) => {
						const newVal = e.target.value ? parseFloat(e.target.value) : null;
						if (newVal !== v) {
							handleUpdateVariantCost(record.id, "unit_cost", newVal);
						}
					}}
				/>
			),
		},
		{
			title: "FBA 费用 ($)",
			dataIndex: "fba_fee",
			key: "fba_fee",
			width: 130,
			render: (v: number | null, record: VariantItem) => (
				<InputNumber
					value={v}
					min={0}
					step={0.01}
					precision={2}
					size="small"
					style={{ width: 110 }}
					placeholder="0.00"
					onBlur={(e) => {
						const newVal = e.target.value ? parseFloat(e.target.value) : null;
						if (newVal !== v) {
							handleUpdateVariantCost(record.id, "fba_fee", newVal);
						}
					}}
				/>
			),
		},
		{
			title: "佣金比例",
			dataIndex: "referral_fee_pct",
			key: "referral_fee_pct",
			width: 130,
			render: (v: number | null, record: VariantItem) => (
				<InputNumber
					value={v != null ? v * 100 : null}
					min={0}
					max={100}
					step={0.5}
					precision={1}
					size="small"
					style={{ width: 110 }}
					placeholder="15.0"
					suffix="%"
					onBlur={(e) => {
						const raw = e.target.value
							? parseFloat(e.target.value) / 100
							: null;
						const current = v;
						if (raw !== current) {
							handleUpdateVariantCost(record.id, "referral_fee_pct", raw);
						}
					}}
				/>
			),
		},
	];

	const organicSalesColumns = [
		{ title: "日期", dataIndex: "date", key: "date", width: 120 },
		{
			title: "总销售额 ($)",
			dataIndex: "total_sales",
			key: "total_sales",
			render: (v: number) => `$${v?.toFixed(2)}`,
		},
		{ title: "总订单数", dataIndex: "total_orders", key: "total_orders" },
		{
			title: "备注",
			dataIndex: "notes",
			key: "notes",
			render: (v: string | null) => v || "-",
		},
		{
			title: "操作",
			key: "action",
			width: 80,
			render: (_: unknown, record: OrganicSalesRecord) => (
				<Popconfirm
					title="确定删除此记录？"
					onConfirm={() => handleDeleteOrganicSales(record.id)}
				>
					<Button type="text" danger icon={<DeleteOutlined />} size="small" />
				</Popconfirm>
			),
		},
	];

	const tabs = [
		{
			key: "backup",
			label: (
				<span>
					<DatabaseOutlined /> 数据备份
				</span>
			),
			children: (
				<div>
					<Space style={{ marginBottom: 16 }}>
						<Button
							type="primary"
							icon={<CloudUploadOutlined />}
							onClick={handleCreateBackup}
							loading={backupLoading}
						>
							创建备份
						</Button>
					</Space>
					<Table
						columns={backupColumns}
						dataSource={backups}
						rowKey="id"
						size="small"
						pagination={false}
						locale={{ emptyText: "暂无备份，点击上方按钮创建" }}
					/>
				</div>
			),
		},
		{
			key: "products",
			label: (
				<span>
					<ShopOutlined /> 产品管理
				</span>
			),
			children: (
				<div>
					{products.map((p) => (
						<Card
							key={p.id}
							title={`${p.sku} - ${p.name}`}
							size="small"
							style={{ marginBottom: 16 }}
							extra={
								<Space>
									<Select
										placeholder="选择品类基准"
										allowClear
										style={{ width: 160 }}
										value={p.category_key ?? undefined}
										onChange={(val: string | undefined) =>
											handleUpdateCategoryKey(p.id, val ?? null)
										}
										options={categories.map((c) => ({
											value: c.key,
											label: c.label,
										}))}
									/>
									<Tag>{p.category}</Tag>
								</Space>
							}
						>
							<Table
								columns={variantColumns}
								dataSource={p.variants}
								rowKey="id"
								size="small"
								pagination={false}
							/>
						</Card>
					))}
					<Card title="广告资格检查清单" size="small" style={{ marginTop: 24 }}>
						{[
							{
								item: "专业卖家账户",
								description: "必须是 Professional Seller 账户",
							},
							{ item: "账户信誉良好", description: "无严重违规或欠款" },
							{
								item: "Buy Box 资格",
								description: "受定价、库存、配送速度、客户评价影响",
							},
							{ item: "商品有库存", description: "FBA 或 FBM 库存 > 0" },
							{
								item: "Listing 标题合规",
								description: "<= 200 字符，无特殊字符堆砌",
							},
							{ item: "无违规标记", description: "商品未被限制或下架" },
						].map((rule) => (
							<div
								key={rule.item}
								style={{
									display: "flex",
									alignItems: "flex-start",
									gap: 8,
									padding: "8px 0",
									borderBottom: "1px solid rgba(128,128,128,0.15)",
								}}
							>
								<CheckCircleOutlined
									style={{ color: "#52c41a", marginTop: 3 }}
								/>
								<div>
									<div style={{ fontWeight: 500 }}>{rule.item}</div>
									<div style={{ fontSize: 12, opacity: 0.7 }}>
										{rule.description}
									</div>
								</div>
							</div>
						))}
					</Card>
				</div>
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
				<div>
					<Space style={{ marginBottom: 16 }}>
						<Button
							type="primary"
							icon={<PlusOutlined />}
							onClick={() => setSalesModalOpen(true)}
						>
							添加
						</Button>
					</Space>
					<Table
						columns={organicSalesColumns}
						dataSource={organicSales}
						rowKey="id"
						size="small"
						pagination={{ pageSize: 20 }}
						locale={{ emptyText: "暂无销售数据，用于计算 TACoS" }}
					/>
					<Modal
						title="添加销售数据"
						open={salesModalOpen}
						onOk={handleAddOrganicSales}
						onCancel={() => setSalesModalOpen(false)}
						okText="保存"
						cancelText="取消"
					>
						<div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
							<div>
								<div style={{ marginBottom: 4 }}>日期</div>
								<DatePicker
									style={{ width: "100%" }}
									onChange={(d) =>
										setSalesForm((prev) => ({
											...prev,
											date: d ? d.format("YYYY-MM-DD") : "",
										}))
									}
									value={salesForm.date ? dayjs(salesForm.date) : null}
								/>
							</div>
							<div>
								<div style={{ marginBottom: 4 }}>总销售额 ($)</div>
								<InputNumber
									style={{ width: "100%" }}
									min={0}
									step={0.01}
									precision={2}
									value={salesForm.total_sales}
									onChange={(v) =>
										setSalesForm((prev) => ({
											...prev,
											total_sales: v ?? 0,
										}))
									}
								/>
							</div>
							<div>
								<div style={{ marginBottom: 4 }}>总订单数</div>
								<InputNumber
									style={{ width: "100%" }}
									min={0}
									step={1}
									precision={0}
									value={salesForm.total_orders}
									onChange={(v) =>
										setSalesForm((prev) => ({
											...prev,
											total_orders: v ?? 0,
										}))
									}
								/>
							</div>
							<div>
								<div style={{ marginBottom: 4 }}>备注</div>
								<Input
									value={salesForm.notes}
									onChange={(e) =>
										setSalesForm((prev) => ({
											...prev,
											notes: e.target.value,
										}))
									}
								/>
							</div>
						</div>
					</Modal>
				</div>
			),
		},
		{
			key: "import-history",
			label: (
				<span>
					<HistoryOutlined /> 导入历史
				</span>
			),
			children: (
				<Table
					columns={[
						{
							title: "时间",
							dataIndex: "created_at",
							key: "time",
							width: 180,
						},
						{
							title: "类型",
							dataIndex: "import_type",
							key: "type",
							width: 140,
							render: (v: string) => (
								<Tag color="blue">{IMPORT_TYPE_LABELS[v] ?? v}</Tag>
							),
						},
						{
							title: "文件名",
							dataIndex: "file_name",
							key: "file",
							ellipsis: true,
							render: (v: string | null) => v ?? "-",
						},
						{
							title: "新增",
							dataIndex: "records_imported",
							key: "imported",
							width: 80,
						},
						{
							title: "更新",
							dataIndex: "records_updated",
							key: "updated",
							width: 80,
						},
						{
							title: "跳过",
							dataIndex: "records_skipped",
							key: "skipped",
							width: 80,
						},
						{
							title: "状态",
							dataIndex: "status",
							key: "status",
							width: 80,
							render: (v: string) => (
								<Tag color={IMPORT_STATUS_COLORS[v] ?? "default"}>
									{v === "success" ? "成功" : v === "error" ? "失败" : v}
								</Tag>
							),
						},
					]}
					dataSource={importHistory}
					rowKey="id"
					size="small"
					pagination={{ pageSize: 20 }}
					locale={{ emptyText: "暂无导入记录" }}
				/>
			),
		},
	];

	return (
		<Spin spinning={loading}>
			<div style={{ display: "flex", alignItems: "center", marginBottom: 16 }}>
				<span style={{ fontSize: 16, fontWeight: 600 }}>系统设置</span>
				<PageHelp
					title="系统设置帮助"
					content="管理产品成本信息（用于利润计算）、数据备份、有机销售数据和导入历史。"
				/>
			</div>
			<Tabs items={tabs} />
		</Spin>
	);
}
