import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  basePath: process.env.NODE_ENV === "production" ? "/wc2026-quiniela" : "",
  images: {
    unoptimized: true,
    remotePatterns: [{ protocol: "https", hostname: "flagcdn.com" }],
  },
  trailingSlash: true,
  turbopack: {
    root: __dirname,
  },
};

export default nextConfig;
