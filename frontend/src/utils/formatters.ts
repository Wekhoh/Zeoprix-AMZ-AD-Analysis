/**
 * Shared display formatters for KPI tables and cards.
 *
 * All functions accept `number | null | undefined` and return "-" for
 * missing values so callers don't need to pre-check.
 */

export const fmtUsd = (v: number | null | undefined): string =>
	v != null ? `$${v.toFixed(2)}` : "-";

/**
 * Format a fractional value as a percentage.
 *
 * @param v - fraction in [0, 1] range (e.g. 0.42 → "42.0%")
 * @param digits - decimal places (default: 1)
 */
export const fmtPct = (v: number | null | undefined, digits = 1): string =>
	v != null ? `${(v * 100).toFixed(digits)}%` : "-";

export const fmtNum = (v: number | null | undefined): string =>
	v != null ? v.toLocaleString() : "-";
