#!/usr/bin/env python3
"""
Government Data Analysis & Report Generator
==========================================

This script generates comprehensive reports and analysis from ingested government data.
It produces multiple report formats including executive summaries, detailed analytics,
and visualizations for political analysis and tracking.

Features:
- Executive summary reports
- Politician effectiveness analysis
- Legislative trends and patterns
- Voting behavior analysis
- Committee and party analysis
- Geographic and demographic insights
- Data quality assessments
- Performance metrics
- Multiple output formats (JSON, CSV, Markdown, HTML)

Usage:
    python scripts/generate_reports.py --report all
    python scripts/generate_reports.py --report politician-effectiveness --format html
    python scripts/generate_reports.py --report legislative-trends --period 2years
"""

import os
import sys
import json
import csv
import logging
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import matplotlib.pyplot as plt
import seaborn as sns
from jinja2 import Template

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GovernmentDataReporter:
    """Comprehensive government data analysis and reporting system."""
    
    def __init__(self, postgres_url: str):
        self.postgres_url = postgres_url
        self.engine = create_engine(postgres_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Create output directories
        self.output_dir = Path("reports/generated")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Report timestamp
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report_dir = self.output_dir / f"comprehensive_report_{self.timestamp}"
        self.report_dir.mkdir(exist_ok=True)
        
        logger.info(f"📊 Report generator initialized. Output: {self.report_dir}")
    
    def generate_executive_summary(self) -> Dict[str, Any]:
        """Generate executive summary of all government data."""
        logger.info("📋 Generating executive summary...")
        
        # Database statistics
        stats_query = """
        SELECT 
            'data_sources' as table_name, COUNT(*) as count FROM data_sources
        UNION ALL
        SELECT 'documents', COUNT(*) FROM documents
        UNION ALL  
        SELECT 'politicians', COUNT(*) FROM politicians
        UNION ALL
        SELECT 'bills', COUNT(*) FROM bills
        UNION ALL
        SELECT 'votes', COUNT(*) FROM votes
        UNION ALL
        SELECT 'ingestion_runs', COUNT(*) FROM ingestion_runs
        """
        
        stats_df = pd.read_sql(stats_query, self.engine)
        stats_dict = dict(zip(stats_df['table_name'], stats_df['count']))
        
        # Recent activity (last 30 days)
        recent_activity_query = """
        SELECT 
            COUNT(CASE WHEN date_ingested >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as recent_documents,
            COUNT(CASE WHEN introduced_date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as recent_bills,
            COUNT(CASE WHEN vote_date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as recent_votes
        FROM documents d
        FULL OUTER JOIN bills b ON true
        FULL OUTER JOIN votes v ON true
        """
        
        activity_df = pd.read_sql(recent_activity_query, self.engine)
        
        # Data quality metrics
        quality_query = """
        SELECT 
            'documents' as entity,
            COUNT(*) as total,
            COUNT(CASE WHEN content IS NOT NULL AND content != '' THEN 1 END) as complete,
            ROUND(COUNT(CASE WHEN content IS NOT NULL AND content != '' THEN 1 END) * 100.0 / COUNT(*), 2) as completeness_pct
        FROM documents
        WHERE content IS NOT NULL
        UNION ALL
        SELECT 
            'politicians',
            COUNT(*),
            COUNT(CASE WHEN name IS NOT NULL AND party IS NOT NULL THEN 1 END),
            ROUND(COUNT(CASE WHEN name IS NOT NULL AND party IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 2)
        FROM politicians
        """
        
        quality_df = pd.read_sql(quality_query, self.engine)
        
        summary = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'reporting_period': '30 days',
            'database_statistics': stats_dict,
            'recent_activity': {
                'documents_added': int(activity_df.iloc[0]['recent_documents']) if len(activity_df) > 0 else 0,
                'bills_introduced': int(activity_df.iloc[0]['recent_bills']) if len(activity_df) > 0 else 0,
                'votes_recorded': int(activity_df.iloc[0]['recent_votes']) if len(activity_df) > 0 else 0
            },
            'data_quality': {
                row['entity']: {
                    'total_records': int(row['total']),
                    'complete_records': int(row['complete']),
                    'completeness_percentage': float(row['completeness_pct'])
                }
                for _, row in quality_df.iterrows()
            },
            'key_insights': [
                f"Total of {stats_dict.get('politicians', 0):,} politicians tracked across all levels of government",
                f"Monitoring {stats_dict.get('bills', 0):,} pieces of legislation with full text and metadata",
                f"Complete voting records for {stats_dict.get('votes', 0):,} individual votes",
                f"Comprehensive document collection of {stats_dict.get('documents', 0):,} government publications"
            ]
        }
        
        self._save_report(summary, 'executive_summary')
        logger.info("✅ Executive summary generated")
        return summary
    
    def generate_politician_effectiveness_report(self, limit: int = 100) -> Dict[str, Any]:
        """Generate comprehensive politician effectiveness analysis."""
        logger.info("👥 Generating politician effectiveness report...")
        
        # Effectiveness scoring query
        effectiveness_query = """
        WITH politician_metrics AS (
            SELECT 
                p.id,
                p.name,
                p.party,
                p.state,
                p.chamber,
                p.current_office,
                COALESCE(bills.sponsored_count, 0) as bills_sponsored,
                COALESCE(bills.enacted_count, 0) as bills_enacted,
                COALESCE(votes.total_votes, 0) as votes_cast,
                COALESCE(votes.yes_votes, 0) as yes_votes,
                COALESCE(votes.no_votes, 0) as no_votes,
                COALESCE(votes.present_votes, 0) as present_votes,
                COALESCE(committees.committee_count, 0) as committee_memberships
            FROM politicians p
            LEFT JOIN (
                SELECT 
                    sponsor_id,
                    COUNT(*) as sponsored_count,
                    COUNT(CASE WHEN status ILIKE '%enacted%' OR status ILIKE '%law%' THEN 1 END) as enacted_count
                FROM bills 
                WHERE introduced_date >= CURRENT_DATE - INTERVAL '2 years'
                GROUP BY sponsor_id
            ) bills ON bills.sponsor_id = p.id::text
            LEFT JOIN (
                SELECT 
                    politician_id,
                    COUNT(*) as total_votes,
                    COUNT(CASE WHEN position = 'yes' THEN 1 END) as yes_votes,
                    COUNT(CASE WHEN position = 'no' THEN 1 END) as no_votes,
                    COUNT(CASE WHEN position = 'present' THEN 1 END) as present_votes
                FROM votes 
                WHERE vote_date >= CURRENT_DATE - INTERVAL '1 year'
                GROUP BY politician_id
            ) votes ON votes.politician_id = p.id::text
            LEFT JOIN (
                SELECT 
                    id,
                    COALESCE(jsonb_array_length(committee_memberships), 0) as committee_count
                FROM politicians
                WHERE committee_memberships IS NOT NULL
            ) committees ON committees.id = p.id
            WHERE p.current_office = true
        ),
        effectiveness_scores AS (
            SELECT 
                *,
                -- Effectiveness calculation
                CASE 
                    WHEN chamber = 'senate' THEN 
                        (bills_sponsored * 2.0) + (bills_enacted * 10.0) + (votes_cast * 0.1) + (committee_memberships * 1.0)
                    ELSE 
                        (bills_sponsored * 1.0) + (bills_enacted * 8.0) + (votes_cast * 0.05) + (committee_memberships * 0.8)
                END as effectiveness_score,
                -- Attendance rate
                CASE 
                    WHEN votes_cast > 0 THEN ROUND((yes_votes + no_votes) * 100.0 / votes_cast, 2)
                    ELSE 0
                END as attendance_rate,
                -- Legislative success rate  
                CASE 
                    WHEN bills_sponsored > 0 THEN ROUND(bills_enacted * 100.0 / bills_sponsored, 2)
                    ELSE 0
                END as success_rate
            FROM politician_metrics
        )
        SELECT * FROM effectiveness_scores
        ORDER BY effectiveness_score DESC
        LIMIT %s
        """
        
        effectiveness_df = pd.read_sql(effectiveness_query, self.engine, params=[limit])
        
        # Party analysis
        party_analysis_query = """
        SELECT 
            party,
            chamber,
            COUNT(*) as members,
            AVG(CASE 
                WHEN chamber = 'senate' THEN bills_sponsored * 2.0 + bills_enacted * 10.0
                ELSE bills_sponsored * 1.0 + bills_enacted * 8.0
            END) as avg_legislative_score,
            AVG(CASE WHEN votes_cast > 0 THEN (yes_votes + no_votes) * 100.0 / votes_cast ELSE 0 END) as avg_attendance
        FROM (
            SELECT 
                p.party,
                p.chamber,
                COALESCE(b.sponsored_count, 0) as bills_sponsored,
                COALESCE(b.enacted_count, 0) as bills_enacted,
                COALESCE(v.total_votes, 0) as votes_cast,
                COALESCE(v.yes_votes, 0) as yes_votes,
                COALESCE(v.no_votes, 0) as no_votes
            FROM politicians p
            LEFT JOIN (
                SELECT sponsor_id, COUNT(*) as sponsored_count,
                       COUNT(CASE WHEN status ILIKE '%enacted%' THEN 1 END) as enacted_count
                FROM bills WHERE introduced_date >= CURRENT_DATE - INTERVAL '2 years'
                GROUP BY sponsor_id
            ) b ON b.sponsor_id = p.id::text
            LEFT JOIN (
                SELECT politician_id, COUNT(*) as total_votes,
                       COUNT(CASE WHEN position = 'yes' THEN 1 END) as yes_votes,
                       COUNT(CASE WHEN position = 'no' THEN 1 END) as no_votes
                FROM votes WHERE vote_date >= CURRENT_DATE - INTERVAL '1 year'
                GROUP BY politician_id
            ) v ON v.politician_id = p.id::text
            WHERE p.current_office = true
        ) party_stats
        GROUP BY party, chamber
        ORDER BY avg_legislative_score DESC
        """
        
        party_df = pd.read_sql(party_analysis_query, self.engine)
        
        # State delegation analysis
        state_analysis_query = """
        SELECT 
            state,
            COUNT(*) as delegation_size,
            COUNT(CASE WHEN party = 'Democratic' THEN 1 END) as democratic_members,
            COUNT(CASE WHEN party = 'Republican' THEN 1 END) as republican_members,
            AVG(effectiveness_score) as avg_effectiveness
        FROM (
            SELECT 
                p.state,
                p.party,
                CASE 
                    WHEN p.chamber = 'senate' THEN 
                        COALESCE(b.sponsored_count, 0) * 2.0 + COALESCE(b.enacted_count, 0) * 10.0
                    ELSE 
                        COALESCE(b.sponsored_count, 0) * 1.0 + COALESCE(b.enacted_count, 0) * 8.0
                END as effectiveness_score
            FROM politicians p
            LEFT JOIN (
                SELECT sponsor_id, COUNT(*) as sponsored_count,
                       COUNT(CASE WHEN status ILIKE '%enacted%' THEN 1 END) as enacted_count
                FROM bills WHERE introduced_date >= CURRENT_DATE - INTERVAL '2 years'
                GROUP BY sponsor_id
            ) b ON b.sponsor_id = p.id::text
            WHERE p.current_office = true AND p.state IS NOT NULL
        ) state_stats
        GROUP BY state
        ORDER BY avg_effectiveness DESC
        LIMIT 25
        """
        
        state_df = pd.read_sql(state_analysis_query, self.engine)
        
        report = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'analysis_period': '2 years (bills), 1 year (votes)',
            'methodology': {
                'effectiveness_formula': 'Bills*weight + Enacted*10 + Votes*0.1 + Committees*1.0',
                'chamber_weights': {'senate': 2.0, 'house': 1.0},
                'minimum_thresholds': {'bills': 1, 'votes': 10}
            },
            'top_performers': effectiveness_df.head(50).to_dict('records'),
            'party_analysis': party_df.to_dict('records'),
            'state_rankings': state_df.to_dict('records'),
            'summary_statistics': {
                'total_active_politicians': len(effectiveness_df),
                'avg_effectiveness_score': float(effectiveness_df['effectiveness_score'].mean()),
                'median_bills_sponsored': float(effectiveness_df['bills_sponsored'].median()),
                'avg_attendance_rate': float(effectiveness_df['attendance_rate'].mean()),
                'most_effective_party': party_df.iloc[0]['party'] if len(party_df) > 0 else None,
                'most_effective_state': state_df.iloc[0]['state'] if len(state_df) > 0 else None
            }
        }
        
        self._save_report(report, 'politician_effectiveness')
        logger.info("✅ Politician effectiveness report generated")
        return report
    
    def generate_legislative_trends_report(self) -> Dict[str, Any]:
        """Generate comprehensive legislative trends analysis."""
        logger.info("📈 Generating legislative trends report...")
        
        # Monthly trends
        monthly_trends_query = """
        SELECT 
            DATE_TRUNC('month', introduced_date) as month,
            COUNT(*) as bills_introduced,
            COUNT(CASE WHEN bill_type = 'hr' THEN 1 END) as house_bills,
            COUNT(CASE WHEN bill_type = 's' THEN 1 END) as senate_bills,
            COUNT(CASE WHEN status ILIKE '%passed%' OR status ILIKE '%enacted%' THEN 1 END) as bills_passed,
            COUNT(DISTINCT sponsor_id) as unique_sponsors
        FROM bills
        WHERE introduced_date >= CURRENT_DATE - INTERVAL '2 years'
        GROUP BY DATE_TRUNC('month', introduced_date)
        ORDER BY month DESC
        """
        
        monthly_df = pd.read_sql(monthly_trends_query, self.engine)
        
        # Subject analysis
        subject_trends_query = """
        SELECT 
            unnest(subjects) as subject,
            COUNT(*) as bill_count,
            COUNT(CASE WHEN status ILIKE '%passed%' OR status ILIKE '%enacted%' THEN 1 END) as passed_count,
            ROUND(COUNT(CASE WHEN status ILIKE '%passed%' OR status ILIKE '%enacted%' THEN 1 END) * 100.0 / COUNT(*), 2) as success_rate,
            COUNT(DISTINCT sponsor_id) as sponsor_diversity
        FROM bills
        WHERE subjects IS NOT NULL 
        AND introduced_date >= CURRENT_DATE - INTERVAL '2 years'
        GROUP BY subject
        HAVING COUNT(*) >= 10
        ORDER BY bill_count DESC
        LIMIT 30
        """
        
        subject_df = pd.read_sql(subject_trends_query, self.engine)
        
        # Bill type analysis
        bill_type_query = """
        SELECT 
            bill_type,
            congress_number,
            COUNT(*) as count,
            COUNT(CASE WHEN status ILIKE '%passed%' OR status ILIKE '%enacted%' THEN 1 END) as passed,
            ROUND(COUNT(CASE WHEN status ILIKE '%passed%' OR status ILIKE '%enacted%' THEN 1 END) * 100.0 / COUNT(*), 2) as success_rate
        FROM bills
        WHERE congress_number IS NOT NULL
        AND introduced_date >= CURRENT_DATE - INTERVAL '4 years'
        GROUP BY bill_type, congress_number
        ORDER BY congress_number DESC, count DESC
        """
        
        bill_type_df = pd.read_sql(bill_type_query, self.engine)
        
        # Seasonal patterns
        seasonal_query = """
        SELECT 
            EXTRACT(MONTH FROM introduced_date) as month,
            TO_CHAR(introduced_date, 'Month') as month_name,
            COUNT(*) as bills_introduced,
            AVG(COUNT(*)) OVER () as avg_monthly
        FROM bills
        WHERE introduced_date >= CURRENT_DATE - INTERVAL '5 years'
        GROUP BY EXTRACT(MONTH FROM introduced_date), TO_CHAR(introduced_date, 'Month')
        ORDER BY month
        """
        
        seasonal_df = pd.read_sql(seasonal_query, self.engine)
        
        report = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'analysis_period': '2 years (primary), 4 years (historical)',
            'monthly_trends': monthly_df.to_dict('records'),
            'top_subjects': subject_df.to_dict('records'),
            'bill_type_analysis': bill_type_df.to_dict('records'),
            'seasonal_patterns': seasonal_df.to_dict('records'),
            'summary_insights': {
                'total_bills_analyzed': int(monthly_df['bills_introduced'].sum()),
                'avg_monthly_bills': float(monthly_df['bills_introduced'].mean()),
                'peak_month': monthly_df.loc[monthly_df['bills_introduced'].idxmax(), 'month'].strftime('%Y-%m') if len(monthly_df) > 0 else None,
                'most_active_subject': subject_df.iloc[0]['subject'] if len(subject_df) > 0 else None,
                'highest_success_subject': subject_df.loc[subject_df['success_rate'].idxmax(), 'subject'] if len(subject_df) > 0 else None,
                'overall_passage_rate': float(monthly_df['bills_passed'].sum() / monthly_df['bills_introduced'].sum() * 100) if monthly_df['bills_introduced'].sum() > 0 else 0
            }
        }
        
        self._save_report(report, 'legislative_trends')
        logger.info("✅ Legislative trends report generated")
        return report
    
    def generate_voting_patterns_report(self) -> Dict[str, Any]:
        """Generate comprehensive voting patterns analysis."""
        logger.info("🗳️ Generating voting patterns report...")
        
        # Party unity analysis
        party_unity_query = """
        WITH vote_positions AS (
            SELECT 
                v.vote_id,
                v.politician_id,
                v.position,
                p.party,
                p.chamber,
                v.vote_date
            FROM votes v
            JOIN politicians p ON p.id::text = v.politician_id
            WHERE v.vote_date >= CURRENT_DATE - INTERVAL '1 year'
            AND v.position IN ('yes', 'no')
            AND p.party IN ('Democratic', 'Republican')
        ),
        party_majority_positions AS (
            SELECT 
                vote_id,
                party,
                MODE() WITHIN GROUP (ORDER BY position) as majority_position,
                COUNT(*) as party_vote_count
            FROM vote_positions
            GROUP BY vote_id, party
        )
        SELECT 
            vp.party,
            vp.chamber,
            COUNT(*) as total_votes,
            COUNT(CASE WHEN vp.position = pmp.majority_position THEN 1 END) as party_line_votes,
            ROUND(COUNT(CASE WHEN vp.position = pmp.majority_position THEN 1 END) * 100.0 / COUNT(*), 2) as unity_score
        FROM vote_positions vp
        JOIN party_majority_positions pmp ON pmp.vote_id = vp.vote_id AND pmp.party = vp.party
        GROUP BY vp.party, vp.chamber
        ORDER BY unity_score DESC
        """
        
        party_unity_df = pd.read_sql(party_unity_query, self.engine)
        
        # Bipartisan cooperation
        bipartisan_query = """
        WITH cross_party_votes AS (
            SELECT 
                v.politician_id,
                p.name,
                p.party,
                p.state,
                COUNT(*) as total_votes,
                COUNT(CASE 
                    WHEN (p.party = 'Democratic' AND majority.majority_party = 'Republican') OR
                         (p.party = 'Republican' AND majority.majority_party = 'Democratic')
                    THEN 1 
                END) as cross_party_votes
            FROM votes v
            JOIN politicians p ON p.id::text = v.politician_id
            JOIN (
                SELECT 
                    vote_id,
                    CASE 
                        WHEN COUNT(CASE WHEN party = 'Republican' AND position = 'yes' THEN 1 END) >
                             COUNT(CASE WHEN party = 'Democratic' AND position = 'yes' THEN 1 END)
                        THEN 'Republican'
                        ELSE 'Democratic'
                    END as majority_party
                FROM votes v2
                JOIN politicians p2 ON p2.id::text = v2.politician_id
                WHERE v2.position IN ('yes', 'no') AND p2.party IN ('Democratic', 'Republican')
                GROUP BY vote_id
            ) majority ON majority.vote_id = v.vote_id
            WHERE v.vote_date >= CURRENT_DATE - INTERVAL '1 year'
            AND v.position IN ('yes', 'no')
            AND p.party IN ('Democratic', 'Republican')
            GROUP BY v.politician_id, p.name, p.party, p.state
            HAVING COUNT(*) >= 50
        )
        SELECT 
            name,
            party,
            state,
            total_votes,
            cross_party_votes,
            ROUND(cross_party_votes * 100.0 / total_votes, 2) as bipartisan_score
        FROM cross_party_votes
        ORDER BY bipartisan_score DESC
        LIMIT 25
        """
        
        bipartisan_df = pd.read_sql(bipartisan_query, self.engine)
        
        # Controversial votes (close margins)
        controversial_query = """
        SELECT 
            vote_id,
            description,
            vote_date,
            chamber,
            COUNT(CASE WHEN position = 'yes' THEN 1 END) as yes_votes,
            COUNT(CASE WHEN position = 'no' THEN 1 END) as no_votes,
            ABS(COUNT(CASE WHEN position = 'yes' THEN 1 END) - 
                COUNT(CASE WHEN position = 'no' THEN 1 END)) as margin,
            result
        FROM votes
        WHERE vote_date >= CURRENT_DATE - INTERVAL '1 year'
        AND position IN ('yes', 'no')
        GROUP BY vote_id, description, vote_date, chamber, result
        HAVING COUNT(CASE WHEN position = 'yes' THEN 1 END) > 0 
           AND COUNT(CASE WHEN position = 'no' THEN 1 END) > 0
        ORDER BY margin ASC
        LIMIT 20
        """
        
        controversial_df = pd.read_sql(controversial_query, self.engine)
        
        # Attendance analysis
        attendance_query = """
        SELECT 
            p.name,
            p.party,
            p.state,
            p.chamber,
            COUNT(v.id) as total_recorded_votes,
            COUNT(CASE WHEN v.position IN ('yes', 'no') THEN 1 END) as substantive_votes,
            COUNT(CASE WHEN v.position = 'not_voting' THEN 1 END) as missed_votes,
            ROUND(COUNT(CASE WHEN v.position IN ('yes', 'no') THEN 1 END) * 100.0 / COUNT(v.id), 2) as attendance_rate
        FROM politicians p
        JOIN votes v ON v.politician_id = p.id::text
        WHERE v.vote_date >= CURRENT_DATE - INTERVAL '6 months'
        AND p.current_office = true
        GROUP BY p.id, p.name, p.party, p.state, p.chamber
        HAVING COUNT(v.id) >= 20
        ORDER BY attendance_rate ASC
        LIMIT 25
        """
        
        attendance_df = pd.read_sql(attendance_query, self.engine)
        
        report = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'analysis_period': '1 year (voting patterns), 6 months (attendance)',
            'party_unity_scores': party_unity_df.to_dict('records'),
            'bipartisan_leaders': bipartisan_df.to_dict('records'),
            'controversial_votes': controversial_df.to_dict('records'),
            'attendance_analysis': attendance_df.to_dict('records'),
            'summary_metrics': {
                'avg_party_unity': float(party_unity_df['unity_score'].mean()) if len(party_unity_df) > 0 else 0,
                'most_unified_party': party_unity_df.loc[party_unity_df['unity_score'].idxmax(), 'party'] if len(party_unity_df) > 0 else None,
                'most_bipartisan_member': bipartisan_df.iloc[0]['name'] if len(bipartisan_df) > 0 else None,
                'closest_vote_margin': int(controversial_df['margin'].min()) if len(controversial_df) > 0 else None,
                'avg_attendance_rate': float(attendance_df['attendance_rate'].mean()) if len(attendance_df) > 0 else 0,
                'lowest_attendance': attendance_df.iloc[-1]['name'] if len(attendance_df) > 0 else None
            }
        }
        
        self._save_report(report, 'voting_patterns')
        logger.info("✅ Voting patterns report generated")
        return report
    
    def generate_data_sources_report(self) -> Dict[str, Any]:
        """Generate data sources performance and quality report."""
        logger.info("📊 Generating data sources report...")
        
        # Source performance
        source_performance_query = """
        SELECT 
            ds.name,
            ds.category,
            ds.source_type,
            ds.status,
            COUNT(d.id) as documents_collected,
            ds.last_successful_sync,
            EXTRACT(DAYS FROM NOW() - ds.last_successful_sync) as days_since_sync,
            ds.rate_limit_per_hour,
            ds.api_key_required,
            CASE 
                WHEN ds.last_successful_sync >= CURRENT_DATE - INTERVAL '7 days' THEN 'Active'
                WHEN ds.last_successful_sync >= CURRENT_DATE - INTERVAL '30 days' THEN 'Stale'
                ELSE 'Inactive'
            END as freshness_status
        FROM data_sources ds
        LEFT JOIN documents d ON d.source_id = ds.id
        GROUP BY ds.id, ds.name, ds.category, ds.source_type, ds.status, 
                 ds.last_successful_sync, ds.rate_limit_per_hour, ds.api_key_required
        ORDER BY documents_collected DESC
        """
        
        source_df = pd.read_sql(source_performance_query, self.engine)
        
        # Document type analysis
        document_analysis_query = """
        SELECT 
            document_type,
            COUNT(*) as total_documents,
            COUNT(CASE WHEN processed = true THEN 1 END) as processed_documents,
            COUNT(CASE WHEN embedding_id IS NOT NULL THEN 1 END) as vectorized_documents,
            AVG(LENGTH(content)) as avg_content_length,
            MIN(date_ingested) as first_ingested,
            MAX(date_ingested) as last_ingested
        FROM documents
        WHERE content IS NOT NULL
        GROUP BY document_type
        ORDER BY total_documents DESC
        """
        
        document_df = pd.read_sql(document_analysis_query, self.engine)
        
        # Ingestion performance
        ingestion_performance_query = """
        SELECT 
            DATE(start_time) as run_date,
            run_type,
            COUNT(*) as total_runs,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_runs,
            COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_runs,
            AVG(records_processed) as avg_records_processed,
            AVG(EXTRACT(EPOCH FROM (end_time - start_time))/60) as avg_duration_minutes
        FROM ingestion_runs
        WHERE start_time >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY DATE(start_time), run_type
        ORDER BY run_date DESC
        """
        
        ingestion_df = pd.read_sql(ingestion_performance_query, self.engine)
        
        # Source category breakdown
        category_breakdown = source_df.groupby('category').agg({
            'name': 'count',
            'documents_collected': 'sum'
        }).rename(columns={'name': 'source_count'}).reset_index()
        
        report = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'analysis_period': '30 days',
            'source_performance': source_df.to_dict('records'),
            'document_analysis': document_df.to_dict('records'),
            'ingestion_performance': ingestion_df.to_dict('records'),
            'category_breakdown': category_breakdown.to_dict('records'),
            'summary_statistics': {
                'total_sources': len(source_df),
                'active_sources': len(source_df[source_df['freshness_status'] == 'Active']),
                'total_documents': int(source_df['documents_collected'].sum()),
                'most_productive_source': source_df.iloc[0]['name'] if len(source_df) > 0 else None,
                'most_productive_category': category_breakdown.loc[category_breakdown['documents_collected'].idxmax(), 'category'] if len(category_breakdown) > 0 else None,
                'avg_ingestion_success_rate': float(ingestion_df['successful_runs'].sum() / ingestion_df['total_runs'].sum() * 100) if ingestion_df['total_runs'].sum() > 0 else 0,
                'data_freshness_rate': float(len(source_df[source_df['freshness_status'] == 'Active']) / len(source_df) * 100) if len(source_df) > 0 else 0
            }
        }
        
        self._save_report(report, 'data_sources')
        logger.info("✅ Data sources report generated")
        return report
    
    def generate_geographic_analysis_report(self) -> Dict[str, Any]:
        """Generate geographic and demographic analysis report."""
        logger.info("🗺️ Generating geographic analysis report...")
        
        # State delegation analysis
        state_analysis_query = """
        SELECT 
            state,
            COUNT(*) as total_delegation,
            COUNT(CASE WHEN party = 'Democratic' THEN 1 END) as democratic_members,
            COUNT(CASE WHEN party = 'Republican' THEN 1 END) as republican_members,
            COUNT(CASE WHEN party = 'Independent' THEN 1 END) as independent_members,
            COUNT(CASE WHEN chamber = 'house' THEN 1 END) as house_members,
            COUNT(CASE WHEN chamber = 'senate' THEN 1 END) as senate_members,
            ROUND(AVG(COALESCE(bills.bill_count, 0)), 2) as avg_bills_per_member,
            ROUND(AVG(COALESCE(votes.vote_count, 0)), 2) as avg_votes_per_member
        FROM politicians p
        LEFT JOIN (
            SELECT sponsor_id, COUNT(*) as bill_count
            FROM bills WHERE introduced_date >= CURRENT_DATE - INTERVAL '2 years'
            GROUP BY sponsor_id
        ) bills ON bills.sponsor_id = p.id::text
        LEFT JOIN (
            SELECT politician_id, COUNT(*) as vote_count
            FROM votes WHERE vote_date >= CURRENT_DATE - INTERVAL '1 year'
            GROUP BY politician_id
        ) votes ON votes.politician_id = p.id::text
        WHERE p.current_office = true AND p.state IS NOT NULL
        GROUP BY state
        ORDER BY total_delegation DESC
        """
        
        state_df = pd.read_sql(state_analysis_query, self.engine)
        
        # Regional bill topics
        regional_topics_query = """
        SELECT 
            p.state,
            unnest(b.subjects) as subject,
            COUNT(*) as bill_count
        FROM bills b
        JOIN politicians p ON p.id::text = b.sponsor_id
        WHERE b.introduced_date >= CURRENT_DATE - INTERVAL '2 years'
        AND b.subjects IS NOT NULL
        AND p.state IS NOT NULL
        GROUP BY p.state, subject
        HAVING COUNT(*) >= 3
        ORDER BY p.state, bill_count DESC
        """
        
        regional_df = pd.read_sql(regional_topics_query, self.engine)
        
        # Cross-state collaboration
        collaboration_query = """
        WITH state_collaborations AS (
            SELECT 
                sponsor_state.state as sponsor_state,
                cosponsor_state.state as cosponsor_state,
                COUNT(*) as collaboration_count
            FROM bills b
            JOIN politicians sponsor_state ON sponsor_state.id::text = b.sponsor_id
            JOIN (
                SELECT 
                    bills.id as bill_id,
                    politicians.state
                FROM bills
                JOIN LATERAL (
                    SELECT unnest(
                        CASE 
                            WHEN jsonb_typeof(cosponsors) = 'array' 
                            THEN ARRAY(SELECT jsonb_array_elements_text(cosponsors))
                            ELSE ARRAY[]::text[]
                        END
                    ) as cosponsor_id
                ) cosponsors_expanded ON true
                JOIN politicians ON politicians.bioguide_id = cosponsors_expanded.cosponsor_id
            ) cosponsor_state ON cosponsor_state.bill_id = b.id
            WHERE b.introduced_date >= CURRENT_DATE - INTERVAL '2 years'
            AND sponsor_state.state != cosponsor_state.state
            AND sponsor_state.state IS NOT NULL
            AND cosponsor_state.state IS NOT NULL
            GROUP BY sponsor_state.state, cosponsor_state.state
            HAVING COUNT(*) >= 5
        )
        SELECT 
            sponsor_state,
            cosponsor_state,
            collaboration_count
        FROM state_collaborations
        ORDER BY collaboration_count DESC
        LIMIT 50
        """
        
        collaboration_df = pd.read_sql(collaboration_query, self.engine)
        
        # Top regional subjects by state
        top_regional_subjects = (
            regional_df.groupby('state')
            .apply(lambda x: x.nlargest(5, 'bill_count'))
            .reset_index(drop=True)
            .groupby('state')
            .apply(lambda x: x[['subject', 'bill_count']].to_dict('records'))
            .to_dict()
        )
        
        report = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'analysis_period': '2 years (bills), 1 year (votes)',
            'state_delegations': state_df.to_dict('records'),
            'regional_bill_topics': regional_df.to_dict('records'),
            'cross_state_collaboration': collaboration_df.to_dict('records'),
            'top_subjects_by_state': top_regional_subjects,
            'summary_insights': {
                'total_states_represented': len(state_df),
                'largest_delegation': state_df.loc[state_df['total_delegation'].idxmax(), 'state'] if len(state_df) > 0 else None,
                'most_collaborative_state': collaboration_df.groupby('sponsor_state')['collaboration_count'].sum().idxmax() if len(collaboration_df) > 0 else None,
                'avg_delegation_size': float(state_df['total_delegation'].mean()) if len(state_df) > 0 else 0,
                'most_active_legislative_state': state_df.loc[state_df['avg_bills_per_member'].idxmax(), 'state'] if len(state_df) > 0 else None,
                'party_balance': {
                    'total_democratic': int(state_df['democratic_members'].sum()),
                    'total_republican': int(state_df['republican_members'].sum()),
                    'total_independent': int(state_df['independent_members'].sum())
                }
            }
        }
        
        self._save_report(report, 'geographic_analysis')
        logger.info("✅ Geographic analysis report generated")
        return report
    
    def _save_report(self, report_data: Dict[str, Any], report_name: str):
        """Save report in multiple formats."""
        # JSON format
        json_path = self.report_dir / f"{report_name}.json"
        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        # CSV format for tabular data
        if 'top_performers' in report_data or 'source_performance' in report_data:
            csv_path = self.report_dir / f"{report_name}.csv"
            
            # Determine main tabular data
            if 'top_performers' in report_data:
                df = pd.DataFrame(report_data['top_performers'])
            elif 'source_performance' in report_data:
                df = pd.DataFrame(report_data['source_performance'])
            elif 'monthly_trends' in report_data:
                df = pd.DataFrame(report_data['monthly_trends'])
            elif 'state_delegations' in report_data:
                df = pd.DataFrame(report_data['state_delegations'])
            else:
                df = pd.DataFrame([report_data.get('summary_statistics', {})])
            
            df.to_csv(csv_path, index=False)
        
        # Markdown summary
        md_path = self.report_dir / f"{report_name}.md"
        self._create_markdown_report(report_data, report_name, md_path)
        
        logger.info(f"📄 Report saved: {report_name}")
    
    def _create_markdown_report(self, report_data: Dict[str, Any], report_name: str, output_path: Path):
        """Create markdown version of report."""
        md_template = """# {{ title }}

## Summary

Generated on: {{ generated_at }}
Analysis Period: {{ analysis_period }}

{% if summary_statistics %}
### Key Statistics
{% for key, value in summary_statistics.items() %}
- **{{ key.replace('_', ' ').title() }}**: {{ value }}
{% endfor %}
{% endif %}

{% if summary_insights %}
### Key Insights
{% for insight in summary_insights %}
- {{ insight }}
{% endfor %}
{% endif %}

{% if summary_metrics %}
### Summary Metrics
{% for key, value in summary_metrics.items() %}
- **{{ key.replace('_', ' ').title() }}**: {{ value }}
{% endfor %}
{% endif %}

## Detailed Analysis

This report contains comprehensive analysis of government data across multiple dimensions. 
The full dataset and analysis are available in the accompanying JSON and CSV files.

{% if methodology %}
### Methodology
{{ methodology }}
{% endif %}

---
*Report generated by Government Data Analysis System*
"""
        
        template = Template(md_template)
        
        # Prepare template variables
        template_vars = {
            'title': report_name.replace('_', ' ').title(),
            'generated_at': report_data.get('generated_at', ''),
            'analysis_period': report_data.get('analysis_period', ''),
            'summary_statistics': report_data.get('summary_statistics'),
            'summary_insights': report_data.get('key_insights'),
            'summary_metrics': report_data.get('summary_metrics'),
            'methodology': report_data.get('methodology')
        }
        
        md_content = template.render(**template_vars)
        
        with open(output_path, 'w') as f:
            f.write(md_content)
    
    def generate_all_reports(self) -> str:
        """Generate all available reports."""
        logger.info("🚀 Generating comprehensive report suite...")
        
        reports_generated = []
        
        try:
            # Generate all reports
            self.generate_executive_summary()
            reports_generated.append("Executive Summary")
            
            self.generate_politician_effectiveness_report()
            reports_generated.append("Politician Effectiveness")
            
            self.generate_legislative_trends_report()
            reports_generated.append("Legislative Trends")
            
            self.generate_voting_patterns_report()
            reports_generated.append("Voting Patterns")
            
            self.generate_data_sources_report()
            reports_generated.append("Data Sources")
            
            self.generate_geographic_analysis_report()
            reports_generated.append("Geographic Analysis")
            
            # Generate master index
            self._generate_master_index(reports_generated)
            
            logger.info(f"🎉 All reports generated successfully: {', '.join(reports_generated)}")
            return str(self.report_dir)
            
        except Exception as e:
            logger.error(f"❌ Error generating reports: {e}")
            raise
    
    def _generate_master_index(self, reports_generated: List[str]):
        """Generate master index of all reports."""
        index_content = f"""# Government Data Analysis Report Suite

Generated on: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

## Available Reports

"""
        
        for report in reports_generated:
            report_filename = report.lower().replace(' ', '_')
            index_content += f"""
### {report}
- [JSON Data](./{report_filename}.json)
- [CSV Data](./{report_filename}.csv)
- [Summary](./{report_filename}.md)
"""
        
        index_content += """
## Report Descriptions

- **Executive Summary**: High-level overview of all data and key metrics
- **Politician Effectiveness**: Analysis of politician performance and rankings
- **Legislative Trends**: Patterns in bill introduction and passage
- **Voting Patterns**: Analysis of voting behavior and party unity
- **Data Sources**: Performance and quality of data sources
- **Geographic Analysis**: State and regional political patterns

## Data Sources

This analysis is based on data from 300+ government sources including:
- Federal agencies and departments
- Congressional records and voting data
- State and local government sources
- International government databases
- Transparency and research organizations

---
*Generated by Government Data Analysis System*
"""
        
        with open(self.report_dir / 'README.md', 'w') as f:
            f.write(index_content)

