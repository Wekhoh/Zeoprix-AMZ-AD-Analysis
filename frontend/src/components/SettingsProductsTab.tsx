import {
	Card,
	Input,
	InputNumber,
	Select,
	Space,
	Table,
	Tag,
	message,
} from "antd";
import { CheckCircleOutlined } from "@ant-design/icons";
import api from "../api/client";
import type { BenchmarkCategory } from "../types/api";

export interface VariantItem {
	id: number;
	variant_code: string;
	variant_name: string;
	asin: string | null;
	unit_cost: number | null;
	fba_fee: number | null;
	referral_fee_pct: number | null;
}

export interface ProductItem {
	id: number;
	sku: string;
	name: string;
	category: string;
	category_key: string | null;
	variants: VariantItem[];
}

interface SettingsProductsTabProps {
	products: ProductItem[];
	categories: BenchmarkCategory[];
	onRefresh: () => void;
}

const QUALIFICATION_RULES = [
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
];

/**
 * 产品管理 tab — per-product card with editable variant cost fields
 * (ASIN / unit_cost / fba_fee / referral_fee_pct) and a category-key
 * selector for benchmark comparison. Extracted from Settings.tsx (F3-β).
 */
export default function SettingsProductsTab({
	products,
	categories,
	onRefresh,
}: SettingsProductsTabProps) {
	const handleUpdateVariantCost = async (
		variantId: number,
		field: string,
		value: string | number | null,
	) => {
		try {
			await api.put(`/settings/products/${variantId}`, { [field]: value });
			message.success("已保存");
			onRefresh();
		} catch {
			message.error("保存失败");
		}
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
			onRefresh();
		} catch {
			message.error("更新失败");
		}
	};

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

	return (
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
				{QUALIFICATION_RULES.map((rule) => (
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
						<CheckCircleOutlined style={{ color: "#52c41a", marginTop: 3 }} />
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
	);
}
