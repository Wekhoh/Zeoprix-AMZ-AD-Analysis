import { useCallback, useEffect, useState } from "react";
import api from "../api/client";
import type { MarketplaceItem } from "../types/api";

const STORAGE_KEY = "amz_marketplace_id";

export interface UseMarketplaceReturn {
	marketplaceId: number | undefined;
	setMarketplaceId: (id: number | undefined) => void;
	marketplaces: MarketplaceItem[];
}

export function useMarketplace(): UseMarketplaceReturn {
	const [marketplaces, setMarketplaces] = useState<MarketplaceItem[]>([]);
	const [marketplaceId, setMarketplaceIdState] = useState<number | undefined>(
		() => {
			const stored = localStorage.getItem(STORAGE_KEY);
			return stored ? Number(stored) : undefined;
		},
	);

	useEffect(() => {
		api.get<MarketplaceItem[]>("/settings/marketplaces").then((res) => {
			setMarketplaces(res.data);
		});
	}, []);

	const setMarketplaceId = useCallback((id: number | undefined) => {
		setMarketplaceIdState(id);
		if (id !== undefined) {
			localStorage.setItem(STORAGE_KEY, String(id));
		} else {
			localStorage.removeItem(STORAGE_KEY);
		}
	}, []);

	return { marketplaceId, setMarketplaceId, marketplaces };
}
