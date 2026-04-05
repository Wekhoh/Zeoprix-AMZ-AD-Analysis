import { ArrowUpOutlined, ArrowDownOutlined } from "@ant-design/icons";
import { createElement } from "react";
import type { DailyTrend } from "../types/api";

export interface WowDeltas {
	spend: number | null;
	orders: number | null;
	roas: number | null;
	acos: number | null;
}

export function calcWowDeltas(trend: DailyTrend[]): WowDeltas | null {
	if (trend.length < 8) return null;
	const sorted = [...trend].sort(
		(a, b) => new Date(a.date).getTime() - new Date(b.date).getTime(),
	);
	const last7 = sorted.slice(-7);
	const prev7 = sorted.slice(-14, -7);
	if (prev7.length < 7) return null;

	const sum = (arr: DailyTrend[], key: keyof DailyTrend) =>
		arr.reduce((s, d) => s + ((d[key] as number) || 0), 0);

	const calc = (curr: number, prev: number) =>
		prev > 0 ? ((curr - prev) / prev) * 100 : null;

	const currSpend = sum(last7, "spend");
	const prevSpend = sum(prev7, "spend");
	const currOrders = sum(last7, "orders");
	const prevOrders = sum(prev7, "orders");
	const currSales = sum(last7, "sales");
	const prevSales = sum(prev7, "sales");

	const currRoas = currSpend > 0 ? currSales / currSpend : 0;
	const prevRoas = prevSpend > 0 ? prevSales / prevSpend : 0;
	const currAcos = currSales > 0 ? currSpend / currSales : 0;
	const prevAcos = prevSales > 0 ? prevSpend / prevSales : 0;

	return {
		spend: calc(currSpend, prevSpend),
		orders: calc(currOrders, prevOrders),
		roas: calc(currRoas, prevRoas),
		acos: calc(currAcos, prevAcos),
	};
}

export function WowIndicator({
	delta,
	invertColor,
}: {
	delta: number | null;
	invertColor?: boolean;
}) {
	if (delta === null) return null;
	const isUp = delta > 0;
	const isGood = invertColor ? !isUp : isUp;
	const color = isGood ? "#52c41a" : "#ff4d4f";
	const icon = isUp
		? createElement(ArrowUpOutlined)
		: createElement(ArrowDownOutlined);
	return createElement(
		"div",
		{ style: { fontSize: 12, color, marginTop: 4 } },
		icon,
		` ${Math.abs(delta).toFixed(1)}% vs 上周`,
	);
}
