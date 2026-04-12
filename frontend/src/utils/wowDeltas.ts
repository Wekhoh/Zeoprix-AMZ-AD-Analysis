import { ArrowDownOutlined, ArrowUpOutlined } from "@ant-design/icons";
import { createElement } from "react";
import type { DailyTrend } from "../types/api";

export interface WowDeltas {
	spend: number | null;
	orders: number | null;
	roas: number | null;
	acos: number | null;
	// Day-over-Day (B6-A-4)
	dod_spend: number | null;
	dod_orders: number | null;
	dod_roas: number | null;
	dod_acos: number | null;
}

export function calcWowDeltas(trend: DailyTrend[]): WowDeltas | null {
	if (trend.length < 2) return null;
	const sorted = [...trend].sort(
		(a, b) => new Date(a.date).getTime() - new Date(b.date).getTime(),
	);

	const sum = (arr: DailyTrend[], key: keyof DailyTrend) =>
		arr.reduce((s, d) => s + ((d[key] as number) || 0), 0);

	const calc = (curr: number, prev: number) =>
		prev > 0 ? ((curr - prev) / prev) * 100 : null;

	// Day-over-Day: last day vs day before
	const lastDay = sorted[sorted.length - 1];
	const prevDay = sorted.length >= 2 ? sorted[sorted.length - 2] : null;

	let dodSpend: number | null = null;
	let dodOrders: number | null = null;
	let dodRoas: number | null = null;
	let dodAcos: number | null = null;

	if (prevDay) {
		dodSpend = calc(lastDay.spend || 0, prevDay.spend || 0);
		dodOrders = calc(lastDay.orders || 0, prevDay.orders || 0);
		const lastRoas = lastDay.spend ? (lastDay.sales || 0) / lastDay.spend : 0;
		const prevRoas = prevDay.spend ? (prevDay.sales || 0) / prevDay.spend : 0;
		dodRoas = calc(lastRoas, prevRoas);
		const lastAcos = lastDay.sales ? (lastDay.spend || 0) / lastDay.sales : 0;
		const prevAcos = prevDay.sales ? (prevDay.spend || 0) / prevDay.sales : 0;
		dodAcos = calc(lastAcos, prevAcos);
	}

	// Week-over-Week: last 7 days vs previous 7 days (original logic)
	let wowSpend: number | null = null;
	let wowOrders: number | null = null;
	let wowRoas: number | null = null;
	let wowAcos: number | null = null;

	if (sorted.length >= 14) {
		const last7 = sorted.slice(-7);
		const prev7 = sorted.slice(-14, -7);

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

		wowSpend = calc(currSpend, prevSpend);
		wowOrders = calc(currOrders, prevOrders);
		wowRoas = calc(currRoas, prevRoas);
		wowAcos = calc(currAcos, prevAcos);
	}

	return {
		spend: wowSpend,
		orders: wowOrders,
		roas: wowRoas,
		acos: wowAcos,
		dod_spend: dodSpend,
		dod_orders: dodOrders,
		dod_roas: dodRoas,
		dod_acos: dodAcos,
	};
}

function DeltaLine({
	delta,
	label,
	invertColor,
}: {
	delta: number | null;
	label: string;
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
		"span",
		{ style: { fontSize: 11, color } },
		icon,
		` ${Math.abs(delta).toFixed(1)}% ${label}`,
	);
}

export function WowIndicator({
	delta,
	dodDelta,
	invertColor,
}: {
	delta: number | null;
	dodDelta?: number | null;
	invertColor?: boolean;
}) {
	const dodLine = DeltaLine({
		delta: dodDelta ?? null,
		label: "vs 昨天",
		invertColor,
	});
	const wowLine = DeltaLine({ delta, label: "vs 上周", invertColor });

	if (!dodLine && !wowLine) return null;

	return createElement(
		"div",
		{ style: { marginTop: 4, lineHeight: 1.6 } },
		dodLine,
		dodLine && wowLine ? createElement("br") : null,
		wowLine,
	);
}
