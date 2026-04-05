import { Card, Col, Row, Skeleton } from "antd";

type Variant = "dashboard" | "table" | "cards";

interface PageSkeletonProps {
	variant?: Variant;
}

function DashboardSkeleton() {
	return (
		<div>
			{/* KPI cards row */}
			<Row gutter={16} style={{ marginBottom: 24 }}>
				{[1, 2, 3, 4].map((i) => (
					<Col span={6} key={i}>
						<Card>
							<Skeleton
								active
								paragraph={{ rows: 1 }}
								title={{ width: "40%" }}
							/>
						</Card>
					</Col>
				))}
			</Row>
			{/* Chart + sidebar */}
			<Row gutter={16} style={{ marginBottom: 24 }}>
				<Col span={16}>
					<Card>
						<Skeleton.Node active style={{ width: "100%", height: 350 }}>
							<span />
						</Skeleton.Node>
					</Card>
				</Col>
				<Col span={8}>
					<Card>
						<Skeleton.Node active style={{ width: "100%", height: 350 }}>
							<span />
						</Skeleton.Node>
					</Card>
				</Col>
			</Row>
			{/* Bottom row */}
			<Row gutter={16}>
				<Col span={8}>
					<Card>
						<Skeleton active paragraph={{ rows: 4 }} />
					</Card>
				</Col>
				<Col span={16}>
					<Card>
						<Skeleton active paragraph={{ rows: 4 }} />
					</Card>
				</Col>
			</Row>
		</div>
	);
}

function TableSkeleton() {
	return (
		<div>
			{/* Header area */}
			<Skeleton.Input
				active
				size="small"
				style={{ width: 200, marginBottom: 16 }}
			/>
			{/* Table rows */}
			<Card>
				{[1, 2, 3, 4, 5, 6].map((i) => (
					<Skeleton
						key={i}
						active
						title={false}
						paragraph={{ rows: 1, width: "100%" }}
						style={{ marginBottom: i < 6 ? 12 : 0 }}
					/>
				))}
			</Card>
		</div>
	);
}

function CardsSkeleton() {
	return (
		<div>
			{[1, 2, 3].map((i) => (
				<Card key={i} style={{ marginBottom: 16 }}>
					<Skeleton active paragraph={{ rows: 2 }} title={{ width: "30%" }} />
				</Card>
			))}
		</div>
	);
}

const VARIANT_MAP: Record<Variant, () => JSX.Element> = {
	dashboard: DashboardSkeleton,
	table: TableSkeleton,
	cards: CardsSkeleton,
};

export default function PageSkeleton({ variant = "table" }: PageSkeletonProps) {
	const Component = VARIANT_MAP[variant];
	return <Component />;
}
