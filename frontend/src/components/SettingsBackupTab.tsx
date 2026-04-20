import { useState } from "react";
import { Button, Popconfirm, Space, Table, Tag, message } from "antd";
import { CloudUploadOutlined, DeleteOutlined } from "@ant-design/icons";
import api from "../api/client";

export interface BackupItem {
	id: number;
	file_path: string;
	file_size: number;
	backup_type: string;
	created_at: string;
}

interface SettingsBackupTabProps {
	backups: BackupItem[];
	onRefresh: () => void;
}

const formatSize = (bytes: number) => {
	if (bytes < 1024) return `${bytes} B`;
	if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
	return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

/**
 * 数据备份 tab — create / delete / list backups.
 * Extracted from Settings.tsx (F3-α).
 */
export default function SettingsBackupTab({
	backups,
	onRefresh,
}: SettingsBackupTabProps) {
	const [backupLoading, setBackupLoading] = useState(false);

	const handleCreateBackup = async () => {
		setBackupLoading(true);
		try {
			await api.post("/settings/backups");
			message.success("备份创建成功");
			onRefresh();
		} catch {
			message.error("备份失败");
		} finally {
			setBackupLoading(false);
		}
	};

	const handleDeleteBackup = async (id: number) => {
		await api.delete(`/settings/backups/${id}`);
		message.success("备份已删除");
		onRefresh();
	};

	const columns = [
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
					icon={<CloudUploadOutlined />}
					onClick={handleCreateBackup}
					loading={backupLoading}
				>
					创建备份
				</Button>
			</Space>
			<Table
				columns={columns}
				dataSource={backups}
				rowKey="id"
				size="small"
				pagination={false}
				locale={{ emptyText: "暂无备份，点击上方按钮创建" }}
			/>
		</div>
	);
}
