import { useState } from "react";
import { Button, Card, Input, Modal, message } from "antd";
import { DeleteOutlined, ExclamationCircleOutlined } from "@ant-design/icons";
import api from "../api/client";

interface SettingsDataManageTabProps {
	dataStats: Record<string, number>;
	onRefresh: () => void;
}

const STAT_ROWS: Array<[string, string]> = [
	["广告活动", "campaigns"],
	["广告组", "ad_groups"],
	["展示位置记录", "placement_records"],
	["操作日志", "operation_logs"],
	["活动日报", "campaign_daily"],
	["广告组日报", "ad_group_daily"],
	["搜索词报告", "search_terms"],
	["笔记", "notes"],
	["有机销售", "organic_sales"],
	["导入历史", "import_history"],
];

/**
 * 数据管理 tab — stats summary + danger-zone clear-data modal with typed
 * confirmation. Clear endpoint auto-creates a backup first, so no data
 * loss risk. Extracted from Settings.tsx (F3-γ, final F3 step).
 */
export default function SettingsDataManageTab({
	dataStats,
	onRefresh,
}: SettingsDataManageTabProps) {
	const [confirmText, setConfirmText] = useState("");
	const [modalOpen, setModalOpen] = useState(false);
	const [loading, setLoading] = useState(false);

	const handleClear = async () => {
		setLoading(true);
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
			setModalOpen(false);
			setConfirmText("");
			onRefresh();
		} catch {
			message.error("清空数据失败");
		} finally {
			setLoading(false);
		}
	};

	return (
		<div>
			<Card title="数据统计" size="small" style={{ marginBottom: 24 }}>
				<table style={{ width: "100%", borderCollapse: "collapse" }}>
					<tbody>
						{STAT_ROWS.map(([label, key]) => (
							<tr key={key}>
								<td style={{ padding: "6px 12px" }}>{label}</td>
								<td
									style={{
										padding: "6px 12px",
										fontWeight: 600,
										textAlign: "right",
									}}
								>
									{dataStats[key]?.toLocaleString() ?? 0}
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
					onClick={() => setModalOpen(true)}
				>
					清空广告数据
				</Button>
			</Card>
			<Modal
				title="确认清空所有广告数据"
				open={modalOpen}
				onCancel={() => {
					setModalOpen(false);
					setConfirmText("");
				}}
				footer={[
					<Button
						key="cancel"
						onClick={() => {
							setModalOpen(false);
							setConfirmText("");
						}}
					>
						取消
					</Button>,
					<Button
						key="confirm"
						danger
						type="primary"
						loading={loading}
						disabled={confirmText !== "确认清空"}
						onClick={handleClear}
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
					value={confirmText}
					onChange={(e) => setConfirmText(e.target.value)}
					placeholder="确认清空"
				/>
			</Modal>
		</div>
	);
}
