/** TypeScript interfaces matching backend Pydantic schemas */

export interface Campaign {
	id: number;
	name: string;
	ad_type: string;
	targeting_type: string;
	match_type: string | null;
	bidding_strategy: string;
	base_bid: number | null;
	portfolio: string | null;
	status: string;
	status_updated_at: string | null;
	spend?: number;
	orders?: number;
	sales?: number;
	acos?: number | null;
	roas?: number | null;
	impressions?: number;
	clicks?: number;
	daily_budget?: number | null;
}

export interface PlacementRecord {
	id: number;
	date: string;
	campaign_id: number;
	campaign_name: string | null;
	placement_type: string;
	bidding_strategy: string | null;
	impressions: number;
	clicks: number;
	spend: number;
	orders: number;
	sales: number;
	ctr: number | null;
	cpc: number | null;
	roas: number | null;
	acos: number | null;
	cvr: number | null;
	notes: string | null;
}

export interface OperationLog {
	id: number;
	date: string;
	time: string;
	operator: string | null;
	level_type: string;
	campaign_id: number;
	campaign_name: string | null;
	change_type: string;
	from_value: string | null;
	to_value: string | null;
}

export interface DashboardKPI {
	impressions: number;
	clicks: number;
	spend: number;
	orders: number;
	sales: number;
	ctr: number | null;
	cpc: number | null;
	roas: number | null;
	acos: number | null;
	cvr: number | null;
}

export interface DailyTrend {
	date: string;
	spend: number;
	orders: number;
	roas: number | null;
	impressions: number;
	clicks: number;
	sales: number;
	ctr: number | null;
	cpc: number | null;
	acos: number | null;
	cvr: number | null;
}

export interface TopCampaign {
	campaign_id: number;
	campaign_name: string;
	status: string;
	spend: number;
	orders: number;
	roas: number | null;
	impressions: number;
	clicks: number;
	sales: number;
}

export interface DashboardAlert {
	type: "high_acos" | "zero_orders" | "high_roas";
	severity: "warning" | "danger" | "success";
	campaign_name: string;
	value: number;
	message: string;
}

export interface ProfitData {
	has_cost_data: boolean;
	break_even_acos?: number | null;
	estimated_profit?: number;
}

export interface TacosData {
	value: number | null;
	has_data: boolean;
}

export interface DataFreshness {
	latest_data_date: string | null;
	last_import_at: string | null;
	last_import_file?: string | null;
	days_stale: number | null;
	level: "fresh" | "warning" | "stale" | "empty" | "unknown";
	message: string;
}

export interface DashboardData {
	kpi: DashboardKPI;
	daily_trend: DailyTrend[];
	top_campaigns: TopCampaign[];
	status_counts: Record<string, number>;
	alerts: DashboardAlert[];
	profit: ProfitData;
	tacos: TacosData;
	freshness?: DataFreshness;
}

export interface SummaryRow {
	date?: string;
	campaign_id?: number;
	campaign_name?: string;
	placement_type?: string;
	impressions: number;
	clicks: number;
	spend: number;
	orders: number;
	sales: number;
	ctr: number | null;
	cpc: number | null;
	roas: number | null;
	acos: number | null;
	cvr: number | null;
}

export interface CampaignDetail extends Campaign {
	total_impressions: number;
	total_clicks: number;
	total_spend: number;
	total_orders: number;
	total_sales: number;
	ctr: number | null;
	cpc: number | null;
	roas: number | null;
	acos: number | null;
	first_date: string | null;
	last_date: string | null;
}

export interface ImportDetail {
	message: string;
	level: string;
}

export interface ImportResult {
	imported: number;
	updated: number;
	skipped: number;
	errors: number;
	details: ImportDetail[];
}

export interface SearchTermSummary {
	search_term: string;
	impressions: number;
	clicks: number;
	ctr: number | null;
	spend: number;
	cpc: number | null;
	orders: number;
	sales: number;
	roas: number | null;
	acos: number | null;
	cvr: number | null;
}

export interface NegativeCandidate {
	search_term: string;
	clicks: number;
	spend: number;
	reason: string;
}

export interface MarketplaceItem {
	id: number;
	code: string;
	name: string;
	currency: string;
}

export interface BenchmarkCategory {
	key: string;
	label: string;
}

export interface BenchmarkComparison {
	metric: string;
	actual: number;
	benchmark: number;
	status: "above" | "below";
	diff_pct: number;
}

export interface BenchmarkResult {
	category: string;
	category_label: string;
	comparisons: BenchmarkComparison[];
}

export interface OrganicSalesRecord {
	id: number;
	date: string;
	total_sales: number;
	total_orders: number;
	notes: string | null;
}

export type SuggestionSeverity =
	| "critical"
	| "high"
	| "medium"
	| "opportunity"
	| "info";

export interface Suggestion {
	type: string;
	severity: SuggestionSeverity;
	priority: number;
	title: string;
	campaign_id: number | null;
	campaign_name: string;
	description: string;
	action: string;
	metric: Record<string, string | number>;
}
