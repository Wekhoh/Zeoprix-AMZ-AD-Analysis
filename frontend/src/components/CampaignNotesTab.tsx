import { useState } from "react";
import { Button, Input, List, Popconfirm, Space, message } from "antd";
import { DeleteOutlined } from "@ant-design/icons";
import api from "../api/client";

export interface CampaignNote {
	id: number;
	content: string;
	note_type: string;
	created_at: string | null;
}

interface CampaignNotesTabProps {
	campaignId: string;
	notes: CampaignNote[];
	onChange: () => void;
}

/**
 * Notes tab for CampaignDetail — input + list + soft-delete with undo.
 * Extracted from CampaignDetail.tsx Section D notes tab (F2-γ1).
 */
export default function CampaignNotesTab({
	campaignId,
	notes,
	onChange,
}: CampaignNotesTabProps) {
	const [newNote, setNewNote] = useState("");

	const handleAddNote = async () => {
		if (!newNote.trim()) return;
		await api.post("/notes", {
			campaign_id: Number(campaignId),
			content: newNote.trim(),
			note_type: "decision",
		});
		setNewNote("");
		message.success("笔记已添加");
		onChange();
	};

	const handleDeleteNote = async (noteId: number) => {
		try {
			await api.delete(`/notes/${noteId}`);
			onChange();
			message.open({
				type: "success",
				content: (
					<span>
						笔记已删除{" "}
						<Button
							type="link"
							size="small"
							style={{ padding: 0, marginLeft: 8 }}
							onClick={async () => {
								try {
									await api.post(`/notes/${noteId}/restore`);
									message.success("已恢复");
									onChange();
								} catch {
									message.error("恢复失败，笔记可能已被永久删除");
								}
							}}
						>
							撤销
						</Button>
					</span>
				),
				duration: 5,
			});
		} catch {
			message.error("删除失败");
		}
	};

	return (
		<div>
			<Space.Compact style={{ width: "100%", marginBottom: 16 }}>
				<Input
					placeholder="记录优化决策、观察、提醒..."
					value={newNote}
					onChange={(e) => setNewNote(e.target.value)}
					onPressEnter={handleAddNote}
				/>
				<Button type="primary" onClick={handleAddNote}>
					添加笔记
				</Button>
			</Space.Compact>
			<List
				dataSource={notes}
				locale={{ emptyText: "暂无笔记" }}
				renderItem={(note) => (
					<List.Item
						actions={[
							<Popconfirm
								key="del"
								title="确定删除？"
								onConfirm={() => handleDeleteNote(note.id)}
							>
								<Button
									type="text"
									danger
									icon={<DeleteOutlined />}
									size="small"
									aria-label="删除笔记"
								/>
							</Popconfirm>,
						]}
					>
						<List.Item.Meta
							title={note.content}
							description={note.created_at ? note.created_at.slice(0, 19) : ""}
						/>
					</List.Item>
				)}
			/>
		</div>
	);
}
