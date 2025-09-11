# AI Platform Monitoring Dashboard

A comprehensive monitoring dashboard for the Local AI Platform, built with Next.js, TypeScript, and Tailwind CSS.

## Features

- **Real-time Monitoring**: Track system metrics and service status in real-time
- **Alert Management**: View and manage system alerts
- **Service Health**: Monitor the health of all platform services
- **Logs**: Access and search through system logs
- **Responsive Design**: Works on desktop and mobile devices

## Prerequisites

- Node.js 18+
- npm or yarn
- Docker (for local development with services)

## Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/coleam00/local-ai-packaged.git
   cd local-ai-packaged/dashboard
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Set up environment variables**
   Create a `.env.local` file in the dashboard directory with the following variables:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:3000/api
   NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
   ```

4. **Run the development server**
   ```bash
   npm run dev
   # or
   yarn dev
   ```
   Open [http://localhost:3001](http://localhost:3001) with your browser to see the dashboard.

## Development

### Available Scripts

- `npm run dev` - Start the development server
- `npm run build` - Build for production
- `npm start` - Start the production server
- `npm run lint` - Run ESLint
- `npm run format` - Format code with Prettier
- `npm run type-check` - Check TypeScript types

### Project Structure

```
src/
  components/     # Reusable UI components
  lib/           # Utility functions and API clients
  pages/         # Next.js pages
  styles/        # Global styles and Tailwind configuration
  types/         # TypeScript type definitions
```

## Deployment

The dashboard can be deployed to any platform that supports Next.js applications, including:

- Vercel
- Netlify
- Cloudflare Pages
- Self-hosted with Node.js

### Docker Deployment

Build the Docker image:
```bash
docker build -t local-ai-dashboard .
```

Run the container:
```bash
docker run -p 3001:3000 local-ai-dashboard
```

## Monitoring Stack

The dashboard integrates with the following monitoring services:

- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization
- **Loki**: Log aggregation
- **OpenSearch**: Distributed search and analytics

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
