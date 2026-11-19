import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  ...(process.env.NODE_ENV === "development"
    ? {
        async rewrites() {
          const backend = process.env.KEYZONE_DEV_BACKEND;
          if (!backend) return [];
          return ["/admin", "/admin.js", "/admin-time.js", "/admin.css", "/api/admin/:path*"].map(source => ({
            source,
            destination: backend + source,
          }));
        },
      }
    : { output: "export" }),
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
