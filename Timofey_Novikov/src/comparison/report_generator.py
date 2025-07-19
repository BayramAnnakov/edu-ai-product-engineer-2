"""
Simple PM Report Generator
Converts comparison results into PM-friendly reports
Following TDD - keeping it simple
"""

import json
import time
from datetime import datetime
from typing import Dict, Any


class PMReportGenerator:
    """Simple generator for PM-style reports"""
    
    def __init__(self):
        """Initialize report generator"""
        self.name = "SimplePMReportGenerator"
        self.version = "1.0.0"
    
    def generate_pm_report(self, comparison_data: Dict[str, Any]) -> str:
        """
        Generate PM-style markdown report
        
        Args:
            comparison_data: Comparison results from ComparisonEngine
            
        Returns:
            Markdown formatted report string
        """
        try:
            report_lines = []
            
            # Header
            report_lines.append("# 📊 Review Analysis Comparison Report")
            report_lines.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
            report_lines.append("")
            
            # Executive Summary
            report_lines.append("## Executive Summary")
            summary = comparison_data.get('summary', {})
            agreement_rate = summary.get('agreement_rate', 0)
            
            if agreement_rate >= 0.8:
                report_lines.append("✅ **High Agreement**: Both approaches show strong consensus")
            elif agreement_rate >= 0.5:
                report_lines.append("⚠️ **Moderate Agreement**: Some differences detected")
            else:
                report_lines.append("❌ **Low Agreement**: Significant differences require investigation")
            
            report_lines.append("")
            
            # Key Findings
            report_lines.append("## Key Findings")
            
            # Performance metrics
            perf_metrics = comparison_data.get('performance_metrics', {})
            speed_advantage = perf_metrics.get('speed_advantage', 0)
            
            report_lines.append(f"- **Speed**: Deterministic approach is {speed_advantage:.1f}x faster")
            
            # Cost analysis
            cost_analysis = perf_metrics.get('cost_analysis', {})
            agent_cost = cost_analysis.get('agent_cost', 0)
            report_lines.append(f"- **Cost**: Agent analysis costs ${agent_cost:.4f} per review")
            
            # Quality assessment
            quality = comparison_data.get('quality_assessment', {})
            det_quality = quality.get('deterministic_quality', 0)
            agent_quality = quality.get('agent_quality', 0)
            
            report_lines.append(f"- **Quality**: Deterministic ({det_quality:.2f}) vs Agent ({agent_quality:.2f})")
            report_lines.append("")
            
            # Recommendations
            report_lines.append("## Recommendations")
            recommendations = comparison_data.get('recommendations', [])
            
            if recommendations:
                for rec in recommendations:
                    report_lines.append(f"- {rec}")
            else:
                report_lines.append("- No specific recommendations at this time")
            
            report_lines.append("")
            
            # Technical Details
            report_lines.append("## Technical Details")
            sentiment_comp = comparison_data.get('sentiment_comparison', {})
            
            if sentiment_comp.get('agreement'):
                report_lines.append("**Sentiment Analysis**: ✅ Both approaches agree")
            else:
                det_sentiment = sentiment_comp.get('deterministic_sentiment', 'Unknown')
                agent_sentiment = sentiment_comp.get('agent_sentiment', 'Unknown')
                report_lines.append(f"**Sentiment Analysis**: ❌ Disagreement (Det: {det_sentiment}, Agent: {agent_sentiment})")
            
            return "\n".join(report_lines)
            
        except Exception as e:
            return f"# Error Generating Report\n\nError: {str(e)}"
    
    def export_json(self, data: Dict[str, Any]) -> str:
        """
        Export data as JSON string
        
        Args:
            data: Data to export
            
        Returns:
            JSON formatted string
        """
        try:
            # Add metadata
            export_data = {
                'deterministic': data.get('deterministic', {}),
                'agents': data.get('agents', {}),
                'comparison': data.get('comparison', {}),
                'metadata': {
                    'export_timestamp': datetime.now().isoformat(),
                    'generator_version': self.version
                }
            }
            
            return json.dumps(export_data, indent=2, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({'error': f'Export failed: {str(e)}'}, indent=2)