import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
	plugins: [react()],
	test: {
		environment: "jsdom",
		globals: true,
		setupFiles: ["./tests/setup.ts"],
		include: ["tests/**/*.{test,spec}.{ts,tsx}"],
		exclude: ["node_modules/**", "dist/**"],
		// Hook default is 5s. Under full-suite parallel load (15+ test
		// files importing React + antd + ECharts) cold imports can push
		// mount-time waitFor assertions past 5s even on healthy machines.
		// 15s is generous enough to absorb import contention; isolated
		// file runs still complete in <2s, so this doesn't mask real hangs.
		testTimeout: 15000,
		clearMocks: true,
		restoreMocks: true,
	},
});
