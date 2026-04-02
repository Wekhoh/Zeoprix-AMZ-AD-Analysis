import { useCallback, useEffect, useMemo, useState } from "react";
import { Layout as AntLayout, Breadcrumb, Menu, Select, Tooltip } from "antd";
import {
	GlobalOutlined,
	SunOutlined,
	MoonOutlined,
	DesktopOutlined,
} from "@ant-design/icons";
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
} from "@ant-design/icons";
import { Link, Outlet, useNavigate, useLocation } from "react-router-dom";
import { useMarketplace } from "../hooks/useMarketplace";
import { useTheme } from "../hooks/useTheme";
import type { ThemeMode } from "../hooks/useTheme";
import CommandPalette from "./CommandPalette";

const { Sider, Content, Header } = AntLayout;

const SIDEBAR_COLLAPSED_KEY = "amz-sidebar-collapsed";

function getInitialCollapsed(): boolean {
	const stored = localStorage.getItem(SIDEBAR_COLLAPSED_KEY);
	return stored === "true";
}

const menuItems = [
	{
		type: "group" as const,
		label: "数据管理",
		children: [
			{ key: "/", icon: <DashboardOutlined />, label: "首页仪表盘" },
			{ key: "/import", icon: <UploadOutlined />, label: "数据导入" },
			{
				key: "/campaigns",
				icon: <FundProjectionScreenOutlined />,
				label: "广告活动",
			},
			{ key: "/placements", icon: <AppstoreOutlined />, label: "展示位置" },
			{
				key: "/operation-logs",
				icon: <FileTextOutlined />,
				label: "操作日志",
			},
		],
	},
	{
		type: "group" as const,
		label: "分析洞察",
		children: [
			{ key: "/summaries", icon: <BarChartOutlined />, label: "数据汇总" },
			{ key: "/analysis", icon: <SwapOutlined />, label: "对比分析" },
			{
				key: "/search-terms",
				icon: <SearchOutlined />,
				label: "搜索词分析",
			},
			{ key: "/suggestions", icon: <BulbOutlined />, label: "智能建议" },
		],
	},
	{
		type: "group" as const,
		label: "自动化与设置",
		children: [
			{
				key: "/rules",
				icon: <ThunderboltOutlined />,
				label: "自动化规则",
			},
			{ key: "/settings", icon: <SettingOutlined />, label: "系统设置" },
		],
	},
];

const THEME_CYCLE: ThemeMode[] = ["light", "dark", "system"];

const THEME_CONFIG: Record<
	ThemeMode,
	{ icon: React.ReactNode; tooltip: string }
> = {
	light: { icon: <SunOutlined />, tooltip: "浅色模式" },
	dark: { icon: <MoonOutlined />, tooltip: "深色模式" },
	system: { icon: <DesktopOutlined />, tooltip: "跟随系统" },
};

const ROUTE_LABELS: Record<string, string> = {
	"/": "首页",
	"/import": "数据导入",
	"/campaigns": "广告活动",
	"/placements": "展示位置",
	"/operation-logs": "操作日志",
	"/summaries": "数据汇总",
	"/analysis": "对比分析",
	"/search-terms": "搜索词分析",
	"/suggestions": "智能建议",
	"/rules": "自动化规则",
	"/settings": "系统设置",
};

function useBreadcrumbItems(pathname: string, isDark: boolean) {
	return useMemo(() => {
		const linkColor = isDark ? "#9CA3AF" : "#8C8C8C";
		const textColor = isDark ? "#D1D5DB" : "#595959";

		if (pathname === "/") {
			return [{ title: <span style={{ color: textColor }}>首页</span> }];
		}

		const items: Array<{ title: React.ReactNode }> = [
			{
				title: (
					<Link to="/" style={{ color: linkColor }}>
						首页
					</Link>
				),
			},
		];

		const segments = pathname.split("/").filter(Boolean);

		for (let i = 0; i < segments.length; i++) {
			const partialPath = "/" + segments.slice(0, i + 1).join("/");
			const isLast = i === segments.length - 1;
			const label = ROUTE_LABELS[partialPath];

			if (label) {
				items.push(
					isLast
						? { title: <span style={{ color: textColor }}>{label}</span> }
						: {
								title: (
									<Link to={partialPath} style={{ color: linkColor }}>
										{label}
									</Link>
								),
							},
				);
			} else if (
				segments.length > 1 &&
				ROUTE_LABELS["/" + segments[0]] &&
				isLast
			) {
				items.push({
					title: <span style={{ color: textColor }}>详情</span>,
				});
			}
		}

		return items;
	}, [pathname, isDark]);
}

