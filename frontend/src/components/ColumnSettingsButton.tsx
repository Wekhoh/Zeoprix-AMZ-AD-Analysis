import { Button, Checkbox, Divider, Popover } from "antd";
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
 * Gear-icon Popover that lets users show/hide table columns.
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
		<div style={{ minWidth: 180 }}>
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
		<Popover
			trigger="click"
			placement="bottomRight"
			title="显示的列"
			content={content}
		>
			<Button icon={<SettingOutlined />} aria-label="列设置">
				列
			</Button>
		</Popover>
	);
}
