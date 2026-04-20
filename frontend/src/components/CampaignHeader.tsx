import { Tag, Typography } from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import { Link } from "react-router-dom";
import type { CampaignDetail } from "../types/api";

const { Title, Text } = Typography;

interface CampaignHeaderProps {
	campaign: CampaignDetail;
	isDark: boolean;
	attributionDays: number;
	isDynamicUpDown: boolean;
}

/**
 * Header block for the CampaignDetail page — back link + title row + metadata strip.
 * Extracted from CampaignDetail.tsx Section A (F2-β).
 */
export default function CampaignHeader({
	campaign,
	isDark,
	attributionDays,
	isDynamicUpDown,
}: CampaignHeaderProps) {
	const statusColor =
		campaign.status === "Delivering"
			? "green"
			: campaign.status === "Paused"
				? "red"
				: "default";

	return (
		<div style={{ marginBottom: 16 }}>
			<Link
				to="/campaigns"
				style={{ color: "#1677ff", marginBottom: 8, display: "inline-block" }}
			>
				<ArrowLeftOutlined /> 返回广告活动列表
			</Link>
			<div
				style={{
					display: "flex",
					alignItems: "center",
					gap: 12,
					marginBottom: 8,
				}}
			>
				<Title level={2} style={{ margin: 0 }}>
					{campaign.name}
				</Title>
				<Tag color={statusColor}>{campaign.status}</Tag>
			</div>
			<div
				style={{
					display: "flex",
					gap: 24,
					color: isDark ? "#9CA3AF" : "#6B7280",
				}}
			>
				<Text>类型: {campaign.ad_type}</Text>
				<Text>竞价策略: {campaign.bidding_strategy}</Text>
				{isDynamicUpDown && <Tag color="orange">竞价可翻倍</Tag>}
				{campaign.base_bid != null && (
					<Text>基础出价: ${campaign.base_bid}</Text>
				)}
				<Text>归因窗口: {attributionDays} 天</Text>
				{campaign.portfolio && <Text>组合: {campaign.portfolio}</Text>}
				{campaign.first_date && campaign.last_date && (
					<Text>
						数据范围: {campaign.first_date} ~ {campaign.last_date}
					</Text>
				)}
			</div>
		</div>
	);
}
