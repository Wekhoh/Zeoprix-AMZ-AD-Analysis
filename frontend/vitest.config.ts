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
		// Keep unit tests fast; hook timeout 5s is enough for our size
		testTimeout: 5000,
		clearMocks: true,
		restoreMocks: true,
	},
});
