/**
 * CJS/ESM interop shim for echarts-for-react.
 *
 * The package ships as CJS at `lib/core.js` (with `"main": "lib/index.js"`)
 * and ESM at `esm/core.js`. Vite's dep pre-bundler resolves the subpath
 * `echarts-for-react/lib/core` to the CJS file and wraps it as
 * `export default require_core()`, handing consumers the whole CommonJS
 * exports object `{ default, __esModule }` instead of the
 * `EChartsReactCore` class. Rendering that object throws
 * `Element type is invalid: got: object`.
 *
 * This shim unwraps `.default` when present, so callers can use a normal
 * `import ReactECharts from "../utils/reactEcharts"` regardless of whether
 * Vite's interop or the underlying package is later fixed.
 */
import * as CoreModule from "echarts-for-react/lib/core";

// Vite wraps the CJS module as `export default require_core()`, so the ES
// namespace looks like `{ default: { default: EChartsReactCore, __esModule: true } }`.
// Two-level unwrap handles both Vite's current double-nesting and a
// hypothetical future ESM-correct resolution (single-level or none).
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const namespaced = CoreModule as any;
const inner = namespaced.default ?? namespaced;
const resolved = inner?.default ?? inner;

export default resolved as typeof import("echarts-for-react/lib/core").default;
