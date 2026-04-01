import type { ReactNode } from "react";
import { Empty, Button } from "antd";

interface EmptyStateProps {
	title: string;
	description?: string;
	actionText?: string;
	onAction?: () => void;
	icon?: ReactNode;
}

export default function EmptyState({
	title,
	description,
	actionText,
	onAction,
	icon,
}: EmptyStateProps) {
	return (
		<div
			style={{
				display: "flex",
				justifyContent: "center",
				alignItems: "center",
				padding: "64px 24px",
			}}
		>
			<Empty
				image={icon ?? Empty.PRESENTED_IMAGE_SIMPLE}
				description={
					<div>
						<div
							style={{
								fontSize: 16,
								fontWeight: 600,
								marginBottom: description ? 8 : 0,
							}}
						>
							{title}
						</div>
						{description && (
							<div style={{ fontSize: 13, opacity: 0.65 }}>{description}</div>
						)}
					</div>
				}
			>
				{actionText && onAction && (
					<Button type="primary" onClick={onAction}>
						{actionText}
					</Button>
				)}
			</Empty>
		</div>
	);
}
