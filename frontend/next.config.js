/** @type {import('next').NextConfig} */
// output: 'export' creates static HTML for packaging - served by FastAPI at same origin, so /api works.
// Rewrites cannot be used with output: 'export'. For dev, set NEXT_PUBLIC_API_URL=http://localhost:8080 in .env.local
const nextConfig = {
  output: 'export',
};

module.exports = nextConfig;
