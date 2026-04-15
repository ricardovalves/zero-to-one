import { dirname } from "path";
import { fileURLToPath } from "url";
import nextConfig from "eslint-config-next";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/** @type {import("eslint").Linter.Config[]} */
const config = [
  ...nextConfig,
  {
    rules: {
      // React Compiler's set-state-in-effect rule is too strict for common
      // initialisation patterns (e.g. restoring a draft from localStorage on
      // mount, or syncing a default value once data loads). These are
      // legitimate single-run effects, not cascading-render risks.
      "react-hooks/set-state-in-effect": "off",
      // react-hook-form's watch() API is flagged by the React Compiler plugin;
      // this is a known false positive — downgrade to warning only.
      "react-hooks/incompatible-library": "warn",
    },
  },
];

export default config;
