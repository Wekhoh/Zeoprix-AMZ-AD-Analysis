import { useState, useEffect } from "react";
import {
	Alert,
	Card,
	DatePicker,
	Button,
	Select,
	Table,
	Tabs,
	Tag,
	Row,
	Col,
	Statistic,
	Empty,
} from "antd";
import {
	SwapOutlined,
	ArrowUpOutlined,
	ArrowDownOutlined,
} from "@ant-design/icons";
import dayjs from "dayjs";
import "dayjs/locale/zh-cn";
import api from "../api/client";
import type { Campaign } from "../types/api";

dayjs.locale("zh-cn");

interface ComparisonResult {
	period_a: KPIRow;
	period_b: KPIRow;
	deltas: DeltaRow;
}

interface KPIRow {
	impressions: number;
	clicks: number;
	spend: number;
	orders: number;
	sales: number;
	ctr: number | null;
	cpc: number | null;
	roas: number | null;
	acos: number | null;
	cvr: number | null;
}

interface DeltaRow {
	[key: string]: {
		absolute: number;
		percent: number | null;
		favorable: boolean;
	};
}

const { RangePicker } = DatePicker;

export default function Analysis() {
	const [periodA, setPeriodA] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(
		null,
	);
	const [periodB, setPeriodB] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(
		null,
	);
	const [result, setResult] = useState<ComparisonResult | null>(null);
	const [loading, setLoading] = useState(false);

	// Campaign comparison state
	const [campaigns, setCampaigns] = useState<Campaign[]>([]);
	const [campA, setCampA] = useState<number | undefined>(undefined);
	const [campB, setCampB] = useState<number | undefined>(undefined);
	const [campResult, setCampResult] = useState<
		(ComparisonResult & { campaign_a: string; campaign_b: string }) | null
	>(null);
	const [campLoading, setCampLoading] = useState(false);

	useEffect(() => {
		api
			.get<Campaign[]>("/campaigns")
			.then((res) => setCampaigns(res.data))
			.catch(() => {});
	}, []);

	const handleCampCompare = async () => {
		if (!campA || !campB) return;
		setCampLoading(true);
		try {
			const params = new URLSearchParams({
				campaign_a: String(campA),
				campaign_b: String(campB),
			});
			const res = await api.get(`/summaries/campaign-comparison?${params}`);
			setCampResult(res.data);
		} finally {
			setCampLoading(false);
		}
	};

	const handleCompare = async () => {
		if (!periodA || !periodB) return;
		setLoading(true);
		try {
			const params = new URLSearchParams({
				period_a_from: periodA[0].format("YYYY-MM-DD"),
				period_a_to: periodA[1].format("YYYY-MM-DD"),
				period_b_from: periodB[0].format("YYYY-MM-DD"),
				period_b_to: periodB[1].format("YYYY-MM-DD"),
			});
			const res = await api.get<ComparisonResult>(
				`/summaries/comparison?${params}`,
			);
			setResult(res.data);
		} finally {
			setLoading(false);
		}
	};

	const kpiLabels: Record<string, string> = {
		impressions: "曝光量",
		clicks: "点击量",
		spend: "花费 ($)",
		orders: "订单数",
		sales: "销售额 ($)",
		ctr: "CTR",
		cpc: "CPC ($)",
		roas: "ROAS",
		acos: "ACOS",
		cvr: "CVR",
	};

	// For ACOS: lower is better. For everything else: higher is better.
	const lowerIsBetter = new Set(["acos", "cpc", "spend"]);

	const formatValue = (key: string, val: number | null): string => {
		if (val === null || val === undefined) return "-";
		if (key === "ctr" || key === "acos" || key === "cvr")
			return `${(val * 100).toFixed(2)}%`;
		if (key === "spend" || key === "sales" || key === "cpc")
			return `$${val.toFixed(2)}`;
		if (key === "roas") return val.toFixed(2);
		return String(Math.round(val));
	};

	const columns = [
		{ title: "指标", dataIndex: "label", key: "label", width: 120 },
		{
			title: periodA
				? `${periodA[0].format("MM/DD")} ~ ${periodA[1].format("MM/DD")}`
				: "期间 A",
			dataIndex: "valueA",
			key: "valueA",
			width: 150,
		},
		{
			title: periodB
				? `${periodB[0].format("MM/DD")} ~ ${periodB[1].format("MM/DD")}`
				: "期间 B",
			dataIndex: "valueB",
			key: "valueB",
			width: 150,
		},
		{
			title: "变化",
			dataIndex: "delta",
			key: "delta",
			width: 150,
			render: (
				_: unknown,
				record: {
					key: string;
					deltaAbs: number;
					deltaPct: number | null;
					favorable: boolean;
				},
			) => {
				if (record.deltaAbs === 0 && record.deltaPct === 0) return <Tag>-</Tag>;
				const color = record.favorable ? "green" : "red";
				const icon =
					record.deltaAbs > 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />;
				const pctStr =
					record.deltaPct !== null
						? ` (${record.deltaPct > 0 ? "+" : ""}${record.deltaPct.toFixed(1)}%)`
						: "";
				return (
					<Tag color={color} icon={icon}>
						{record.deltaAbs > 0 ? "+" : ""}
						{formatValue(record.key, record.deltaAbs)}
						{pctStr}
					</Tag>
				);
			},
		},
	];

	const tableData = result
		? Object.entries(kpiLabels).map(([key, label]) => {
				const a = result.period_a[key as keyof KPIRow] ?? 0;
				const b = result.period_b[key as keyof KPIRow] ?? 0;
				const delta = result.deltas[key] || {
					absolute: 0,
					percent: null,
					favorable: true,
				};
				return {
					key,
					label,
					valueA: formatValue(key, a as number),
					valueB: formatValue(key, b as number),
					deltaAbs: delta.absolute,
					deltaPct: delta.percent,
					favorable: delta.favorable,
				};
			})
		: [];

	const campTableData = campResult
		? Object.entries(kpiLabels).map(([key, label]) => {
				const a = campResult.period_a[key as keyof KPIRow] ?? 0;
				const b = campResult.period_b[key as keyof KPIRow] ?? 0;
				const delta = campResult.deltas[key] || {
					absolute: 0,
					percent: null,
					favorable: true,
				};
				return {
					key,
					label,
					valueA: formatValue(key, a as number),
					valueB: formatValue(key, b as number),
					deltaAbs: delta.absolute,
					deltaPct: delta.percent,
					favorable: delta.favorable,
				};
			})
		: [];

	const campColumns = [
		{ title: "指标", dataIndex: "label", key: "label", width: 120 },
		{
			title: campResult?.campaign_a || "活动 A",
			dataIndex: "valueA",
			key: "valueA",
			width: 150,
		},
		{
			title: campResult?.campaign_b || "活动 B",
			dataIndex: "valueB",
			key: "valueB",
			width: 150,
		},
		columns[3], // reuse delta column
	];

	return (
		<div>
			<Alert
				type="info"
				showIcon
				style={{ marginBottom: 16 }}
				message="归因窗口提示：SP 广告使用 7 天归因窗口，SB/SD 使用 14 天。最近 7 天的数据可能尚未完全归因，建议分析 7 天前的完整数据。"
			/>
			<Tabs
				items={[
					{
						key: "period",
						label: "周期对比",
						children: (
							<div>
								<Card style={{ marginBottom: 24 }}>
									<Row gutter={16} align="middle">
										<Col>
											<span style={{ marginRight: 8 }}>期间 A:</span>
											<RangePicker
												value={periodA}
												onChange={(dates) =>
													setPeriodA(dates as [dayjs.Dayjs, dayjs.Dayjs])
												}
											/>
										</Col>
										<Col>
											<SwapOutlined
												style={{ fontSize: 20, color: "#6B7280" }}
											/>
										</Col>
										<Col>
											<span style={{ marginRight: 8 }}>期间 B:</span>
											<RangePicker
												value={periodB}
												onChange={(dates) =>
													setPeriodB(dates as [dayjs.Dayjs, dayjs.Dayjs])
												}
											/>
										</Col>
										<Col>
											<Button
												type="primary"
												onClick={handleCompare}
												loading={loading}
												disabled={!periodA || !periodB}
											>
												对比
											</Button>
										</Col>
									</Row>
								</Card>
								{result ? (
									<Card title="对比结果">
										<Table
											columns={columns}
											dataSource={tableData}
											pagination={false}
											size="middle"
										/>
									</Card>
								) : (
									<Card>
										<Empty description="选择两个日期范围并点击「对比」查看结果" />
									</Card>
								)}
							</div>
						),
					},
					{
						key: "campaign",
						label: "活动对比",
						children: (
							<div>
								<Card style={{ marginBottom: 24 }}>
									<Row gutter={16} align="middle">
										<Col>
											<span style={{ marginRight: 8 }}>活动 A:</span>
											<Select
												placeholder="选择活动"
												value={campA}
												onChange={setCampA}
												style={{ width: 280 }}
												showSearch
												optionFilterProp="label"
												options={campaigns.map((c) => ({
													value: c.id,
													label: c.name,
												}))}
											/>
										</Col>
										<Col>
											<SwapOutlined
												style={{ fontSize: 20, color: "#6B7280" }}
											/>
										</Col>
										<Col>
											<span style={{ marginRight: 8 }}>活动 B:</span>
											<Select
												placeholder="选择活动"
												value={campB}
												onChange={setCampB}
												style={{ width: 280 }}
												showSearch
												optionFilterProp="label"
												options={campaigns.map((c) => ({
													value: c.id,
													label: c.name,
												}))}
											/>
										</Col>
										<Col>
											<Button
												type="primary"
												onClick={handleCampCompare}
												loading={campLoading}
												disabled={!campA || !campB || campA === campB}
											>
												对比
											</Button>
										</Col>
									</Row>
								</Card>
								{campResult ? (
									<Card title="活动对比结果">
										<Table
											columns={campColumns}
											dataSource={campTableData}
											pagination={false}
											size="middle"
										/>
									</Card>
								) : (
									<Card>
										<Empty description="选择两个广告活动并点击「对比」查看结果" />
									</Card>
								)}
							</div>
						),
					},
				]}
			/>
		</div>
	);
}
