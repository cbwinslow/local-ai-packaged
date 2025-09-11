#!/usr/bin/env python3
"""
Government Data Analysis Demo Script
===================================

This script demonstrates the complete government data analysis workflow:
1. Data ingestion from multiple sources
2. SQL analysis and querying
3. Report generation
4. Visualization examples

Usage:
    python scripts/demo_analysis.py --mode demo
    python scripts/demo_analysis.py --mode full
"""

import os
import sys
import asyncio
import argparse
import logging
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_sql_demo_queries(postgres_url: str):
    """Run demonstration SQL queries to show analysis capabilities."""
    logger.info("📊 Running SQL analysis demonstrations...")
    
    engine = create_engine(postgres_url)
    
    # Demo queries from our comprehensive SQL collection
    demo_queries = {
        "politician_effectiveness": """
        SELECT 
            p.name,
            p.party,
            p.state,
            COUNT(DISTINCT b.id) AS bills_sponsored,
            COUNT(DISTINCT v.id) AS votes_cast,
            CASE 
                WHEN p.chamber = 'senate' THEN COUNT(DISTINCT b.id) * 1.5 + COUNT(DISTINCT v.id) * 0.1
                ELSE COUNT(DISTINCT b.id) * 1.0 + COUNT(DISTINCT v.id) * 0.1
            END AS effectiveness_score
        FROM politicians p
        LEFT JOIN bills b ON b.sponsor_id = p.id::text
        LEFT JOIN votes v ON v.politician_id = p.id::text
        WHERE p.current_office = true
        GROUP BY p.id, p.name, p.party, p.state, p.chamber
        ORDER BY effectiveness_score DESC
        LIMIT 10;
        """,
        
        "data_source_stats": """
        SELECT 
            ds.category,
            COUNT(*) AS source_count,
            COUNT(CASE WHEN ds.status = 'active' THEN 1 END) AS active_sources,
            SUM(doc_counts.doc_count) AS total_documents
        FROM data_sources ds
        LEFT JOIN (
            SELECT source_id, COUNT(*) AS doc_count
            FROM documents
            GROUP BY source_id
        ) doc_counts ON doc_counts.source_id = ds.id
        GROUP BY ds.category
        ORDER BY total_documents DESC NULLS LAST;
        """,
        
        "recent_activity": """
        SELECT 
            'Documents' AS entity_type,
            COUNT(*) AS total_count,
            COUNT(CASE WHEN date_ingested >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) AS recent_count
        FROM documents
        UNION ALL
        SELECT 
            'Bills',
            COUNT(*),
            COUNT(CASE WHEN introduced_date >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END)
        FROM bills
        UNION ALL
        SELECT 
            'Votes',
            COUNT(*),
            COUNT(CASE WHEN vote_date >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END)
        FROM votes;
        """
    }
    
    results = {}
    
    for query_name, query_sql in demo_queries.items():
        try:
            logger.info(f"🔍 Running query: {query_name}")
            df = pd.read_sql(query_sql, engine)
            results[query_name] = df.to_dict('records')
            
            print(f"\n📋 {query_name.replace('_', ' ').title()}:")
            print(df.to_string(index=False))
            
        except Exception as e:
            logger.warning(f"⚠️ Query {query_name} failed (likely no data yet): {e}")
            results[query_name] = []
    
    # Save results
    output_dir = Path("reports/generated/demo")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "sql_demo_results.json", 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"✅ SQL demo results saved to {output_dir}")
    return results

async def run_ingestion_demo():
    """Run a small-scale ingestion demonstration."""
    logger.info("🔄 Running ingestion demonstration...")
    
    try:
        # Import our enhanced ingestion system
        sys.path.append(str(Path(__file__).parent))
        from enhanced_government_ingestion import EnhancedGovernmentIngestion, IngestionConfig
        
        # Create lightweight config for demo
        config = IngestionConfig(
            batch_size=50,
            max_concurrent_requests=3,
            rate_limit_per_second=2,
            enable_selenium=False,
            enable_vector_embeddings=False,  # Disable for demo
            deduplicate_content=True
        )
        
        # Initialize ingestion system
        ingestion = EnhancedGovernmentIngestion(config)
        await ingestion.initialize()
        
        # Run limited Congress data ingestion
        logger.info("📥 Ingesting sample Congressional data...")
        await ingestion.ingest_congress_data(limit=100)
        
        # Generate basic reports
        logger.info("📊 Generating sample reports...")
        await ingestion.generate_comprehensive_reports()
        
        await ingestion.cleanup()
        
        logger.info("✅ Ingestion demo completed")
        
    except ImportError as e:
        logger.error(f"❌ Could not import ingestion modules: {e}")
        logger.info("💡 Try installing dependencies: pip install aiohttp sentence-transformers")
    except Exception as e:
        logger.error(f"❌ Ingestion demo failed: {e}")

