import { useState } from "react";
import {
	Card,
	Collapse,
	Upload,
	message,
	Table,
	Tag,
	Row,
	Col,
	Steps,
	Button,
	Space,
} from "antd";
import {
	UploadOutlined,
	FileTextOutlined,
	CheckCircleOutlined,
	QuestionCircleOutlined,
} from "@ant-design/icons";
import type { UploadFile } from "antd";
import api from "../api/client";
import PageHelp from "../components/PageHelp";

interface ImportDetail {
	message: string;
	level: string;
}

interface ImportResult {
	imported: number;
	updated: number;
	skipped: number;
	details: ImportDetail[];
}

interface PreviewWarning {
	level: "error" | "warning" | "info";
	message: string;
}

interface PreviewFile {
	filename: string;
	campaign_name: string;
	date_range: string;
	record_count: number;
	columns: string[];
	sample_rows: Record<string, unknown>[];
	ad_type: string;
	warnings?: PreviewWarning[];
	error?: string;
}

interface PreviewResponse {
	files: PreviewFile[];
}

const PREVIEW_COLUMNS = [
	{ title: "日期", dataIndex: "date", key: "date", width: 100 },
	{
		title: "展示位置",
		dataIndex: "placement",
		key: "placement",
		width: 140,
		ellipsis: true,
	},
	{
		title: "曝光",
		dataIndex: "impressions",
		key: "impressions",
		width: 80,
	},
	{ title: "点击", dataIndex: "clicks", key: "clicks", width: 70 },
	{
		title: "花费",
		dataIndex: "spend",
		key: "spend",
		width: 90,
		render: (v: number) => (v != null ? `$${v.toFixed(2)}` : "-"),
	},
	{ title: "订单", dataIndex: "orders", key: "orders", width: 70 },
	{
		title: "销售额",
		dataIndex: "sales",
		key: "sales",
		width: 100,
		render: (v: number) => (v != null ? `$${v.toFixed(2)}` : "-"),
	},
];

