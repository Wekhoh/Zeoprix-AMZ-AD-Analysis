import { useEffect, useState } from "react";
import {
	Table,
	Button,
	Modal,
	Form,
	Input,
	InputNumber,
	Select,
	Switch,
	Space,
	Tag,
	message,
	Card,
	Spin,
	Popconfirm,
} from "antd";
import {
	PlusOutlined,
	PlayCircleOutlined,
	DeleteOutlined,
} from "@ant-design/icons";
import api from "../api/client";
import EmptyState from "../components/EmptyState";
import PageHelp from "../components/PageHelp";

interface RuleItem {
	id: number;
	name: string;
	description: string | null;
	condition_field: string;
	condition_operator: string;
	condition_value: number;
	condition_min_data: number;
	period_days: number;
	action_type: string;
	is_active: number;
	last_run_at: string | null;
	created_at: string | null;
}

interface RuleResult {
	rule_id: number;
	rule_name: string;
	campaign_id: number;
	campaign_name: string;
	condition_field: string;
	condition_operator: string;
	condition_value: number;
	triggered_value: number | null;
	action_type: string;
	recommended_action: string;
}

const FIELD_LABELS: Record<string, string> = {
	acos: "ACOS",
	roas: "ROAS",
	clicks: "点击量",
	orders: "订单数",
	spend: "花费",
	ctr: "CTR",
	cpc: "CPC",
};

const ACTION_LABELS: Record<string, string> = {
	flag_pause: "建议暂停",
	suggest_negative: "否定关键词",
	suggest_bid_increase: "提高竞价",
	suggest_bid_decrease: "降低竞价",
	suggest_budget_increase: "增加预算",
	diagnose_zero_spend: "诊断零花费",
	flag_budget_risk: "预算风险",
	attribution_reminder: "归因提醒",
	negative_buffer_reminder: "否定词生效",
};

const ACTION_COLORS: Record<string, string> = {
	flag_pause: "red",
	suggest_negative: "orange",
	suggest_bid_increase: "green",
	suggest_bid_decrease: "blue",
	suggest_budget_increase: "cyan",
	diagnose_zero_spend: "volcano",
	flag_budget_risk: "gold",
	attribution_reminder: "geekblue",
	negative_buffer_reminder: "purple",
};

function formatCondition(rule: RuleItem): string {
	const field = FIELD_LABELS[rule.condition_field] ?? rule.condition_field;
	const minClause =
		rule.condition_min_data > 0
			? ` (最低 ${rule.condition_min_data} 次点击)`
			: "";
	return `${field} ${rule.condition_operator} ${rule.condition_value}${minClause}`;
}

