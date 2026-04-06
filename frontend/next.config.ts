import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  env: {
    // Fallback so builds without the Vercel env var still reach the backend
    NEXT_PUBLIC_API_URL:
      process.env.NEXT_PUBLIC_API_URL ||
      "https://caractr-production.up.railway.app",
  },
};

export default nextConfig;
