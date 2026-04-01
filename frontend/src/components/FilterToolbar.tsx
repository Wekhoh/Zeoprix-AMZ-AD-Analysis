import { Flex } from "antd";
import DateRangeFilter from "./DateRangeFilter";
import CampaignFilter from "./CampaignFilter";
import { useFilterParams } from "../hooks/useFilterParams";

interface FilterToolbarProps {
	showCampaignFilter?: boolean;
}

export default function FilterToolbar({
	showCampaignFilter = true,
}: FilterToolbarProps) {
	const { dateFrom, dateTo, campaignId, setDateRange, setCampaignId } =
		useFilterParams();

	return (
		<Flex gap={12} align="center" wrap="wrap" style={{ marginBottom: 16 }}>
			<DateRangeFilter
				dateFrom={dateFrom}
				dateTo={dateTo}
				onChange={setDateRange}
			/>
			{showCampaignFilter && (
				<CampaignFilter value={campaignId} onChange={setCampaignId} />
			)}
		</Flex>
	);
}