export default function AppLayout() {
	const navigate = useNavigate();
	const location = useLocation();
	const { marketplaceId, setMarketplaceId, marketplaces } = useMarketplace();
	const { mode, isDark, setMode } = useTheme();
	const [collapsed, setCollapsed] = useState(getInitialCollapsed);
	const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
	const breadcrumbItems = useBreadcrumbItems(location.pathname, isDark);

	const toggleCommandPalette = useCallback(() => {
		setCommandPaletteOpen((prev) => !prev);
	}, []);

	useEffect(() => {
		const handleKeyDown = (e: KeyboardEvent) => {
			if ((e.ctrlKey || e.metaKey) && e.key === "k") {
				e.preventDefault();
				toggleCommandPalette();
			}
		};
		window.addEventListener("keydown", handleKeyDown);
		return () => window.removeEventListener("keydown", handleKeyDown);
	}, [toggleCommandPalette]);

	const handleCollapse = (value: boolean) => {
		setCollapsed(value);
		localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(value));
	};

	const cycleTheme = () => {
		const currentIdx = THEME_CYCLE.indexOf(mode);
		const nextIdx = (currentIdx + 1) % THEME_CYCLE.length;
		setMode(THEME_CYCLE[nextIdx]);
	};

	const currentConfig = THEME_CONFIG[mode];

	return (
		<AntLayout style={{ minHeight: "100vh" }}>
			<Sider
				width={200}
				collapsedWidth={64}
				collapsible
				collapsed={collapsed}
				onCollapse={handleCollapse}
				theme={isDark ? "dark" : "light"}
				trigger={null}
				style={{ position: "relative" }}
			>
				<div
					style={{
						height: 64,
						display: "flex",
						alignItems: "center",
						justifyContent: "center",
						color: isDark ? "#fff" : "#1F2937",
						fontWeight: 700,
						fontSize: collapsed ? 18 : 15,
						background: "transparent",
						borderBottom: `1px solid ${isDark ? "#1E2129" : "#E5E7EB"}`,
						cursor: "pointer",
						userSelect: "none",
						overflow: "hidden",
						whiteSpace: "nowrap",
					}}
					onClick={() => handleCollapse(!collapsed)}
					title={collapsed ? "展开侧栏" : "收起侧栏"}
				>
					{collapsed ? "A" : "AMZ Ad Tracker"}
				</div>
				<Menu
					theme={isDark ? "dark" : "light"}
					mode="inline"
					selectedKeys={[location.pathname]}
					items={menuItems}
					onClick={({ key }) => navigate(key)}
				/>
			</Sider>
			<AntLayout style={{ background: isDark ? "#111318" : "#F5F5F7" }}>
				<Header
					style={{
						background: isDark ? "#111318" : "#FFFFFF",
						padding: "0 24px",
						display: "flex",
						alignItems: "center",
						justifyContent: "flex-end",
						borderBottom: `1px solid ${isDark ? "#1E2129" : "#E5E7EB"}`,
					}}
				>
					<div style={{ display: "flex", alignItems: "center", gap: 12 }}>
						<Tooltip title={currentConfig.tooltip}>
							<button
								type="button"
								onClick={cycleTheme}
								aria-label={currentConfig.tooltip}
								style={{
									background: "none",
									border: `1px solid ${isDark ? "#3A3F4B" : "#E5E7EB"}`,
									borderRadius: 6,
									padding: "4px 8px",
									cursor: "pointer",
									display: "flex",
									alignItems: "center",
									justifyContent: "center",
									color: isDark ? "#9CA3AF" : "#6B7280",
									fontSize: 16,
									transition: "all 0.2s",
								}}
							>
								{currentConfig.icon}
							</button>
						</Tooltip>
						<div
							style={{
								width: 1,
								height: 20,
								background: isDark ? "#2A2F3A" : "#E5E7EB",
							}}
						/>
						<GlobalOutlined style={{ color: isDark ? "#9CA3AF" : "#6B7280" }} />
						<Select
							placeholder="全部站点"
							allowClear
							style={{ width: 160 }}
							value={marketplaceId}
							onChange={(val: number | undefined) => setMarketplaceId(val)}
							options={marketplaces.map((m) => ({
								value: m.id,
								label: `${m.name} (${m.code})`,
							}))}
						/>
					</div>
				</Header>
				<Breadcrumb
					items={breadcrumbItems}
					style={{
						margin: "12px 24px 0",
						marginBottom: 8,
						fontSize: 13,
					}}
				/>
				<Content
					style={{
						margin: 24,
						minHeight: "calc(100vh - 64px)",
						background: "transparent",
					}}
				>
					<Outlet />
				</Content>
			</AntLayout>
			<CommandPalette
				open={commandPaletteOpen}
				onClose={() => setCommandPaletteOpen(false)}
			/>
		</AntLayout>
	);
}
