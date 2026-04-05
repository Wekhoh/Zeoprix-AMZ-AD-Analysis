import { useState, useEffect, useCallback } from "react";
import { Card, Tag, Space } from "antd";
import { Link } from "react-router-dom";
import type { Suggestion, SuggestionSeverity } from "../types/api";
import api from "../api/client";
import EmptyState from "../components/EmptyState";
import FilterToolbar from "../components/FilterToolbar";
import PageSkeleton from "../components/PageSkeleton";
import { useFilterParams } from "../hooks/useFilterParams";
import { useTheme } from "../hooks/useTheme";

const SEVERITY_CONFIG: Record<
	SuggestionSeverity,
	{ color: string; label: string }
> = {
	critical: { color: "#f5222d", label: "严重" },
	high: { color: "#fa8c16", label: "高" },
	medium: { color: "#EAB308", label: "中" },
	opportunity: { color: "#52c41a", label: "机会" },
	info: { color: "#1677ff", label: "信息" },
};

const SEVERITY_ORDER: SuggestionSeverity[] = [
	"critical",
	"high",
	"medium",
	"opportunity",
	"info",
];

function groupBySeverity(
	suggestions: Suggestion[],
): Map<SuggestionSeverity, Suggestion[]> {
	const grouped = new Map<SuggestionSeverity, Suggestion[]>();
	for (const severity of SEVERITY_ORDER) {
		const items = suggestions.filter((s) => s.severity === severity);
		if (items.length > 0) {
			grouped.set(severity, items);
		}
	}
	return grouped;
}

function SuggestionCard({ suggestion }: { suggestion: Suggestion }) {
	const config = SEVERITY_CONFIG[suggestion.severity];
	const { isDark } = useTheme();
	const metricEntries = suggestion.metric
		? Object.entries(suggestion.metric)
		: [];

	return (
		<Card
			style={{
				marginBottom: 16,
				borderLeft: `2px solid ${config.color}`,
			}}
			styles={{ body: { padding: "16px 20px" } }}
		>
			<div
				style={{
					display: "flex",
					justifyContent: "space-between",
					alignItems: "flex-start",
					marginBottom: 8,
				}}
			>
				<h4 style={{ margin: 0, fontWeight: 600, fontSize: 15 }}>
					{suggestion.title}
				</h4>
				<Tag color={config.color} style={{ marginLeft: 12, flexShrink: 0 }}>
					{config.label}
				</Tag>
			</div>

			<div
				style={{
					marginBottom: 8,
					color: isDark ? "#9CA3AF" : "#6B7280",
					fontSize: 13,
				}}
			>
				广告活动:{" "}
				<Link to={`/campaigns/${suggestion.campaign_id}`}>
					{suggestion.campaign_name}
				</Link>
			</div>

			<p style={{ margin: "8px 0", color: isDark ? "#D1D5DB" : "#374151" }}>
				{suggestion.description}
			</p>

			<div
				style={{
					background: isDark ? "rgba(59,130,246,0.06)" : "rgba(37,99,235,0.04)",
					border: isDark
						? "1px solid rgba(59,130,246,0.15)"
						: "1px solid rgba(37,99,235,0.12)",
					borderLeft: `2px solid ${isDark ? "#3B82F6" : "#2563EB"}`,
					borderRadius: 6,
					padding: "8px 12px",
					margin: "12px 0",
					fontSize: 13,
				}}
			>
				<strong>建议操作: </strong>
				{suggestion.action}
			</div>

			{metricEntries.length > 0 && (
				<Space wrap style={{ marginTop: 8 }}>
					{metricEntries.map(([key, value]) => (
						<Tag key={key} color="default">
							{key}: {value}
						</Tag>
					))}
				</Space>
			)}
		</Card>
	);
}

export default function Suggestions() {
	const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
	const [loading, setLoading] = useState(false);
	const { dateFrom, dateTo, buildQueryString } = useFilterParams();

	const fetchData = useCallback(() => {
		setLoading(true);
		api
			.get<Suggestion[]>(`/analysis/suggestions${buildQueryString()}`)
			.then((res) => setSuggestions(res.data))
			.finally(() => setLoading(false));
	}, [buildQueryString]);

	useEffect(fetchData, [dateFrom, dateTo, fetchData]);

	if (loading) return <PageSkeleton variant="cards" />;

	if (suggestions.length === 0) {
		return (
			<>
				<div style={{ marginBottom: 16 }}>
					<FilterToolbar showCampaignFilter={false} />
				</div>
				<EmptyState
					title="暂无优化建议"
					description="当前日期范围内数据不足以生成建议。调整日期范围或导入更多广告数据。"
				/>
			</>
		);
	}

	const grouped = groupBySeverity(suggestions);

	return (
		<div>
			<div style={{ marginBottom: 16 }}>
				<FilterToolbar showCampaignFilter={false} />
			</div>
			{Array.from(grouped.entries()).map(([severity, items]) => {
				const config = SEVERITY_CONFIG[severity];
				return (
					<div key={severity} style={{ marginBottom: 32 }}>
						<h3
							style={{
								color: config.color,
								borderBottom: `2px solid ${config.color}`,
								paddingBottom: 8,
								marginBottom: 16,
							}}
						>
							{config.label} ({items.length})
						</h3>
						{items.map((s, idx) => (
							<SuggestionCard key={`${severity}-${idx}`} suggestion={s} />
						))}
					</div>
				);
			})}
		</div>
	);
}
