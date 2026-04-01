import { useEffect, useState } from "react";
import { Select } from "antd";
import api from "../api/client";
import type { Campaign } from "../types/api";

interface CampaignFilterProps {
	value: number | undefined;
	onChange: (id: number | undefined) => void;
}

export default function CampaignFilter({
	value,
	onChange,
}: CampaignFilterProps) {
	const [campaigns, setCampaigns] = useState<Campaign[]>([]);
	const [loading, setLoading] = useState(false);

	useEffect(() => {
		// eslint-disable-next-line react-hooks/set-state-in-effect -- loading indicator for async fetch
		setLoading(true);
		api
			.get<Campaign[]>("/campaigns")
			.then((res) => setCampaigns(res.data))
			.finally(() => setLoading(false));
	}, []);

	const options = [
		{ label: "全部广告活动", value: "__all__" as const },
		...campaigns.map((c) => ({
			label: c.name,
			value: String(c.id),
		})),
	];

	const handleChange = (selected: string) => {
		if (selected === "__all__") {
			onChange(undefined);
		} else {
			onChange(Number(selected));
		}
	};

	return (
		<Select
			showSearch
			value={value !== undefined ? String(value) : "__all__"}
			onChange={handleChange}
			options={options}
			loading={loading}
			optionFilterProp="label"
			style={{ minWidth: 260 }}
			placeholder="选择广告活动"
		/>
	);
}
