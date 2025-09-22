/** @type {import('next').NextConfig} */
const nextConfig = {
  // Remove invalid experimental options
  // No appDir or other unsupported flags
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },
  // Add Tailwind CSS support if needed
  webpack: (config) => {
    config.resolve.alias.canvaskit = false;
    return config;
  },
}

module.exports = nextConfig
