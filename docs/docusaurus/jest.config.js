module.exports = {
  collectCoverage: true,
  collectCoverageFrom: ["src/**/*.{js,jsx}"],
  coverageDirectory: "coverage",
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],
  moduleNameMapper: {
    "\\.css$": "identity-obj-proxy",
    "@docusaurus/(BrowserOnly|ComponentCreator|constants|ExecutionEnvironment|Head|Interpolate|isInternalUrl|Link|Noop|renderRoutes|router|Translate|use.*)":
      "identity-obj-proxy",
    "@theme/(.*)": "@docusaurus/theme-classic/src/theme/$1",
    "@theme-original/(.*)": "identity-obj-proxy",
    "@site/(.*)": "website/$1",
  },
  transform: {
    "^.+\\.[jt]sx?$": "babel-jest",
  },
};
