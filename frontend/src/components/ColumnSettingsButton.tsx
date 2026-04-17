import { Button, Checkbox, Divider, Dropdown } from "antd";
import { SettingOutlined } from "@ant-design/icons";

export interface ColumnDescriptor {
	/** Column key (must match the `key` in your columns array) */
	key: string;
	/** Human-readable label shown in the dropdown */
	label: string;
	/** Optional: if true, column cannot be hidden (disabled checkbox) */
	required?: boolean;
}

interface ColumnSettingsButtonProps {
	columns: ColumnDescriptor[];
	hiddenKeys: Set<string>;
	onToggle: (key: string) => void;
	onReset: () => void;
}

/**
 * Gear-icon Dropdown that lets users show/hide table columns.
 *
 * Design: rendered in the page header next to filters. Each column appears as
 * a checkbox; required columns are disabled-but-checked. A "重置" button at
 * the bottom clears all overrides.
 */
export default function ColumnSettingsButton({
	columns,
	hiddenKeys,
	onToggle,
	onReset,
}: ColumnSettingsButtonProps) {
	const content = (
		<div
			style={{
				background: "var(--ant-color-bg-elevated, #fff)",
				border: "1px solid var(--ant-color-border, #d9d9d9)",
				borderRadius: 8,
				padding: "8px 12px",
				minWidth: 180,
				boxShadow:
					"0 6px 16px 0 rgba(0, 0, 0, 0.08), 0 3px 6px -4px rgba(0, 0, 0, 0.12)",
			}}
		>
			<div
				style={{
					fontSize: 12,
					fontWeight: 500,
					opacity: 0.65,
					marginBottom: 6,
				}}
			>
				显示的列
			</div>
			<div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
				{columns.map((col) => {
					const checked = !hiddenKeys.has(col.key);
					return (
						<Checkbox
							key={col.key}
							checked={checked}
							disabled={col.required}
							onChange={() => onToggle(col.key)}
						>
							{col.label}
							{col.required && (
								<span style={{ marginLeft: 6, fontSize: 11, opacity: 0.5 }}>
									（必选）
								</span>
							)}
						</Checkbox>
					);
				})}
			</div>
			<Divider style={{ margin: "8px 0" }} />
			<Button
				type="link"
				size="small"
				onClick={onReset}
				style={{ padding: 0, height: "auto" }}
			>
				重置为默认
			</Button>
		</div>
	);

	return (
		<Dropdown
			trigger={["click"]}
			placement="bottomRight"
			popupRender={() => content}
		>
			<Button icon={<SettingOutlined />} aria-label="列设置">
				列
			</Button>
		</Dropdown>
	);
}
