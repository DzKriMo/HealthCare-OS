/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Proxy API calls to Django backend in development
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination:
          process.env.NODE_ENV === "development"
            ? "http://backend:8000/api/:path*"
            : "/api/:path*",
      },
    ];
  },
  // Allow images from MinIO/S3
  images: {
    remotePatterns: [
      {
        protocol: "http",
        hostname: "localhost",
        port: "9000",
      },
      {
        protocol: "https",
        hostname: "**.s3.amazonaws.com",
      },
    ],
  },
  // Transpile shared packages
  transpilePackages: ["@healthcare-os/types", "@healthcare-os/validators"],
};

module.exports = nextConfig;
