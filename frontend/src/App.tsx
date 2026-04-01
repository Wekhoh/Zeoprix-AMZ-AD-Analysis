import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ConfigProvider, theme } from "antd";
import zhCN from "antd/locale/zh_CN";
import ErrorBoundary from "./components/ErrorBoundary";
import AppLayout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Import from "./pages/Import";
import Campaigns from "./pages/Campaigns";
import Placements from "./pages/Placements";
import OperationLogs from "./pages/OperationLogs";
import Summaries from "./pages/Summaries";
import CampaignDetail from "./pages/CampaignDetail";
import Analysis from "./pages/Analysis";
import SearchTerms from "./pages/SearchTerms";
import Suggestions from "./pages/Suggestions";
import Rules from "./pages/Rules";
import Settings from "./pages/Settings";
import { useTheme, ThemeProvider } from "./hooks/useTheme";

const lightTokens = {
	colorPrimary: "#2563EB",
	colorBgContainer: "#FFFFFF",
	colorBgLayout: "#F5F5F7",
	colorBgElevated: "#FFFFFF",
	colorBorder: "#E5E7EB",
	colorText: "#1F2937",
	colorTextSecondary: "#6B7280",
	colorTextTertiary: "#9CA3AF",
	colorTextQuaternary: "#D1D5DB",
	colorTextPlaceholder: "#9CA3AF",
	borderRadius: 8,
	fontSize: 14,
};

const darkTokens = {
	colorPrimary: "#3B82F6",
	colorBgContainer: "#1A1D24",
	colorBgLayout: "#111318",
	colorBgElevated: "#222730",
	colorBorder: "#3A3F4B",
	colorText: "#E5E7EB",
	colorTextSecondary: "#9CA3AF",
	colorTextTertiary: "#6B7280",
	colorTextQuaternary: "#4B5563",
	colorTextPlaceholder: "#9CA3AF",
	borderRadius: 8,
	fontSize: 14,
};

const lightComponents = {
	Card: {
		paddingLG: 20,
		colorTextHeading: "#1F2937",
	},
	Table: {
		headerBg: "#FAFAFA",
		headerColor: "#6B7280",
		rowHoverBg: "rgba(37,99,235,0.04)",
		borderColor: "#F0F0F0",
		colorText: "#374151",
	},
	Menu: {
		itemBg: "transparent",
		itemSelectedBg: "rgba(37,99,235,0.08)",
		itemSelectedColor: "#2563EB",
		itemColor: "#6B7280",
		itemHoverColor: "#1F2937",
	},
	Select: {
		colorText: "#374151",
		colorTextPlaceholder: "#9CA3AF",
		colorBorder: "#E5E7EB",
		optionSelectedBg: "rgba(37,99,235,0.08)",
	},
	DatePicker: {
		colorTextPlaceholder: "#9CA3AF",
		colorBorder: "#E5E7EB",
		colorIcon: "#9CA3AF",
	},
	Input: {
		colorTextPlaceholder: "#9CA3AF",
		colorBorder: "#E5E7EB",
	},
	InputNumber: {
		colorTextPlaceholder: "#9CA3AF",
		colorBorder: "#E5E7EB",
	},
	Button: {
		defaultColor: "#374151",
		defaultBorderColor: "#E5E7EB",
	},
	Modal: {
		headerBg: "#FFFFFF",
		contentBg: "#FFFFFF",
		titleColor: "#1F2937",
	},
	Tabs: {
		itemColor: "#6B7280",
		itemActiveColor: "#2563EB",
		itemHoverColor: "#1F2937",
	},
	Alert: {
		colorText: "#374151",
	},
	Tag: {
		defaultBg: "rgba(0,0,0,0.04)",
	},
	Statistic: {
		titleColor: "#6B7280",
		contentColor: "#1F2937",
	},
};

const darkComponents = {
	Card: {
		paddingLG: 20,
		colorTextHeading: "#F3F4F6",
	},
	Table: {
		headerBg: "#1A1D24",
		headerColor: "#9CA3AF",
		rowHoverBg: "rgba(59,130,246,0.06)",
		borderColor: "#2A2F3A",
		colorText: "#D1D5DB",
	},
	Menu: {
		darkItemBg: "transparent",
		darkItemSelectedBg: "rgba(59,130,246,0.1)",
		darkItemSelectedColor: "#3B82F6",
		darkItemColor: "#9CA3AF",
		darkItemHoverColor: "#E5E7EB",
	},
	Select: {
		colorText: "#D1D5DB",
		colorTextPlaceholder: "#9CA3AF",
		colorBorder: "#3A3F4B",
		optionSelectedBg: "rgba(59,130,246,0.1)",
	},
	DatePicker: {
		colorTextPlaceholder: "#9CA3AF",
		colorBorder: "#3A3F4B",
		colorIcon: "#9CA3AF",
	},
	Input: {
		colorTextPlaceholder: "#9CA3AF",
		colorBorder: "#3A3F4B",
	},
	InputNumber: {
		colorTextPlaceholder: "#9CA3AF",
		colorBorder: "#3A3F4B",
	},
	Button: {
		defaultColor: "#D1D5DB",
		defaultBorderColor: "#3A3F4B",
	},
	Modal: {
		headerBg: "#1A1D24",
		contentBg: "#1A1D24",
		titleColor: "#F3F4F6",
	},
	Tabs: {
		itemColor: "#9CA3AF",
		itemActiveColor: "#3B82F6",
		itemHoverColor: "#D1D5DB",
	},
	Alert: {
		colorText: "#E5E7EB",
	},
	Tag: {
		defaultBg: "rgba(255,255,255,0.06)",
	},
	Statistic: {
		titleColor: "#9CA3AF",
		contentColor: "#F3F4F6",
	},
};

function AppInner() {
	const { isDark } = useTheme();

	return (
		<ConfigProvider
			locale={zhCN}
			theme={{
				algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
				token: isDark ? darkTokens : lightTokens,
				components: isDark ? darkComponents : lightComponents,
			}}
		>
			<ErrorBoundary>
				<BrowserRouter>
					<Routes>
						<Route element={<AppLayout />}>
							<Route path="/" element={<Dashboard />} />
							<Route path="/import" element={<Import />} />
							<Route path="/campaigns" element={<Campaigns />} />
							<Route path="/campaigns/:id" element={<CampaignDetail />} />
							<Route path="/placements" element={<Placements />} />
							<Route path="/operation-logs" element={<OperationLogs />} />
							<Route path="/summaries" element={<Summaries />} />
							<Route path="/analysis" element={<Analysis />} />
							<Route path="/search-terms" element={<SearchTerms />} />
							<Route path="/suggestions" element={<Suggestions />} />
							<Route path="/rules" element={<Rules />} />
							<Route path="/settings" element={<Settings />} />
						</Route>
					</Routes>
				</BrowserRouter>
			</ErrorBoundary>
		</ConfigProvider>
	);
}

export default function App() {
	return (
		<ThemeProvider>
			<AppInner />
		</ThemeProvider>
	);
}
