import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Input, Modal } from "antd";
import {
	DashboardOutlined,
	UploadOutlined,
	FundProjectionScreenOutlined,
	AppstoreOutlined,
	FileTextOutlined,
	BarChartOutlined,
	SwapOutlined,
	SearchOutlined,
	BulbOutlined,
	ThunderboltOutlined,
	SettingOutlined,
	CloudUploadOutlined,
	DownloadOutlined,
	PlusOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { useTheme } from "../hooks/useTheme";
import type { ReactNode } from "react";

interface CommandItem {
	key: string;
	label: string;
	icon: ReactNode;
	type: "navigate" | "action";
	path?: string;
	action?: () => void;
}

interface CommandPaletteProps {
	open: boolean;
	onClose: () => void;
}

export default function CommandPalette({ open, onClose }: CommandPaletteProps) {
	const navigate = useNavigate();
	const { isDark } = useTheme();
	const [query, setQuery] = useState("");
	const [selectedIndex, setSelectedIndex] = useState(0);
	const inputRef = useRef<ReturnType<typeof Input.Search> | null>(null);
	const listRef = useRef<HTMLDivElement>(null);

	const handleNavigate = useCallback(
		(path: string) => {
			navigate(path);
			onClose();
		},
		[navigate, onClose],
	);

	const items: CommandItem[] = useMemo(
		() => [
			{
				key: "home",
				label: "首页仪表盘",
				icon: <DashboardOutlined />,
				type: "navigate",
				path: "/",
			},
			{
				key: "import",
				label: "数据导入",
				icon: <UploadOutlined />,
				type: "navigate",
				path: "/import",
			},
			{
				key: "campaigns",
				label: "广告活动",
				icon: <FundProjectionScreenOutlined />,
				type: "navigate",
				path: "/campaigns",
			},
			{
				key: "placements",
				label: "展示位置",
				icon: <AppstoreOutlined />,
				type: "navigate",
				path: "/placements",
			},
			{
				key: "operation-logs",
				label: "操作日志",
				icon: <FileTextOutlined />,
				type: "navigate",
				path: "/operation-logs",
			},
			{
				key: "summaries",
				label: "数据汇总",
				icon: <BarChartOutlined />,
				type: "navigate",
				path: "/summaries",
			},
			{
				key: "analysis",
				label: "对比分析",
				icon: <SwapOutlined />,
				type: "navigate",
				path: "/analysis",
			},
			{
				key: "search-terms",
				label: "搜索词分析",
				icon: <SearchOutlined />,
				type: "navigate",
				path: "/search-terms",
			},
			{
				key: "suggestions",
				label: "智能建议",
				icon: <BulbOutlined />,
				type: "navigate",
				path: "/suggestions",
			},
			{
				key: "rules",
				label: "自动化规则",
				icon: <ThunderboltOutlined />,
				type: "navigate",
				path: "/rules",
			},
			{
				key: "settings",
				label: "系统设置",
				icon: <SettingOutlined />,
				type: "navigate",
				path: "/settings",
			},
			{
				key: "action-backup",
				label: "创建备份",
				icon: <CloudUploadOutlined />,
				type: "action",
				action: () => handleNavigate("/settings"),
			},
			{
				key: "action-export",
				label: "导出报告",
				icon: <DownloadOutlined />,
				type: "action",
				action: () => handleNavigate("/placements"),
			},
			{
				key: "action-add-rule",
				label: "添加规则",
				icon: <PlusOutlined />,
				type: "action",
				action: () => handleNavigate("/rules"),
			},
		],
		[handleNavigate],
	);

	const filtered = useMemo(() => {
		if (!query.trim()) return items;
		const lowerQuery = query.toLowerCase();
		return items.filter((item) =>
			item.label.toLowerCase().includes(lowerQuery),
		);
	}, [items, query]);

	useEffect(() => {
		if (open) {
			setQuery("");
			setSelectedIndex(0);
		}
	}, [open]);

	useEffect(() => {
		setSelectedIndex(0);
	}, [query]);

	// Scroll selected item into view
	useEffect(() => {
		if (!listRef.current) return;
		const selectedEl = listRef.current.children[selectedIndex] as
			| HTMLElement
			| undefined;
		if (selectedEl) {
			selectedEl.scrollIntoView({ block: "nearest" });
		}
	}, [selectedIndex]);

	const handleSelect = useCallback(
		(item: CommandItem) => {
			if (item.type === "navigate" && item.path) {
				navigate(item.path);
			} else if (item.type === "action" && item.action) {
				item.action();
			}
			onClose();
		},
		[navigate, onClose],
	);

	const handleKeyDown = useCallback(
		(e: React.KeyboardEvent) => {
			if (e.key === "ArrowDown") {
				e.preventDefault();
				setSelectedIndex((prev) => (prev < filtered.length - 1 ? prev + 1 : 0));
			} else if (e.key === "ArrowUp") {
				e.preventDefault();
				setSelectedIndex((prev) => (prev > 0 ? prev - 1 : filtered.length - 1));
			} else if (e.key === "Enter") {
				e.preventDefault();
				const item = filtered[selectedIndex];
				if (item) {
					handleSelect(item);
				}
			}
		},
		[filtered, selectedIndex, handleSelect],
	);

	const bgColor = isDark ? "#1A1D24" : "#FFFFFF";
	const itemHoverBg = isDark ? "#2A2F3A" : "#F0F0F0";
	const selectedBg = isDark ? "#2A2F3A" : "#E6F4FF";
	const textColor = isDark ? "#D1D5DB" : "#1F2937";
	const secondaryColor = isDark ? "#6B7280" : "#9CA3AF";
	const borderColor = isDark ? "#2A2F3A" : "#E5E7EB";

	return (
		<Modal
			open={open}
			onCancel={onClose}
			footer={null}
			closable={false}
			width={520}
			styles={{
				body: { padding: 0 },
				content: {
					background: bgColor,
					borderRadius: 12,
					overflow: "hidden",
				},
			}}
			style={{ top: "15%" }}
		>
			<div onKeyDown={handleKeyDown}>
				<div
					style={{
						padding: "12px 16px",
						borderBottom: `1px solid ${borderColor}`,
					}}
				>
					<Input
						ref={inputRef as React.Ref<ReturnType<typeof Input>>}
						placeholder="搜索页面或操作... (Ctrl+K)"
						value={query}
						onChange={(e) => setQuery(e.target.value)}
						variant="borderless"
						size="large"
						prefix={
							<SearchOutlined style={{ color: secondaryColor, fontSize: 16 }} />
						}
						autoFocus
						style={{ color: textColor }}
					/>
				</div>
				<div
					ref={listRef}
					style={{
						maxHeight: 360,
						overflowY: "auto",
						padding: "8px 0",
					}}
				>
					{filtered.length === 0 && (
						<div
							style={{
								padding: "24px 16px",
								textAlign: "center",
								color: secondaryColor,
							}}
						>
							未找到匹配项
						</div>
					)}
					{filtered.map((item, idx) => (
						<div
							key={item.key}
							onClick={() => handleSelect(item)}
							onMouseEnter={() => setSelectedIndex(idx)}
							style={{
								display: "flex",
								alignItems: "center",
								gap: 12,
								padding: "10px 16px",
								cursor: "pointer",
								background: idx === selectedIndex ? selectedBg : "transparent",
								color: textColor,
								transition: "background 0.15s",
							}}
							onMouseOver={(e) => {
								if (idx !== selectedIndex) {
									(e.currentTarget as HTMLElement).style.background =
										itemHoverBg;
								}
							}}
							onMouseOut={(e) => {
								if (idx !== selectedIndex) {
									(e.currentTarget as HTMLElement).style.background =
										"transparent";
								}
							}}
						>
							<span style={{ fontSize: 16, color: secondaryColor }}>
								{item.icon}
							</span>
							<span style={{ flex: 1 }}>{item.label}</span>
							<span
								style={{
									fontSize: 11,
									color: secondaryColor,
									textTransform: "uppercase",
								}}
							>
								{item.type === "navigate" ? "页面" : "操作"}
							</span>
						</div>
					))}
				</div>
				<div
					style={{
						padding: "8px 16px",
						borderTop: `1px solid ${borderColor}`,
						display: "flex",
						gap: 16,
						fontSize: 12,
						color: secondaryColor,
					}}
				>
					<span>↑↓ 导航</span>
					<span>↵ 选择</span>
					<span>Esc 关闭</span>
				</div>
			</div>
		</Modal>
	);
}