def main():
    """Main entry point for report generation."""
    parser = argparse.ArgumentParser(description="Government Data Analysis & Report Generator")
    
    parser.add_argument(
        '--report',
        choices=['all', 'executive', 'politician-effectiveness', 'legislative-trends', 
                'voting-patterns', 'data-sources', 'geographic'],
        default='all',
        help='Type of report to generate'
    )
    
    parser.add_argument(
        '--format',
        choices=['json', 'csv', 'markdown', 'all'],
        default='all',
        help='Output format for reports'
    )
    
    parser.add_argument(
        '--postgres-url',
        default=os.getenv('POSTGRES_URL', 'postgresql://postgres:postgres@localhost:5432/postgres'),
        help='PostgreSQL connection URL'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize reporter
        reporter = GovernmentDataReporter(args.postgres_url)
        
        # Generate requested reports
        if args.report == 'all':
            report_dir = reporter.generate_all_reports()
        elif args.report == 'executive':
            reporter.generate_executive_summary()
            report_dir = reporter.report_dir
        elif args.report == 'politician-effectiveness':
            reporter.generate_politician_effectiveness_report()
            report_dir = reporter.report_dir
        elif args.report == 'legislative-trends':
            reporter.generate_legislative_trends_report()
            report_dir = reporter.report_dir
        elif args.report == 'voting-patterns':
            reporter.generate_voting_patterns_report()
            report_dir = reporter.report_dir
        elif args.report == 'data-sources':
            reporter.generate_data_sources_report()
            report_dir = reporter.report_dir
        elif args.report == 'geographic':
            reporter.generate_geographic_analysis_report()
            report_dir = reporter.report_dir
        
        print(f"\n📊 Reports generated successfully!")
        print(f"📁 Location: {report_dir}")
        print(f"🔗 Open: file://{report_dir}/README.md")
        
    except Exception as e:
        logger.error(f"❌ Report generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()