import type { ReactElement } from "react";
import { fmtPct } from "./formatters";

/**
 * Render a threshold-colored ACOS cell.
 *
 * Color rules (shared across Settings placement-compare, Ad-groups tab, etc.):
 *   - ACOS > 50%  → red   (#ff4d4f, clearly unprofitable)
 *   - ACOS < 25%  → green (#52c41a, healthy)
 *   - otherwise   → neutral
 *
 * Null/undefined renders as "-".
 *
 * @param v fractional ACOS in [0, 1]
 */
export function renderAcos(
	v: number | null | undefined,
): ReactElement | string {
	if (v == null) return "-";
	const color = v > 0.5 ? "#ff4d4f" : v < 0.25 ? "#52c41a" : undefined;
	return <span style={{ color }}>{fmtPct(v, 2)}</span>;
}
