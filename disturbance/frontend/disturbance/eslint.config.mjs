import globals from "globals";
import jsLint from "@eslint/js";
import pluginVue from "eslint-plugin-vue";
import vueEslintParser from "vue-eslint-parser";

const projectGlobals = {
  ...globals.browser,
  ...globals.node,
  ...globals.jquery,
  es6: true,
  moment: true,
  swal: true,
  bootstrap: true,
  env: true,
  _: true, // Lodash
};

export default [
  jsLint.configs.recommended,
  ...pluginVue.configs["flat/essential"],
  {
    ignores: [".venv/", ".env/", ".env", "node_modules/"],
  },
  {
    files: ["**/*.{js,mjs,cjs,ts,mts,jsx,tsx}"],
    languageOptions: {
      parserOptions: {
        sourceType: "module",
        ecmaFeatures: {
          jsx: true,
        },
      },
      globals: projectGlobals,
    },
  },
  {
    files: ["**/*.{jsx,tsx}"],
    plugins: {
      vue: pluginVue, // Gives this block access to Vue rules
    },
    rules: {
      "no-unused-vars": "off", // Off ONLY for JSX files
      "vue/no-unused-vars": "warn", // On ONLY for JSX files to track components
    },
  },
  {
    files: ["src/**/*.vue"],
    plugins: {
      vue: pluginVue,
    },
    languageOptions: {
      sourceType: "module",
      ecmaVersion: 12,
      parser: vueEslintParser,
      parserOptions: {
        sourceType: "module",
        ecmaVersion: 12,
      },
      globals: projectGlobals,
    },
    rules: {
      "no-redeclare": "warn",
      "no-unused-vars": "warn",
      "vue/no-mutating-props": "off",
    },
  },
];
