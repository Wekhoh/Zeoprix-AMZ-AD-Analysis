import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import dayjs, { type Dayjs } from "dayjs";

import "dayjs/locale/zh-cn";

dayjs.locale("zh-cn");

const PARAM_DATE_FROM = "date_from";
const PARAM_DATE_TO = "date_to";
const PARAM_CAMPAIGN_ID = "campaign_id";
const PARAM_MARKETPLACE_ID = "marketplace_id";
const DATE_FORMAT = "YYYY-MM-DD";

export interface FilterParams {
	dateFrom: Dayjs | null;
	dateTo: Dayjs | null;
	campaignId: number | undefined;
	marketplaceId: number | undefined;
	setDateRange: (from: Dayjs | null, to: Dayjs | null) => void;
	setCampaignId: (id: number | undefined) => void;
	setMarketplaceId: (id: number | undefined) => void;
	clearFilters: () => void;
	/** Build query string like "?date_from=X&date_to=Y&campaign_id=Z&marketplace_id=W" */
	buildQueryString: () => string;
}

export function useFilterParams(): FilterParams {
	const [searchParams, setSearchParams] = useSearchParams();

	const dateFrom = useMemo(() => {
		const v = searchParams.get(PARAM_DATE_FROM);
		return v ? dayjs(v) : null;
	}, [searchParams]);

	const dateTo = useMemo(() => {
		const v = searchParams.get(PARAM_DATE_TO);
		return v ? dayjs(v) : null;
	}, [searchParams]);

	const campaignId = useMemo(() => {
		const v = searchParams.get(PARAM_CAMPAIGN_ID);
		return v ? Number(v) : undefined;
	}, [searchParams]);

	const marketplaceId = useMemo(() => {
		const v = searchParams.get(PARAM_MARKETPLACE_ID);
		if (v) return Number(v);
		const stored = localStorage.getItem("amz_marketplace_id");
		return stored ? Number(stored) : undefined;
	}, [searchParams]);

	const setDateRange = useCallback(
		(from: Dayjs | null, to: Dayjs | null) => {
			setSearchParams((prev) => {
				const next = new URLSearchParams(prev);
				if (from) {
					next.set(PARAM_DATE_FROM, from.format(DATE_FORMAT));
				} else {
					next.delete(PARAM_DATE_FROM);
				}
				if (to) {
					next.set(PARAM_DATE_TO, to.format(DATE_FORMAT));
				} else {
					next.delete(PARAM_DATE_TO);
				}
				return next;
			});
		},
		[setSearchParams],
	);

	const setCampaignId = useCallback(
		(id: number | undefined) => {
			setSearchParams((prev) => {
				const next = new URLSearchParams(prev);
				if (id !== undefined) {
					next.set(PARAM_CAMPAIGN_ID, String(id));
				} else {
					next.delete(PARAM_CAMPAIGN_ID);
				}
				return next;
			});
		},
		[setSearchParams],
	);

	const setMarketplaceId = useCallback(
		(id: number | undefined) => {
			setSearchParams((prev) => {
				const next = new URLSearchParams(prev);
				if (id !== undefined) {
					next.set(PARAM_MARKETPLACE_ID, String(id));
				} else {
					next.delete(PARAM_MARKETPLACE_ID);
				}
				return next;
			});
		},
		[setSearchParams],
	);

	const clearFilters = useCallback(() => {
		setSearchParams({});
	}, [setSearchParams]);

	const buildQueryString = useCallback(() => {
		const params = new URLSearchParams();
		if (dateFrom) params.set(PARAM_DATE_FROM, dateFrom.format(DATE_FORMAT));
		if (dateTo) params.set(PARAM_DATE_TO, dateTo.format(DATE_FORMAT));
		if (campaignId !== undefined)
			params.set(PARAM_CAMPAIGN_ID, String(campaignId));
		if (marketplaceId !== undefined)
			params.set(PARAM_MARKETPLACE_ID, String(marketplaceId));
		const str = params.toString();
		return str ? `?${str}` : "";
	}, [dateFrom, dateTo, campaignId, marketplaceId]);

	return {
		dateFrom,
		dateTo,
		campaignId,
		marketplaceId,
		setDateRange,
		setCampaignId,
		setMarketplaceId,
		clearFilters,
		buildQueryString,
	};
}
