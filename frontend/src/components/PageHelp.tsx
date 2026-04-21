import { useState } from "react";
import { Button, Drawer } from "antd";
import { QuestionCircleOutlined } from "@ant-design/icons";
import { useTheme } from "../hooks/useTheme";
import type { ReactNode } from "react";

interface PageHelpProps {
	title: string;
	content: ReactNode;
}

export default function PageHelp({ title, content }: PageHelpProps) {
	const [open, setOpen] = useState(false);
	const { isDark } = useTheme();

	return (
		<>
			<Button
				type="text"
				shape="circle"
				size="small"
				icon={
					<QuestionCircleOutlined
						style={{ color: isDark ? "#6B7280" : "#9CA3AF", fontSize: 16 }}
					/>
				}
				onClick={() => setOpen(true)}
				style={{ marginLeft: 8 }}
				aria-label="页面帮助"
			/>
			<Drawer
				title={title}
				placement="right"
				size={400}
				onClose={() => setOpen(false)}
				open={open}
			>
				<div
					style={{
						fontSize: 14,
						lineHeight: 1.8,
						color: isDark ? "#D1D5DB" : "#374151",
					}}
				>
					{content}
				</div>
			</Drawer>
		</>
	);
}
