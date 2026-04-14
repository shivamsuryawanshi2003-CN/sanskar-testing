import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  typescript: {
    ignoreBuildErrors: false,
  },
  eslint: {
    dirs: ["src"],
  },
  allowedDevOrigins: [
    "192.168.1.47",
    "192.168.1.48",
    "192.168.1.17",
    "192.168.1.53",
    "localhost",
    "127.0.0.1",
  ],
};

export default nextConfig;
