/**
 * Tree-shaken ECharts core — register only the chart types and components
 * actually used in the app. Cuts the echarts chunk from ~1.1 MB (full build)
 * to ~300-500 KB.
 *
 * Usage: pass this as the `echarts` prop to `<ReactECharts>` from
 * `echarts-for-react/lib/core` instead of using the default `echarts-for-react`
 * import (which pulls the full library).
 */
import * as echarts from "echarts/core";
import { LineChart, BarChart, PieChart, FunnelChart } from "echarts/charts";
import {
	TitleComponent,
	TooltipComponent,
	LegendComponent,
	GridComponent,
	ToolboxComponent,
	MarkLineComponent,
	DataZoomComponent,
} from "echarts/components";
import { LabelLayout } from "echarts/features";
import { CanvasRenderer } from "echarts/renderers";

echarts.use([
	LineChart,
	BarChart,
	PieChart,
	FunnelChart,
	TitleComponent,
	TooltipComponent,
	LegendComponent,
	GridComponent,
	ToolboxComponent,
	MarkLineComponent,
	DataZoomComponent,
	LabelLayout,
	CanvasRenderer,
]);

export default echarts;
