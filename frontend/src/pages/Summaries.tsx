import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Tabs, Table, Spin, Button, message, Space } from "antd";
import { FileExcelOutlined, FilePdfOutlined } from "@ant-design/icons";
import api from "../api/client";
import FilterToolbar from "../components/FilterToolbar";
import { useFilterParams } from "../hooks/useFilterParams";
import { fmtPct, fmtRoas, fmtUsd } from "../utils/formatters";
import type { SummaryRow } from "../types/api";

export default function Summaries() {
	const [byDate, setByDate] = useState<SummaryRow[]>([]);
	const [byCampaign, setByCampaign] = useState<SummaryRow[]>([]);
	const [byPlacement, setByPlacement] = useState<SummaryRow[]>([]);
	const [loading, setLoading] = useState(true);
	const [exporting, setExporting] = useState<"xlsx" | "pdf" | null>(null);
	const { dateFrom, dateTo, campaignId, marketplaceId, buildQueryString } =
		useFilterParams();

	useEffect(() => {
		setLoading(true);
		const qs = buildQueryString();
		Promise.all([
			api.get<SummaryRow[]>(`/summaries/by-date${qs}`),
			api.get<SummaryRow[]>(`/summaries/by-campaign${qs}`),
			api.get<SummaryRow[]>(`/summaries/by-placement${qs}`),
		])
			.then(([d, c, p]) => {
				setByDate(d.data);
				setByCampaign(c.data);
				setByPlacement(p.data);
			})
			.catch(() => {})
			.finally(() => setLoading(false));
	}, [dateFrom, dateTo, campaignId, marketplaceId, buildQueryString]);

	const handleExport = async (format: "xlsx" | "pdf") => {
		setExporting(format);
		try {
			const qs = buildQueryString();
			const endpoint = format === "xlsx" ? "excel" : "pdf";
			const res = await api.get(`/reports/${endpoint}${qs}`, {
				responseType: "blob",
			});
			const url = window.URL.createObjectURL(new Blob([res.data]));
			const link = document.createElement("a");
			link.href = url;
			const filename = `ad-report${dateFrom ? `_${dateFrom.format("YYYY-MM-DD")}` : ""}${dateTo ? `_${dateTo.format("YYYY-MM-DD")}` : ""}.${format}`;
			link.setAttribute("download", filename);
			document.body.appendChild(link);
			link.click();
			link.remove();
			window.URL.revokeObjectURL(url);
			message.success(`${format.toUpperCase()} 报告已下载`);
		} catch {
			message.error("导出失败");
		} finally {
			setExporting(null);
		}
	};

	const kpiCols = [
		{ title: "曝光量", dataIndex: "impressions", key: "imp" },
		{ title: "点击量", dataIndex: "clicks", key: "clk" },
		{
			title: "花费",
			dataIndex: "spend",
			key: "spend",
			render: fmtUsd,
		},
		{ title: "订单", dataIndex: "orders", key: "ord" },
		{
			title: "销售额",
			dataIndex: "sales",
			key: "sales",
			render: fmtUsd,
		},
		{
			title: "ROAS",
			dataIndex: "roas",
			key: "roas",
			render: fmtRoas,
		},
		{
			title: "ACOS",
			dataIndex: "acos",
			key: "acos",
			render: (v: number | null) => fmtPct(v, 2),
		},
	];

	const tabs = [
		{
			key: "date",
			label: "按日期",
			children: (
				<Table<SummaryRow>
					columns={[
						{ title: "日期", dataIndex: "date", key: "date" },
						...kpiCols,
					]}
					dataSource={byDate}
					rowKey="date"
					size="small"
				/>
			),
		},
		{
			key: "campaign",
			label: "按广告活动",
			children: (
				<Table<SummaryRow>
					columns={[
						{
							title: "广告活动",
							dataIndex: "campaign_name",
							key: "name",
							ellipsis: true,
							render: (text: string | undefined, record: SummaryRow) => (
								<Link
									to={`/campaigns/${record.campaign_id}`}
									style={{ color: "#1677ff" }}
								>
									{text ?? "-"}
								</Link>
							),
						},
						...kpiCols,
					]}
					dataSource={byCampaign}
					rowKey="campaign_id"
					size="small"
				/>
			),
		},
		{
			key: "placement",
			label: "按展示位置",
			children: (
				<Table<SummaryRow>
					columns={[
						{ title: "展示位置", dataIndex: "placement_type", key: "type" },
						...kpiCols,
					]}
					dataSource={byPlacement}
					rowKey="placement_type"
					size="small"
				/>
			),
		},
	];

	return (
		<Spin spinning={loading}>
			<FilterToolbar />
			<div
				style={{
					display: "flex",
					justifyContent: "flex-end",
					marginBottom: 16,
				}}
			>
				<Space>
					<Button
						type="primary"
						icon={<FileExcelOutlined />}
						onClick={() => handleExport("xlsx")}
						loading={exporting === "xlsx"}
						disabled={exporting !== null}
					>
						Excel 报告
					</Button>
					<Button
						icon={<FilePdfOutlined />}
						onClick={() => handleExport("pdf")}
						loading={exporting === "pdf"}
						disabled={exporting !== null}
					>
						PDF 报告
					</Button>
				</Space>
			</div>
			<Tabs items={tabs} />
		</Spin>
	);
}
