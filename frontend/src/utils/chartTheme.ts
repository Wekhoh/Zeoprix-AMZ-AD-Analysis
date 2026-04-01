export const CHART_COLORS = [
	"#3B82F6",
	"#10B981",
	"#F59E0B",
	"#8B5CF6",
	"#EF4444",
];

export const darkChartOptions = {
	backgroundColor: "transparent",
	textStyle: { color: "#9CA3AF", fontSize: 12 },
	legend: { textStyle: { color: "#9CA3AF" } },
	tooltip: {
		backgroundColor: "#222730",
		borderColor: "#2A2F3A",
		textStyle: { color: "#D1D5DB" },
	},
	xAxis: {
		axisLine: { lineStyle: { color: "#2A2F3A" } },
		axisLabel: { color: "#9CA3AF" },
		nameTextStyle: { color: "#9CA3AF" },
		splitLine: { lineStyle: { color: "#1E2129" } },
	},
	yAxis: {
		axisLine: { lineStyle: { color: "#2A2F3A" } },
		axisLabel: { color: "#9CA3AF" },
		nameTextStyle: { color: "#9CA3AF" },
		splitLine: { lineStyle: { color: "#1E2129" } },
	},
};

export const lightChartOptions = {
	backgroundColor: "transparent",
	textStyle: { color: "#6B7280", fontSize: 12 },
	legend: { textStyle: { color: "#6B7280" } },
	tooltip: {
		backgroundColor: "#FFFFFF",
		borderColor: "#E5E7EB",
		textStyle: { color: "#1F2937" },
	},
	xAxis: {
		axisLine: { lineStyle: { color: "#E5E7EB" } },
		axisLabel: { color: "#6B7280" },
		nameTextStyle: { color: "#6B7280" },
		splitLine: { lineStyle: { color: "#F3F4F6" } },
	},
	yAxis: {
		axisLine: { lineStyle: { color: "#E5E7EB" } },
		axisLabel: { color: "#6B7280" },
		nameTextStyle: { color: "#6B7280" },
		splitLine: { lineStyle: { color: "#F3F4F6" } },
	},
};

export function withTheme(
	option: Record<string, unknown>,
	isDark: boolean,
): Record<string, unknown> {
	const base = isDark ? darkChartOptions : lightChartOptions;
	return {
		...option,
		backgroundColor: "transparent",
		textStyle: { ...base.textStyle },
		tooltip: {
			...base.tooltip,
			...((option.tooltip as object) || {}),
		},
		legend: {
			...base.legend,
			...((option.legend as object) || {}),
		},
		xAxis: Array.isArray(option.xAxis)
			? option.xAxis.map((x: object) => ({ ...base.xAxis, ...x }))
			: { ...base.xAxis, ...((option.xAxis as object) || {}) },
		yAxis: Array.isArray(option.yAxis)
			? option.yAxis.map((y: object) => ({ ...base.yAxis, ...y }))
			: { ...base.yAxis, ...((option.yAxis as object) || {}) },
	};
}

/** @deprecated Use withTheme(option, true) instead */
export function withDarkTheme(
	option: Record<string, unknown>,
): Record<string, unknown> {
	return withTheme(option, true);
}
