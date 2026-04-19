// Global test setup. Loaded before every test file via vitest.config.ts.
// Adds jest-dom matchers (toBeInTheDocument, toHaveTextContent, etc.) to expect().
import "@testing-library/jest-dom/vitest";

// Polyfill window.matchMedia — jsdom does not ship it, and antd's responsive
// grid / breakpoint observer call it synchronously during mount. Without this
// any page test that renders antd components crashes with
// "window.matchMedia is not a function".
if (typeof window !== "undefined" && typeof window.matchMedia !== "function") {
	window.matchMedia = (query: string) => ({
		matches: false,
		media: query,
		onchange: null,
		addListener: () => {}, // legacy
		removeListener: () => {}, // legacy
		addEventListener: () => {},
		removeEventListener: () => {},
		dispatchEvent: () => false,
	});
}

// Polyfill ResizeObserver — jsdom lacks it and antd's Table / some rc-components
// subscribe to resize events during mount.
if (
	typeof window !== "undefined" &&
	typeof window.ResizeObserver === "undefined"
) {
	window.ResizeObserver = class ResizeObserver {
		observe() {}
		unobserve() {}
		disconnect() {}
	};
}
