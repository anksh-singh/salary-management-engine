/** @type {import('next').NextConfig} */
const nextConfig = {
  agentRules: false,
  basePath: "/salary",
  async rewrites() {
    const backendUrl = process.env.BACKEND_API_URL;
    if (!backendUrl) {
      throw new Error("BACKEND_API_URL must be set to the backend origin");
    }
    return [{ source: "/api/:path*", destination: `${backendUrl}/api/:path*` }];
  },
};

export default nextConfig;