export default function Rules() {
	const [rules, setRules] = useState<RuleItem[]>([]);
	const [results, setResults] = useState<RuleResult[]>([]);
	const [loading, setLoading] = useState(true);
	const [evaluating, setEvaluating] = useState(false);
	const [modalOpen, setModalOpen] = useState(false);
	const [form] = Form.useForm();

	const fetchRules = async () => {
		setLoading(true);
		try {
			const res = await api.get<RuleItem[]>("/rules");
			setRules(res.data);
		} finally {
			setLoading(false);
		}
	};

	useEffect(() => {
		void fetchRules();
	}, []);

	const handleCreate = async () => {
		try {
			const values = await form.validateFields();
			await api.post("/rules", values);
			message.success("规则创建成功");
			setModalOpen(false);
			form.resetFields();
			void fetchRules();
		} catch {
			// validation error or API error
		}
	};

	const handleToggle = async (rule: RuleItem, checked: boolean) => {
		await api.put(`/rules/${rule.id}`, { is_active: checked ? 1 : 0 });
		void fetchRules();
	};

	const handleDelete = async (id: number) => {
		await api.delete(`/rules/${id}`);
		message.success("规则已删除");
		void fetchRules();
	};

	const handleEvaluateAll = async () => {
		setEvaluating(true);
		try {
			const res = await api.post<{
				total_triggered: number;
				results: RuleResult[];
			}>("/rules/evaluate");
			setResults(res.data.results);
			message.success(`评估完成，触发 ${res.data.total_triggered} 条结果`);
			void fetchRules();
		} catch {
			message.error("规则评估失败");
		} finally {
			setEvaluating(false);
		}
	};

	const ruleColumns = [
		{ title: "规则名称", dataIndex: "name", key: "name", width: 160 },
		{
			title: "条件",
			key: "condition",
			width: 280,
			render: (_: unknown, record: RuleItem) => formatCondition(record),
		},
		{
			title: "回溯天数",
			dataIndex: "period_days",
			key: "period",
			width: 100,
			render: (v: number) => `${v} 天`,
		},
		{
			title: "动作",
			dataIndex: "action_type",
			key: "action",
			width: 120,
			render: (v: string) => (
				<Tag color={ACTION_COLORS[v] ?? "default"}>{ACTION_LABELS[v] ?? v}</Tag>
			),
		},
		{
			title: "状态",
			dataIndex: "is_active",
			key: "status",
			width: 80,
			render: (v: number, record: RuleItem) => (
				<Switch
					checked={v === 1}
					onChange={(checked) => handleToggle(record, checked)}
					size="small"
				/>
			),
		},
		{
			title: "上次运行",
			dataIndex: "last_run_at",
			key: "last_run",
			width: 160,
			render: (v: string | null) => v ?? "-",
		},
		{
			title: "操作",
			key: "actions",
			width: 60,
			render: (_: unknown, record: RuleItem) => (
				<Popconfirm
					title="确定删除此规则？"
					onConfirm={() => handleDelete(record.id)}
				>
					<Button
						type="text"
						danger
						icon={<DeleteOutlined />}
						size="small"
						aria-label="删除规则"
					/>
				</Popconfirm>
			),
		},
	];

	const resultColumns = [
		{
			title: "广告活动",
			dataIndex: "campaign_name",
			key: "campaign",
			ellipsis: true,
		},
		{ title: "规则", dataIndex: "rule_name", key: "rule", width: 160 },
		{
			title: "触发值",
			dataIndex: "triggered_value",
			key: "value",
			width: 100,
			render: (v: number | null) =>
				v !== null ? (v < 1 ? `${(v * 100).toFixed(1)}%` : v.toFixed(2)) : "-",
		},
		{
			title: "建议操作",
			dataIndex: "recommended_action",
			key: "action",
			width: 200,
			render: (v: string, record: RuleResult) => (
				<Tag color={ACTION_COLORS[record.action_type] ?? "default"}>{v}</Tag>
			),
		},
	];

	return (
		<Spin spinning={loading}>
			<Card
				title={
					<span>
						自动化规则
						<PageHelp
							title="自动化规则帮助"
							content={
								<div>
									<p>
										自动化规则根据您设定的条件监控广告表现。当条件触发时，系统会显示建议操作。点击「运行全部规则」手动评估。
									</p>
									<p style={{ fontWeight: 600, marginTop: 12 }}>
										竞价策略说明：
									</p>
									<ul style={{ paddingLeft: 20 }}>
										<li>
											<strong>固定竞价 (Fixed bids)</strong>
											：出价不会自动调整。适合严格控制 CPC 的场景。
										</li>
										<li>
											<strong>动态竞价 - 仅降低 (Down only)</strong>
											：转化可能性低时自动降低出价。最安全的动态策略。
										</li>
										<li>
											<strong>动态竞价 - 提高和降低 (Up and down)</strong>
											：高转化时出价最高可翻倍（2x），低转化时降至 0。CPC
											波动最大。
										</li>
									</ul>
									<p style={{ fontWeight: 600, marginTop: 12 }}>广告位调整：</p>
									<p>
										搜索顶部和商品页面可设置 0-900%
										的竞价调整，与动态竞价叠加计算。
									</p>
								</div>
							}
						/>
					</span>
				}
				extra={
					<Space>
						<Button
							type="primary"
							icon={<PlusOutlined />}
							onClick={() => setModalOpen(true)}
						>
							添加规则
						</Button>
						<Button
							icon={<PlayCircleOutlined />}
							onClick={handleEvaluateAll}
							loading={evaluating}
						>
							运行全部规则
						</Button>
					</Space>
				}
			>
				{!loading && rules.length === 0 ? (
					<EmptyState
						title="暂无自动化规则"
						description="创建自动化规则来监控广告表现"
						actionText="添加规则"
						onAction={() => setModalOpen(true)}
					/>
				) : (
					<Table
						columns={ruleColumns}
						dataSource={rules}
						rowKey="id"
						size="middle"
						pagination={false}
					/>
				)}
			</Card>

			{results.length > 0 && (
				<Card
					title={`评估结果 (${results.length} 条触发)`}
					style={{ marginTop: 24 }}
				>
					<Table
						columns={resultColumns}
						dataSource={results}
						rowKey={(r) => `${r.rule_id}-${r.campaign_id}`}
						size="middle"
						pagination={{ pageSize: 20 }}
					/>
				</Card>
			)}

			<Modal
				title="添加自动化规则"
				open={modalOpen}
				onOk={handleCreate}
				onCancel={() => {
					setModalOpen(false);
					form.resetFields();
				}}
				okText="创建"
				cancelText="取消"
				width={560}
			>
				<Form
					form={form}
					layout="vertical"
					initialValues={{
						period_days: 7,
						condition_min_data: 0,
						is_active: 1,
					}}
				>
					<Form.Item
						name="name"
						label="规则名称"
						rules={[{ required: true, message: "请输入规则名称" }]}
					>
						<Input placeholder="如: 高 ACOS 预警" />
					</Form.Item>
					<Form.Item name="description" label="描述">
						<Input.TextArea rows={2} placeholder="规则描述（可选）" />
					</Form.Item>
					<Space size="middle" style={{ display: "flex" }}>
						<Form.Item
							name="condition_field"
							label="监控指标"
							rules={[{ required: true, message: "请选择" }]}
						>
							<Select style={{ width: 120 }}>
								<Select.Option value="acos">ACOS</Select.Option>
								<Select.Option value="roas">ROAS</Select.Option>
								<Select.Option value="clicks">点击量</Select.Option>
								<Select.Option value="orders">订单数</Select.Option>
								<Select.Option value="spend">花费</Select.Option>
								<Select.Option value="ctr">CTR</Select.Option>
								<Select.Option value="cpc">CPC</Select.Option>
							</Select>
						</Form.Item>
						<Form.Item
							name="condition_operator"
							label="操作符"
							rules={[{ required: true, message: "请选择" }]}
						>
							<Select style={{ width: 80 }}>
								<Select.Option value=">">&gt;</Select.Option>
								<Select.Option value="<">&lt;</Select.Option>
								<Select.Option value=">=">&gt;=</Select.Option>
								<Select.Option value="<=">&lt;=</Select.Option>
								<Select.Option value="==">==</Select.Option>
							</Select>
						</Form.Item>
						<Form.Item
							name="condition_value"
							label="阈值"
							rules={[{ required: true, message: "请输入" }]}
						>
							<InputNumber style={{ width: 100 }} />
						</Form.Item>
					</Space>
					<Space size="middle" style={{ display: "flex" }}>
						<Form.Item name="condition_min_data" label="最低点击量">
							<InputNumber min={0} style={{ width: 100 }} />
						</Form.Item>
						<Form.Item name="period_days" label="回溯天数">
							<InputNumber min={1} max={90} style={{ width: 100 }} />
						</Form.Item>
					</Space>
					<Form.Item
						name="action_type"
						label="触发动作"
						rules={[{ required: true, message: "请选择" }]}
					>
						<Select>
							<Select.Option value="flag_pause">建议暂停广告活动</Select.Option>
							<Select.Option value="suggest_negative">
								建议添加否定关键词
							</Select.Option>
							<Select.Option value="suggest_bid_increase">
								建议提高竞价
							</Select.Option>
							<Select.Option value="suggest_bid_decrease">
								建议降低竞价
							</Select.Option>
							<Select.Option value="suggest_budget_increase">
								建议增加预算
							</Select.Option>
							<Select.Option value="diagnose_zero_spend">
								诊断零花费原因
							</Select.Option>
							<Select.Option value="flag_budget_risk">
								预算耗尽风险
							</Select.Option>
							<Select.Option value="attribution_reminder">
								归因窗口提醒
							</Select.Option>
							<Select.Option value="negative_buffer_reminder">
								否定词生效提醒
							</Select.Option>
						</Select>
					</Form.Item>
				</Form>
			</Modal>
		</Spin>
	);
}
