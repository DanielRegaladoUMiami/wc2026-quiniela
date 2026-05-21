import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [{ protocol: "https", hostname: "flagcdn.com" }],
  },
  turbopack: {
    root: __dirname,
  },
};

export default nextConfig;
