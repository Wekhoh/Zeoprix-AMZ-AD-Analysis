import { Table } from "antd";
import type { OperationLog } from "../types/api";

interface OperationLogsTabProps {
	data: OperationLog[];
}

const columns = [
	{ title: "日期", dataIndex: "date", key: "date", width: 110 },
	{ title: "时间", dataIndex: "time", key: "time", width: 70 },
	{ title: "变更类型", dataIndex: "change_type", key: "change", width: 200 },
	{ title: "修改前", dataIndex: "from_value", key: "from", width: 150 },
	{ title: "修改后", dataIndex: "to_value", key: "to", width: 150 },
	{ title: "层级", dataIndex: "level_type", key: "level", width: 90 },
];

/**
 * Operation-logs tab body for CampaignDetail — pure render of bid / budget /
 * status change log rows. Extracted from CampaignDetail.tsx (F2-γ2).
 */
export default function OperationLogsTab({ data }: OperationLogsTabProps) {
	return (
		<Table<OperationLog>
			columns={columns}
			dataSource={data}
			rowKey="id"
			size="small"
			scroll={{ x: 1000 }}
		/>
	);
}
