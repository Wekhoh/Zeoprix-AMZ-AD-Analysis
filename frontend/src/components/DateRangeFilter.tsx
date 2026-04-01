import { useMemo } from "react";
import { DatePicker, Space, Button } from "antd";
import dayjs, { type Dayjs } from "dayjs";

const { RangePicker } = DatePicker;

interface DateRangeFilterProps {
	dateFrom: Dayjs | null;
	dateTo: Dayjs | null;
	onChange: (from: Dayjs | null, to: Dayjs | null) => void;
}

const PRESETS = [
	{ label: "最近7天", days: 7 },
	{ label: "最近14天", days: 14 },
	{ label: "最近30天", days: 30 },
] as const;

export default function DateRangeFilter({
	dateFrom,
	dateTo,
	onChange,
}: DateRangeFilterProps) {
	const value = useMemo<[Dayjs, Dayjs] | null>(() => {
		if (dateFrom && dateTo) return [dateFrom, dateTo];
		return null;
	}, [dateFrom, dateTo]);

	const handleRangeChange = (dates: [Dayjs | null, Dayjs | null] | null) => {
		if (dates && dates[0] && dates[1]) {
			onChange(dates[0], dates[1]);
		} else {
			onChange(null, null);
		}
	};

	const handlePreset = (days: number) => {
		const to = dayjs();
		const from = dayjs().subtract(days - 1, "day");
		onChange(from, to);
	};

	const handleClearAll = () => {
		onChange(null, null);
	};

	return (
		<Space size="small" wrap>
			<RangePicker
				value={value}
				onChange={handleRangeChange}
				allowClear
				style={{ width: 260 }}
			/>
			{PRESETS.map((p) => (
				<Button key={p.days} size="small" onClick={() => handlePreset(p.days)}>
					{p.label}
				</Button>
			))}
			<Button size="small" onClick={handleClearAll}>
				全部
			</Button>
		</Space>
	);
}
