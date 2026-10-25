import type { NextConfig } from "next";
const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    // Local development only: production requests route via the root Vercel Services configuration.
    return process.env.NODE_ENV === "development"
      ? [{ source: "/api/:path*", destination: `${process.env.BACKEND_URL || "http://127.0.0.1:8000"}/api/:path*` }]
      : [];
  },
};
export default nextConfig;
