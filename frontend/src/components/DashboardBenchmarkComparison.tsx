import { useEffect, useState } from "react";
import { Card, Col, Progress, Row } from "antd";
import api from "../api/client";
import type { BenchmarkResult } from "../types/api";

interface DashboardBenchmarkComparisonProps {
	buildQueryString: () => string;
}

/**
 * Category-benchmark comparison card on the Dashboard. Fetches
 * /settings/products first, picks the first product with a category_key,
 * then fires /benchmarks/compare for that category. Extracted from
 * Dashboard.tsx (F4-α).
 */
export default function DashboardBenchmarkComparison({
	buildQueryString,
}: DashboardBenchmarkComparisonProps) {
	const [benchmarkData, setBenchmarkData] = useState<BenchmarkResult | null>(
		null,
	);

	useEffect(() => {
		api
			.get<{ id: number; category_key: string | null }[]>("/settings/products")
			.then((res) => {
				const products = res.data;
				const withCategory = products.find(
					(p: { category_key: string | null }) => p.category_key,
				);
				if (withCategory?.category_key) {
					const qs = buildQueryString();
					const sep = qs ? "&" : "?";
					api
						.get<BenchmarkResult>(
							`/benchmarks/compare${qs}${sep}category=${withCategory.category_key}`,
						)
						.then((r) => setBenchmarkData(r.data))
						.catch(() => setBenchmarkData(null));
				} else {
					setBenchmarkData(null);
				}
			});
	}, [buildQueryString]);

	if (!benchmarkData || benchmarkData.comparisons.length === 0) return null;

	return (
		<Card
			title={`品类基准对比 - ${benchmarkData.category_label}`}
			style={{ marginBottom: 24 }}
		>
			<Row gutter={[24, 16]}>
				{benchmarkData.comparisons.map((item) => {
					const isGood =
						item.metric === "ACOS" || item.metric === "CPC"
							? item.status === "below"
							: item.status === "above";
					const maxVal = Math.max(item.actual, item.benchmark) * 1.2;
					const actualPct = maxVal > 0 ? (item.actual / maxVal) * 100 : 0;
					const benchPct = maxVal > 0 ? (item.benchmark / maxVal) * 100 : 0;
					const formatVal = (v: number) =>
						item.metric === "CTR" ||
						item.metric === "CVR" ||
						item.metric === "ACOS"
							? `${(v * 100).toFixed(2)}%`
							: `$${v.toFixed(2)}`;
					return (
						<Col xs={24} sm={12} md={12} lg={6} key={item.metric}>
							<div style={{ marginBottom: 8 }}>
								<strong>{item.metric}</strong>
								<span
									style={{
										float: "right",
										color: isGood ? "#52c41a" : "#ff4d4f",
										fontSize: 12,
									}}
								>
									{item.diff_pct > 0 ? "+" : ""}
									{item.diff_pct}%
								</span>
							</div>
							<div style={{ marginBottom: 4, fontSize: 12, color: "#9CA3AF" }}>
								实际: {formatVal(item.actual)}
							</div>
							<Progress
								percent={actualPct}
								strokeColor={isGood ? "#52c41a" : "#ff4d4f"}
								showInfo={false}
								size="small"
							/>
							<div
								style={{
									marginBottom: 4,
									marginTop: 4,
									fontSize: 12,
									color: "#9CA3AF",
								}}
							>
								基准: {formatVal(item.benchmark)}
							</div>
							<Progress
								percent={benchPct}
								strokeColor="#d9d9d9"
								showInfo={false}
								size="small"
							/>
						</Col>
					);
				})}
			</Row>
		</Card>
	);
}
