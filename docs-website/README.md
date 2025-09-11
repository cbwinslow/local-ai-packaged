# Local AI Packaged - Documentation Website

This is a comprehensive Next.js documentation website for the Local AI Packaged repository. It provides interactive, searchable documentation with sophisticated features for exploring government data analysis tools and methodologies.

## Features

- 🔍 **Interactive Search**: Full-text search across all documentation
- 📚 **Auto-Generated Docs**: Automatically extracts documentation from Python codebase
- 🎨 **Modern UI**: Beautiful, responsive design with dark mode support
- 📊 **Methodology Framework**: Detailed analysis methodologies with examples
- 🛠️ **Tool Showcase**: Comprehensive overview of all Python tools and scripts
- 🚀 **Quick Start Guides**: Step-by-step setup and usage instructions
- 📈 **Interactive Diagrams**: Mermaid diagrams for system architecture and workflows
- 🎯 **Table of Contents**: Auto-generated navigation for long pages
- 💻 **Code Examples**: Syntax-highlighted code with copy functionality

## Quick Start

### Development

```bash
# Navigate to docs website
cd docs-website

# Install dependencies
npm install

# Start development server
npm run dev

# Open http://localhost:3001
```

### Build for Production

```bash
# Build static site
npm run build

# Start production server
npm start
```

## Documentation Generation

The website includes auto-generated documentation from the Python codebase:

```bash
# Generate latest docs from codebase
npm run generate-docs

# Or run manually
python scripts/generate_docs.py
```

This will:
- Scan all Python files in the repository
- Extract functions, classes, and docstrings
- Generate structured JSON documentation
- Make it available to the website

## Architecture

### Components

- **Layout**: Main layout with navigation and search
- **SearchModal**: Global search functionality
- **Navigation**: Hierarchical navigation sidebar
- **TableOfContents**: Auto-generated page navigation
- **CodeBlock**: Syntax-highlighted code display
- **Diagrams**: Mermaid diagram rendering
- **MethodologyFramework**: Analysis methodology showcase
- **AutoDocumentation**: Auto-generated API documentation

### Pages

- **Homepage** (`/`): Overview and feature showcase
- **Quick Start** (`/getting-started/quick-start`): Setup guide
- **Methodology** (`/analysis/methodology`): Analysis frameworks
- **Tools Overview** (`/tools/overview`): Python tools documentation
- **Auto-generated pages**: Created from navigation structure

### Data Sources

- **Static Content**: Manually written documentation pages
- **Generated Content**: Auto-extracted from Python codebase
- **Configuration**: Navigation structure and metadata

## Customization

### Adding New Pages

1. Create page component in `src/pages/`
2. Add to navigation structure in `src/components/Navigation.tsx`
3. Include table of contents for long pages

### Updating Methodology

Edit `src/components/MethodologyFramework.tsx` to add new analysis methods, tools, or examples.

### Adding Diagrams

Use Mermaid syntax in the `COMMON_DIAGRAMS` object in `src/components/Diagrams.tsx`.

## Deployment

The website can be deployed as a static site:

```bash
# Build for static export
npm run build

# Deploy the `out/` directory to any static hosting service
```

## Technology Stack

- **Framework**: Next.js 14 with React 18
- **Styling**: Tailwind CSS with custom components
- **Search**: Fuse.js for client-side search
- **Diagrams**: Mermaid for technical diagrams
- **Syntax Highlighting**: react-syntax-highlighter
- **Icons**: Heroicons
- **Documentation**: Auto-generated from AST parsing

## File Structure

```
docs-website/
├── src/
│   ├── components/        # Reusable React components
│   ├── pages/            # Next.js pages
│   ├── styles/           # Global CSS and Tailwind
│   └── data/             # Generated documentation data
├── scripts/              # Documentation generation scripts
├── public/               # Static assets
└── package.json          # Dependencies and scripts
```

## Contributing

1. Follow the existing component patterns
2. Add proper TypeScript types
3. Include responsive design considerations
4. Test with both light and dark modes
5. Ensure accessibility compliance

## License

This documentation website is part of the Local AI Packaged project and follows the same license terms.