export default function Import() {
	const [csvResult, setCsvResult] = useState<ImportResult | null>(null);
	const [logResult, setLogResult] = useState<ImportResult | null>(null);
	const [csvLoading, setCsvLoading] = useState(false);
	const [logLoading, setLogLoading] = useState(false);

	// Preview state
	const [csvStep, setCsvStep] = useState(0);
	const [previewData, setPreviewData] = useState<PreviewFile[]>([]);
	const [pendingFiles, setPendingFiles] = useState<UploadFile[]>([]);
	const [previewLoading, setPreviewLoading] = useState(false);

	const handleCsvPreview = async (fileList: UploadFile[]) => {
		if (!fileList.length) return;
		setPendingFiles(fileList);
		setPreviewLoading(true);
		setCsvResult(null);

		const formData = new FormData();
		for (const f of fileList) {
			if (f.originFileObj) formData.append("files", f.originFileObj);
		}
		try {
			const res = await api.post<PreviewResponse>("/import/preview", formData);
			setPreviewData(res.data.files);
			setCsvStep(1);
		} catch {
			message.error("预览失败");
		} finally {
			setPreviewLoading(false);
		}
	};

	const handleCsvConfirmImport = async () => {
		if (!pendingFiles.length) return;
		setCsvLoading(true);
		const formData = new FormData();
		for (const f of pendingFiles) {
			if (f.originFileObj) formData.append("files", f.originFileObj);
		}
		try {
			const res = await api.post<ImportResult>(
				"/import/placement-csv",
				formData,
			);
			setCsvResult(res.data);
			setCsvStep(2);
			message.success(
				`CSV 导入完成: ${res.data.imported} 条新增, ${res.data.updated} 条更新`,
			);
		} catch {
			message.error("CSV 导入失败");
		} finally {
			setCsvLoading(false);
		}
	};

	const handleCsvCancel = () => {
		setCsvStep(0);
		setPreviewData([]);
		setPendingFiles([]);
		setCsvResult(null);
	};

	const handleLogUpload = async (fileList: UploadFile[]) => {
		if (!fileList.length) return;
		setLogLoading(true);
		const formData = new FormData();
		for (const f of fileList) {
			if (f.originFileObj) formData.append("files", f.originFileObj);
		}
		try {
			const res = await api.post<ImportResult>(
				"/import/operation-log",
				formData,
			);
			setLogResult(res.data);
			message.success(`日志导入完成: ${res.data.imported} 条新增`);
		} catch {
			message.error("日志导入失败");
		} finally {
			setLogLoading(false);
		}
	};

	const resultColumns = [
		{
			title: "详情",
			dataIndex: "message",
			key: "message",
		},
		{
			title: "级别",
			dataIndex: "level",
			key: "level",
			render: (level: string) => (
				<Tag
					color={
						level === "error" ? "red" : level === "warning" ? "orange" : "blue"
					}
				>
					{level}
				</Tag>
			),
		},
	];

	return (
		<div>
			<div style={{ display: "flex", alignItems: "center", marginBottom: 16 }}>
				<span style={{ fontSize: 16, fontWeight: 600 }}>数据导入</span>
				<PageHelp
					title="数据导入帮助"
					content="支持上传亚马逊后台导出的展示位置 CSV 文件和操作日志 TXT 文件。系统会自动识别格式并检测重复数据。"
				/>
			</div>
			<Collapse
				style={{ marginBottom: 24 }}
				items={[
					{
						key: "guide",
						label: (
							<Space>
								<QuestionCircleOutlined />
								如何从亚马逊后台下载报告？
							</Space>
						),
						children: (
							<div style={{ fontSize: 13, lineHeight: 1.8 }}>
								<h4 style={{ marginTop: 0 }}>展示位置报告（CSV）</h4>
								<ol style={{ paddingLeft: 20 }}>
									<li>登录 Seller Central &rarr; 广告 &rarr; 广告活动管理器</li>
									<li>点击目标广告活动名称进入详情</li>
									<li>
										切换到 <strong>展示位置</strong> 标签页
									</li>
									<li>设置日期范围（建议最近 30 天）</li>
									<li>
										点击右上角 <strong>导出</strong> 按钮，选择 CSV 格式
									</li>
								</ol>
								<h4>搜索词报告（CSV）</h4>
								<ol style={{ paddingLeft: 20 }}>
									<li>
										广告活动管理器 &rarr; 左侧菜单 &rarr;{" "}
										<strong>衡量和报告</strong> &rarr; <strong>广告报告</strong>
									</li>
									<li>
										点击 <strong>创建报告</strong>
									</li>
									<li>
										报告类型选择 <strong>搜索词</strong>，时间单位选
										<strong>汇总</strong>
									</li>
									<li>设置日期范围，点击运行报告</li>
									<li>报告生成后在列表中下载 CSV 文件</li>
								</ol>
								<h4>操作日志（TXT）</h4>
								<ol style={{ paddingLeft: 20 }}>
									<li>广告活动管理器 &rarr; 目标广告活动</li>
									<li>
										点击 <strong>历史记录</strong> 标签
									</li>
									<li>选择日期范围，点击导出</li>
								</ol>
							</div>
						),
					},
				]}
			/>

			<Row gutter={24}>
				<Col span={12}>
					<Card title="上传展示位置 CSV" style={{ marginBottom: 24 }}>
						<Steps
							current={csvStep}
							size="small"
							style={{ marginBottom: 24 }}
							items={[
								{ title: "上传文件" },
								{ title: "预览数据" },
								{
									title: "导入结果",
									icon: csvStep === 2 ? <CheckCircleOutlined /> : undefined,
								},
							]}
						/>

						{csvStep === 0 && (
							<Upload.Dragger
								multiple
								accept=".csv"
								beforeUpload={() => false}
								onChange={({ fileList }) => handleCsvPreview(fileList)}
								showUploadList={false}
							>
								<p className="ant-upload-drag-icon">
									<UploadOutlined style={{ fontSize: 48, color: "#1677ff" }} />
								</p>
								<p>点击或拖拽 CSV 文件到此区域</p>
								<p style={{ color: "#9CA3AF" }}>支持同时上传多个文件</p>
							</Upload.Dragger>
						)}

						{previewLoading && <p style={{ marginTop: 16 }}>解析中...</p>}

						{csvStep === 1 && previewData.length > 0 && (
							<div>
								{previewData.map((pf, idx) => (
									<Card
										key={`${pf.filename}-${idx}`}
										size="small"
										title={pf.filename}
										style={{ marginBottom: 16 }}
									>
										{pf.error ? (
											<Tag color="red">{pf.error}</Tag>
										) : (
											<>
												<Space size="large" style={{ marginBottom: 12 }}>
													<span>
														广告活动: <strong>{pf.campaign_name}</strong>
													</span>
													<span>
														日期范围: <strong>{pf.date_range || "-"}</strong>
													</span>
													<span>
														记录数: <strong>{pf.record_count}</strong>
													</span>
													<Tag color="blue">{pf.ad_type}</Tag>
												</Space>
												{pf.warnings && pf.warnings.length > 0 && (
													<Space
														direction="vertical"
														style={{ width: "100%", marginBottom: 12 }}
													>
														{pf.warnings.map((w, wIdx) => (
															<Tag
																key={`w-${wIdx}`}
																color={
																	w.level === "error"
																		? "red"
																		: w.level === "warning"
																			? "orange"
																			: "blue"
																}
																style={{
																	whiteSpace: "normal",
																	padding: "4px 8px",
																}}
															>
																{w.level === "error"
																	? "错误"
																	: w.level === "warning"
																		? "警告"
																		: "提示"}
																: {w.message}
															</Tag>
														))}
													</Space>
												)}
												<Table
													columns={PREVIEW_COLUMNS}
													dataSource={pf.sample_rows.map((row, i) => ({
														...row,
														key: i,
													}))}
													size="small"
													pagination={false}
													scroll={{ x: 600 }}
												/>
											</>
										)}
									</Card>
								))}
								<Space style={{ marginTop: 16 }}>
									<Button
										type="primary"
										onClick={handleCsvConfirmImport}
										loading={csvLoading}
										disabled={previewData.some((pf) =>
											pf.warnings?.some((w) => w.level === "error"),
										)}
									>
										确认导入
									</Button>
									<Button onClick={handleCsvCancel}>取消</Button>
								</Space>
							</div>
						)}

						{csvStep === 2 && csvResult && (
							<div style={{ marginTop: 16 }}>
								<p>
									新增: <strong>{csvResult.imported}</strong> | 更新:{" "}
									<strong>{csvResult.updated}</strong> | 跳过:{" "}
									<strong>{csvResult.skipped}</strong>
								</p>
								<Table
									columns={resultColumns}
									dataSource={csvResult.details.map((d, i) => ({
										...d,
										key: i,
									}))}
									size="small"
									pagination={false}
								/>
								<Button style={{ marginTop: 16 }} onClick={handleCsvCancel}>
									继续导入
								</Button>
							</div>
						)}
					</Card>
				</Col>
				<Col span={12}>
					<Card title="上传操作日志 TXT">
						<Upload.Dragger
							multiple
							accept=".txt"
							beforeUpload={() => false}
							onChange={({ fileList }) => handleLogUpload(fileList)}
							showUploadList={false}
						>
							<p className="ant-upload-drag-icon">
								<FileTextOutlined style={{ fontSize: 48, color: "#52c41a" }} />
							</p>
							<p>点击或拖拽 TXT 文件到此区域</p>
							<p style={{ color: "#9CA3AF" }}>支持广告活动和广告组日志</p>
						</Upload.Dragger>
						{logLoading && <p style={{ marginTop: 16 }}>导入中...</p>}
						{logResult && (
							<div style={{ marginTop: 16 }}>
								<p>
									新增: <strong>{logResult.imported}</strong> | 跳过:{" "}
									<strong>{logResult.skipped}</strong>
								</p>
								<Table
									columns={resultColumns}
									dataSource={logResult.details.map((d, i) => ({
										...d,
										key: i,
									}))}
									size="small"
									pagination={false}
								/>
							</div>
						)}
					</Card>
				</Col>
			</Row>
		</div>
	);
}
