import nextConfig from 'eslint-config-next';

const config = [
  ...nextConfig,
  {
    name: 'local/rules',
    files: ['**/*.{js,jsx,mjs,ts,tsx,mts,cts}'],
    rules: {
      '@next/next/no-html-link-for-pages': 'off',
    },
  },
];

export default config;
