/**
 * Sparkline — tiny inline SVG trend line for KPI cards.
 * Zero dependencies, pure SVG polyline from an array of numbers.
 *
 * Usage: <Sparkline data={[10, 15, 8, 22, 18]} />
 */

interface SparklineProps {
	data: number[];
	width?: number;
	height?: number;
	color?: string;
}

export default function Sparkline({
	data,
	width = 80,
	height = 24,
	color = "#1677ff",
}: SparklineProps) {
	if (data.length < 2) return null;

	const min = Math.min(...data);
	const max = Math.max(...data);
	const range = max - min || 1;
	const padding = 2;
	const innerW = width - padding * 2;
	const innerH = height - padding * 2;

	const points = data
		.map((v, i) => {
			const x = padding + (i / (data.length - 1)) * innerW;
			const y = padding + innerH - ((v - min) / range) * innerH;
			return `${x},${y}`;
		})
		.join(" ");

	// Determine if trend is up or down (last vs first)
	const trendColor = data[data.length - 1] >= data[0] ? color : "#ff4d4f";

	return (
		<svg
			width={width}
			height={height}
			style={{ display: "inline-block", verticalAlign: "middle" }}
		>
			<polyline
				points={points}
				fill="none"
				stroke={trendColor}
				strokeWidth={1.5}
				strokeLinecap="round"
				strokeLinejoin="round"
			/>
		</svg>
	);
}
