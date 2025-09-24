/** @type {import('next').NextConfig} */
const nextConfig = {
  // Remove invalid experimental options
  // No appDir or other unsupported flags
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'cdn.jsdelivr.net',  // For icons and assets
      },
      {
        protocol: 'https',
        hostname: 'unpkg.com',  // For library assets
      },
      {
        protocol: 'https',
        hostname: 'github.com',  // For GitHub-hosted images
      },
      // Add more trusted domains as needed (e.g., your CDN)
      // {
      //   protocol: 'https',
      //   hostname: 'your-cdn.com',
      // },
    ],
  },
  // Add Tailwind CSS support if needed
  webpack: (config) => {
    config.resolve.alias.canvaskit = false;
    return config;
  },
}

module.exports = nextConfig
