import { useState } from "react";
import { Button, Flex, Input, Popover, Select, Space, message } from "antd";
import { SaveOutlined, DeleteOutlined } from "@ant-design/icons";
import DateRangeFilter from "./DateRangeFilter";
import CampaignFilter from "./CampaignFilter";
import { useFilterParams } from "../hooks/useFilterParams";

interface FilterToolbarProps {
	showCampaignFilter?: boolean;
}

interface FilterPreset {
	name: string;
	params: string; // URL search params string like "date_from=X&date_to=Y"
}

const PRESETS_KEY = "amz_filter_presets";

function loadPresets(): FilterPreset[] {
	try {
		return JSON.parse(localStorage.getItem(PRESETS_KEY) || "[]");
	} catch {
		return [];
	}
}

function savePresets(presets: FilterPreset[]) {
	localStorage.setItem(PRESETS_KEY, JSON.stringify(presets));
}

export default function FilterToolbar({
	showCampaignFilter = true,
}: FilterToolbarProps) {
	const {
		dateFrom,
		dateTo,
		campaignId,
		setDateRange,
		setCampaignId,
		buildQueryString,
	} = useFilterParams();

	const [presets, setPresets] = useState<FilterPreset[]>(loadPresets);
	const [saveName, setSaveName] = useState("");
	const [saveOpen, setSaveOpen] = useState(false);

	const handleSave = () => {
		const name = saveName.trim();
		if (!name) return;
		const params = buildQueryString().replace(/^\?/, "");
		const updated = [
			...presets.filter((p) => p.name !== name),
			{ name, params },
		];
		savePresets(updated);
		setPresets(updated);
		setSaveName("");
		setSaveOpen(false);
		message.success(`筛选预设「${name}」已保存`);
	};

	const handleLoad = (params: string) => {
		const sp = new URLSearchParams(params);
		const df = sp.get("date_from");
		const dt = sp.get("date_to");
		const cid = sp.get("campaign_id");

		// We need to import dayjs for date parsing
		import("dayjs").then(({ default: dayjs }) => {
			setDateRange(df ? dayjs(df) : null, dt ? dayjs(dt) : null);
			setCampaignId(cid ? Number(cid) : undefined);
		});
	};

	const handleDelete = (name: string) => {
		const updated = presets.filter((p) => p.name !== name);
		savePresets(updated);
		setPresets(updated);
		message.info(`预设「${name}」已删除`);
	};

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
			{presets.length > 0 && (
				<Select
					placeholder="预设"
					style={{ minWidth: 120 }}
					allowClear
					size="small"
					options={presets.map((p) => ({ label: p.name, value: p.params }))}
					onChange={(params) => params && handleLoad(params)}
					dropdownRender={(menu) => (
						<>
							{menu}
							<div
								style={{
									borderTop: "1px solid #f0f0f0",
									padding: "4px 8px",
									fontSize: 12,
									color: "#999",
								}}
							>
								{presets.map((p) => (
									<div
										key={p.name}
										style={{
											display: "flex",
											justifyContent: "space-between",
											alignItems: "center",
											padding: "2px 0",
										}}
									>
										<span>{p.name}</span>
										<Button
											type="text"
											danger
											size="small"
											icon={<DeleteOutlined />}
											onClick={(e) => {
												e.stopPropagation();
												handleDelete(p.name);
											}}
										/>
									</div>
								))}
							</div>
						</>
					)}
				/>
			)}
			<Popover
				open={saveOpen}
				onOpenChange={setSaveOpen}
				trigger="click"
				content={
					<Space.Compact>
						<Input
							placeholder="预设名称"
							value={saveName}
							onChange={(e) => setSaveName(e.target.value)}
							onPressEnter={handleSave}
							size="small"
							style={{ width: 140 }}
						/>
						<Button
							type="primary"
							size="small"
							onClick={handleSave}
							disabled={!saveName.trim()}
						>
							保存
						</Button>
					</Space.Compact>
				}
			>
				<Button
					size="small"
					icon={<SaveOutlined />}
					title="保存当前筛选为预设"
				/>
			</Popover>
		</Flex>
	);
}
