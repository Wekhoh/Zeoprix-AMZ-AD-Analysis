import { Card, Col, Row, Statistic } from "antd";
import {
	DollarOutlined,
	PercentageOutlined,
	RiseOutlined,
	ShoppingCartOutlined,
} from "@ant-design/icons";
import type { CampaignDetail } from "../types/api";
import { WowIndicator, type WowDeltas } from "../utils/wowDeltas";

interface CampaignKpiCardsProps {
	campaign: CampaignDetail;
	wowDeltas: WowDeltas | null;
}

/**
 * Four KPI Statistic cards (spend / orders / ROAS / ACOS) with optional
 * week-over-week indicators. Extracted from CampaignDetail.tsx Section B (F2-β).
 */
export default function CampaignKpiCards({
	campaign,
	wowDeltas,
}: CampaignKpiCardsProps) {
	return (
		<Row gutter={16} style={{ marginBottom: 24 }}>
			<Col xs={24} sm={12} lg={6}>
				<Card>
					<Statistic
						title="总花费"
						value={campaign.total_spend}
						precision={2}
						prefix={<DollarOutlined />}
						suffix="USD"
					/>
					{wowDeltas && <WowIndicator delta={wowDeltas.spend} />}
				</Card>
			</Col>
			<Col xs={24} sm={12} lg={6}>
				<Card>
					<Statistic
						title="总订单"
						value={campaign.total_orders}
						prefix={<ShoppingCartOutlined />}
					/>
					{wowDeltas && <WowIndicator delta={wowDeltas.orders} />}
				</Card>
			</Col>
			<Col xs={24} sm={12} lg={6}>
				<Card>
					<Statistic
						title="ROAS"
						value={campaign.roas ?? 0}
						precision={2}
						prefix={<RiseOutlined />}
					/>
					{wowDeltas && <WowIndicator delta={wowDeltas.roas} />}
				</Card>
			</Col>
			<Col xs={24} sm={12} lg={6}>
				<Card>
					<Statistic
						title="ACOS"
						value={campaign.acos ? campaign.acos * 100 : 0}
						precision={2}
						prefix={<PercentageOutlined />}
						suffix="%"
					/>
					{wowDeltas && <WowIndicator delta={wowDeltas.acos} invertColor />}
				</Card>
			</Col>
		</Row>
	);
}
