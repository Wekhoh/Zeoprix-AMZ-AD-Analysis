import { useState } from "react";
import {
	Button,
	DatePicker,
	Input,
	InputNumber,
	Modal,
	Popconfirm,
	Space,
	Table,
	message,
} from "antd";
import { DeleteOutlined, PlusOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import api from "../api/client";
import type { OrganicSalesRecord } from "../types/api";

interface SettingsOrganicSalesTabProps {
	sales: OrganicSalesRecord[];
	onRefresh: () => void;
}

interface SalesForm {
	date: string;
	total_sales: number;
	total_orders: number;
	notes: string;
}

const EMPTY_FORM: SalesForm = {
	date: "",
	total_sales: 0,
	total_orders: 0,
	notes: "",
};

/**
 * 销售数据 tab — list organic/total sales rows (feeds TACoS) with an Add
 * Modal for new entries and soft delete. Extracted from Settings.tsx
 * (F3-β).
 */
export default function SettingsOrganicSalesTab({
	sales,
	onRefresh,
}: SettingsOrganicSalesTabProps) {
	const [modalOpen, setModalOpen] = useState(false);
	const [form, setForm] = useState<SalesForm>(EMPTY_FORM);

	const handleAdd = async () => {
		if (!form.date) {
			message.warning("请选择日期");
			return;
		}
		try {
			await api.post("/settings/organic-sales", [form]);
			message.success("销售数据已保存");
			setModalOpen(false);
			setForm(EMPTY_FORM);
			onRefresh();
		} catch {
			message.error("保存失败");
		}
	};

	const handleDelete = async (id: number) => {
		await api.delete(`/settings/organic-sales/${id}`);
		message.success("记录已删除");
		onRefresh();
	};

	const columns = [
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
					onConfirm={() => handleDelete(record.id)}
				>
					<Button
						type="text"
						danger
						icon={<DeleteOutlined />}
						size="small"
						aria-label="删除"
					/>
				</Popconfirm>
			),
		},
	];

	return (
		<div>
			<Space style={{ marginBottom: 16 }}>
				<Button
					type="primary"
					icon={<PlusOutlined />}
					onClick={() => setModalOpen(true)}
				>
					添加
				</Button>
			</Space>
			<Table
				columns={columns}
				dataSource={sales}
				rowKey="id"
				size="small"
				pagination={{ pageSize: 20 }}
				locale={{ emptyText: "暂无销售数据，用于计算 TACoS" }}
			/>
			<Modal
				title="添加销售数据"
				open={modalOpen}
				onOk={handleAdd}
				onCancel={() => setModalOpen(false)}
				okText="保存"
				cancelText="取消"
			>
				<div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
					<div>
						<div style={{ marginBottom: 4 }}>日期</div>
						<DatePicker
							style={{ width: "100%" }}
							onChange={(d) =>
								setForm((prev) => ({
									...prev,
									date: d ? d.format("YYYY-MM-DD") : "",
								}))
							}
							value={form.date ? dayjs(form.date) : null}
						/>
					</div>
					<div>
						<div style={{ marginBottom: 4 }}>总销售额 ($)</div>
						<InputNumber
							style={{ width: "100%" }}
							min={0}
							step={0.01}
							precision={2}
							value={form.total_sales}
							onChange={(v) =>
								setForm((prev) => ({
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
							value={form.total_orders}
							onChange={(v) =>
								setForm((prev) => ({
									...prev,
									total_orders: v ?? 0,
								}))
							}
						/>
					</div>
					<div>
						<div style={{ marginBottom: 4 }}>备注</div>
						<Input
							value={form.notes}
							onChange={(e) =>
								setForm((prev) => ({
									...prev,
									notes: e.target.value,
								}))
							}
						/>
					</div>
				</div>
			</Modal>
		</div>
	);
}