def generate_sample_reports():
    """Generate sample reports using the reporting system."""
    logger.info("📈 Generating sample reports...")
    
    try:
        sys.path.append(str(Path(__file__).parent))
        from generate_reports import GovernmentDataReporter
        
        postgres_url = os.getenv('POSTGRES_URL', 'postgresql://postgres:postgres@localhost:5432/postgres')
        
        # Initialize reporter
        reporter = GovernmentDataReporter(postgres_url)
        
        # Generate executive summary (works even with limited data)
        logger.info("📋 Generating executive summary...")
        summary = reporter.generate_executive_summary()
        
        logger.info("✅ Sample reports generated")
        return summary
        
    except Exception as e:
        logger.error(f"❌ Report generation failed: {e}")
        return None

def create_demo_dashboard():
    """Create a simple demo dashboard showing capabilities."""
    logger.info("🎨 Creating demo dashboard...")
    
    dashboard_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Government Data Analysis Demo</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }
        .card { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .metric { text-align: center; padding: 20px; border-left: 4px solid #667eea; }
        .metric h3 { margin: 0; color: #667eea; font-size: 2em; }
        .metric p { margin: 5px 0 0 0; color: #666; }
        .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-top: 20px; }
        .feature { background: #f8f9ff; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; }
        .code-block { background: #2d3748; color: #e2e8f0; padding: 20px; border-radius: 8px; font-family: 'Monaco', 'Menlo', monospace; font-size: 14px; overflow-x: auto; }
        .success { color: #48bb78; }
        .warning { color: #ed8936; }
        .info { color: #4299e1; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏛️ Government Data Analysis Platform</h1>
            <p>Comprehensive analysis of federal, state, and local government data from 300+ sources</p>
        </div>

        <div class="grid">
            <div class="card">
                <h2>📊 System Capabilities</h2>
                <div class="features">
                    <div class="feature">
                        <h3>🔄 Data Ingestion</h3>
                        <p>300+ government sources including Congress, FEC, state legislatures, and international bodies</p>
                    </div>
                    <div class="feature">
                        <h3>🧠 AI Analysis</h3>
                        <p>Vector embeddings, semantic search, and automated politician effectiveness scoring</p>
                    </div>
                    <div class="feature">
                        <h3>📈 Comprehensive Reports</h3>
                        <p>Executive summaries, legislative trends, voting patterns, and geographic analysis</p>
                    </div>
                    <div class="feature">
                        <h3>🎯 Real-time Tracking</h3>
                        <p>Live monitoring of bills, votes, and political activities across all levels of government</p>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>⚡ Quick Start Commands</h2>
                <div class="code-block">
# Basic Congressional data ingestion<br>
<span class="success">make ingest</span><br><br>

# Enhanced multi-source ingestion<br>
<span class="success">make ingest-all</span><br><br>

# Generate comprehensive reports<br>
<span class="success">make reports</span><br><br>

# Quick analysis workflow<br>
<span class="success">make quick-analysis</span><br><br>

# Full analysis (all sources + reports)<br>
<span class="success">make full-analysis</span>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>🎯 Available Analysis Types</h2>
            <div class="grid">
                <div class="metric">
                    <h3>👥</h3>
                    <p>Politician Effectiveness<br><small>Rankings, KPIs, bipartisan scores</small></p>
                </div>
                <div class="metric">
                    <h3>📋</h3>
                    <p>Legislative Trends<br><small>Bill patterns, success rates, topics</small></p>
                </div>
                <div class="metric">
                    <h3>🗳️</h3>
                    <p>Voting Patterns<br><small>Party unity, attendance, controversies</small></p>
                </div>
                <div class="metric">
                    <h3>🗺️</h3>
                    <p>Geographic Analysis<br><small>State delegations, regional priorities</small></p>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>📚 Available Reports</h2>
            <p>The system generates multiple report formats:</p>
            <ul>
                <li><strong>Executive Summary</strong> - High-level overview and key metrics</li>
                <li><strong>Politician Effectiveness</strong> - Comprehensive scoring and rankings</li>
                <li><strong>Legislative Trends</strong> - Bill introduction patterns and success rates</li>
                <li><strong>Voting Patterns</strong> - Party unity and bipartisan cooperation analysis</li>
                <li><strong>Data Sources</strong> - Source performance and quality metrics</li>
                <li><strong>Geographic Analysis</strong> - State and regional political patterns</li>
            </ul>
            <p>All reports available in JSON, CSV, and Markdown formats.</p>
        </div>

        <div class="card">
            <h2>🔗 Key Resources</h2>
            <div class="features">
                <div class="feature">
                    <h4>📖 Documentation</h4>
                    <p><a href="docs/INGESTION_GUIDE.md">Comprehensive Ingestion Guide</a></p>
                    <p><a href="docs/comprehensive_analysis_queries.sql">100+ SQL Analysis Queries</a></p>
                </div>
                <div class="feature">
                    <h4>📊 Data Sources</h4>
                    <p><a href="data/government-sources.yaml">300+ Government Sources</a></p>
                    <p>Federal, State, Local, and International</p>
                </div>
                <div class="feature">
                    <h4>🛠️ Scripts</h4>
                    <p>Enhanced ingestion engine</p>
                    <p>Automated report generation</p>
                    <p>SQL analysis toolkit</p>
                </div>
                <div class="feature">
                    <h4>📈 Monitoring</h4>
                    <p>Real-time health checks</p>
                    <p>Performance metrics</p>
                    <p>Data quality assessments</p>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>🚀 Next Steps</h2>
            <ol>
                <li><strong>Setup:</strong> Run <code>make setup</code> to configure the system</li>
                <li><strong>Start Services:</strong> Run <code>make start</code> to launch the platform</li>
                <li><strong>Ingest Data:</strong> Use <code>make ingest-enhanced</code> for sample data</li>
                <li><strong>Generate Reports:</strong> Run <code>make reports</code> for comprehensive analysis</li>
                <li><strong>Explore Results:</strong> Check <code>reports/generated/</code> for outputs</li>
            </ol>
        </div>
    </div>

    <script>
        // Simple interactivity
        document.addEventListener('DOMContentLoaded', function() {
            console.log('🏛️ Government Data Analysis Platform loaded');
            
            // Highlight code blocks on click
            document.querySelectorAll('.code-block').forEach(block => {
                block.addEventListener('click', function() {
                    this.style.background = '#4a5568';
                    setTimeout(() => {
                        this.style.background = '#2d3748';
                    }, 200);
                });
            });
        });
    </script>
</body>
</html>"""
    
    # Save dashboard
    output_dir = Path("reports/generated/demo")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    dashboard_path = output_dir / "demo_dashboard.html"
    with open(dashboard_path, 'w') as f:
        f.write(dashboard_content)
    
    logger.info(f"✅ Demo dashboard created: {dashboard_path}")
    return dashboard_path

async def run_demo():
    """Run complete demonstration workflow."""
    logger.info("🎬 Starting Government Data Analysis Demo")
    
    print("""
🏛️  Government Data Analysis Platform Demo
=========================================

This demo showcases the comprehensive government data analysis capabilities
including data ingestion, SQL analysis, and automated report generation.
    """)
    
    # Check database connection
    postgres_url = os.getenv('POSTGRES_URL', 'postgresql://postgres:postgres@localhost:5432/postgres')
    logger.info(f"🔗 Connecting to database: {postgres_url.split('@')[1] if '@' in postgres_url else 'localhost'}")
    
    try:
        # 1. Run SQL demonstration queries
        logger.info("1️⃣ Running SQL analysis demonstrations...")
        sql_results = run_sql_demo_queries(postgres_url)
        
        # 2. Generate sample reports (even with limited data)
        logger.info("2️⃣ Generating sample reports...")
        report_summary = generate_sample_reports()
        
        # 3. Create demo dashboard
        logger.info("3️⃣ Creating interactive demo dashboard...")
        dashboard_path = create_demo_dashboard()
        
        # 4. Optionally run small ingestion demo
        run_ingestion = input("\n🤔 Would you like to run a small data ingestion demo? (y/n): ").lower() == 'y'
        if run_ingestion:
            logger.info("4️⃣ Running data ingestion demo...")
            await run_ingestion_demo()
        else:
            logger.info("4️⃣ Skipping ingestion demo")
        
        print(f"""
✅ Demo completed successfully!

📊 Results available:
   • Demo dashboard: file://{dashboard_path.absolute()}
   • SQL results: reports/generated/demo/sql_demo_results.json
   • Sample reports: reports/generated/comprehensive_report_*/

🚀 Next steps:
   • Run 'make ingest-enhanced' for real data ingestion
   • Run 'make reports' for comprehensive analysis
   • Explore docs/INGESTION_GUIDE.md for detailed documentation
   
🔗 Access the platform:
   • Frontend: http://localhost:3000
   • Management: http://localhost:3006  
   • Monitoring: http://localhost:3003
        """)
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        print(f"\n❌ Demo encountered an error: {e}")
        print("\n💡 Troubleshooting tips:")
        print("   • Ensure PostgreSQL is running: make health")
        print("   • Check database connection: echo $POSTGRES_URL")
        print("   • Install dependencies: pip install -r requirements.txt")

async def run_full_analysis():
    """Run full analysis workflow with real data."""
    logger.info("🚀 Starting full government data analysis workflow")
    
    print("""
🏛️  Full Government Data Analysis Workflow
==========================================

This will perform comprehensive data ingestion and analysis across
300+ government sources. This may take 30-60 minutes depending on
your system and network connection.
    """)
    
    proceed = input("🤔 Do you want to proceed with full analysis? (y/n): ").lower() == 'y'
    if not proceed:
        logger.info("❌ Full analysis cancelled by user")
        return
    
    try:
        # Import systems
        sys.path.append(str(Path(__file__).parent))
        from enhanced_government_ingestion import EnhancedGovernmentIngestion, IngestionConfig
        from generate_reports import GovernmentDataReporter
        
        # Full configuration
        config = IngestionConfig(
            batch_size=1000,
            max_concurrent_requests=10,
            rate_limit_per_second=5,
            enable_selenium=False,
            enable_vector_embeddings=True,
            deduplicate_content=True,
            validate_data=True
        )
        
        # Initialize systems
        logger.info("🔧 Initializing ingestion system...")
        ingestion = EnhancedGovernmentIngestion(config)
        await ingestion.initialize()
        
        # Run comprehensive ingestion
        logger.info("📥 Starting comprehensive data ingestion...")
        await ingestion.ingest_congress_data(limit=5000)
        
        # Web scraping for selected sources
        scraping_sources = [name for name in ingestion.data_sources.keys() 
                          if 'api' not in name.lower()][:10]
        await ingestion.ingest_web_scraping_sources(scraping_sources)
        
        # Generate comprehensive reports
        logger.info("📊 Generating comprehensive reports...")
        report_dir = await ingestion.generate_comprehensive_reports()
        
        await ingestion.cleanup()
        
        # Generate additional specialized reports
        postgres_url = os.getenv('POSTGRES_URL', 'postgresql://postgres:postgres@localhost:5432/postgres')
        reporter = GovernmentDataReporter(postgres_url)
        specialized_report_dir = reporter.generate_all_reports()
        
        print(f"""
🎉 Full analysis completed successfully!

📊 Comprehensive results available:
   • Ingestion reports: {report_dir}
   • Analysis reports: {specialized_report_dir}
   • SQL queries: docs/comprehensive_analysis_queries.sql
   
📈 Analysis includes:
   • 300+ government data sources
   • Politician effectiveness rankings
   • Legislative trends and patterns  
   • Voting behavior analysis
   • Geographic and demographic insights
   • Data quality assessments
        """)
        
    except Exception as e:
        logger.error(f"❌ Full analysis failed: {e}")
        print(f"\n❌ Full analysis encountered an error: {e}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Government Data Analysis Demo")
    
    parser.add_argument(
        '--mode',
        choices=['demo', 'full'],
        default='demo',
        help='Demo mode: quick demonstration or full analysis'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'demo':
        asyncio.run(run_demo())
    elif args.mode == 'full':
        asyncio.run(run_full_analysis())

if __name__ == "__main__":
    main()