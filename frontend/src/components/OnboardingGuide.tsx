import { useState } from "react";
import { Button, Checkbox, Modal, Steps } from "antd";
import {
	SettingOutlined,
	UploadOutlined,
	DashboardOutlined,
	RocketOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { useTheme } from "../hooks/useTheme";

const ONBOARDING_KEY = "amz-onboarding-done";

interface OnboardingGuideProps {
	open: boolean;
	onClose: () => void;
}

const STEPS = [
	{
		title: "设置产品信息",
		icon: <SettingOutlined />,
		description:
			"首先在系统设置中配置您的产品 SKU、成本和 FBA 费用信息，这些数据将用于计算利润和盈亏平衡 ACOS。",
		buttonText: "去设置",
		path: "/settings",
	},
	{
		title: "上传广告数据",
		icon: <UploadOutlined />,
		description:
			"从亚马逊广告后台导出展示位置 CSV 文件和操作日志 TXT 文件，然后上传到系统中。系统会自动解析和去重。",
		buttonText: "去导入",
		path: "/import",
	},
	{
		title: "查看仪表盘",
		icon: <DashboardOutlined />,
		description:
			"数据导入后，仪表盘会自动汇总所有广告活动的 KPI 指标，包括花费、订单、ROAS、ACOS 等，并提供趋势图和预警信息。",
		buttonText: "去查看",
		path: "/",
	},
	{
		title: "探索更多功能",
		icon: <RocketOutlined />,
		description:
			"您还可以使用搜索词分析（4-Bucket 框架）、自动化规则、对比分析、智能建议等高级功能来优化广告表现。",
		buttonText: "开始使用",
		path: "",
	},
];

export default function OnboardingGuide({
	open,
	onClose,
}: OnboardingGuideProps) {
	const navigate = useNavigate();
	const { isDark } = useTheme();
	const [currentStep, setCurrentStep] = useState(0);
	const [dontShowAgain, setDontShowAgain] = useState(false);

	const handleClose = () => {
		if (dontShowAgain) {
			localStorage.setItem(ONBOARDING_KEY, "true");
		}
		onClose();
	};

	const handleStepAction = (path: string) => {
		if (path) {
			navigate(path);
		}
		handleClose();
	};

	const step = STEPS[currentStep];
	const textColor = isDark ? "#D1D5DB" : "#374151";

	return (
		<Modal
			title="欢迎使用 AMZ Ad Tracker"
			open={open}
			onCancel={handleClose}
			footer={null}
			width={600}
		>
			<Steps
				current={currentStep}
				size="small"
				style={{ marginBottom: 32 }}
				items={STEPS.map((s) => ({ title: s.title, icon: s.icon }))}
			/>

			<div
				style={{
					padding: "16px 0",
					minHeight: 120,
				}}
			>
				<p
					style={{
						fontSize: 14,
						lineHeight: 1.8,
						color: textColor,
						marginBottom: 24,
					}}
				>
					{step.description}
				</p>

				<div style={{ display: "flex", justifyContent: "space-between" }}>
					<div style={{ display: "flex", gap: 8 }}>
						{currentStep > 0 && (
							<Button onClick={() => setCurrentStep((prev) => prev - 1)}>
								上一步
							</Button>
						)}
						{currentStep < STEPS.length - 1 && (
							<Button
								type="default"
								onClick={() => setCurrentStep((prev) => prev + 1)}
							>
								下一步
							</Button>
						)}
					</div>
					<Button type="primary" onClick={() => handleStepAction(step.path)}>
						{step.buttonText}
					</Button>
				</div>
			</div>

			<div
				style={{
					borderTop: `1px solid ${isDark ? "#2A2F3A" : "#E5E7EB"}`,
					paddingTop: 12,
					marginTop: 16,
				}}
			>
				<Checkbox
					checked={dontShowAgain}
					onChange={(e) => setDontShowAgain(e.target.checked)}
				>
					不再显示
				</Checkbox>
			</div>
		</Modal>
	);
}

export function isOnboardingDismissed(): boolean {
	return localStorage.getItem(ONBOARDING_KEY) === "true";
}
