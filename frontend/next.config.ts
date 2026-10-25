import type { NextConfig } from "next";
const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    // Preserve same-origin cookie and CSRF behavior in split Vercel deployments.
    // Local Docker/dev keeps using BACKEND_URL; Vercel uses BACKEND_ORIGIN.
    const backend = process.env.BACKEND_ORIGIN
      || process.env.BACKEND_URL
      || (process.env.NODE_ENV === "development" ? "http://127.0.0.1:8000" : "");
    return backend
      ? [{ source: "/api/:path*", destination: `${backend.replace(/\/+$/, "")}/api/:path*` }]
      : [];
  },
};
export default nextConfig;
