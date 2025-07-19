"""
Report Generator
Combines deterministic and LLM analysis results into PM-style reports
"""

import time
from typing import Dict, Any, List
from datetime import datetime
import json


def generate_executive_summary(det_results: Dict[str, Any], llm_results: Dict[str, Any]) -> str:
    """Generate executive summary from both analyses"""
    
    # Extract key metrics
    sentiment = det_results.get('sentiment', 'unknown')
    compound_score = det_results.get('sentiment_scores', {}).get('compound', 0)
    issues_count = det_results.get('issue_count', 0)
    
    # Determine overall tone
    if compound_score > 0.3:
        tone = "strongly positive"
    elif compound_score > 0.1:
        tone = "positive"
    elif compound_score < -0.3:
        tone = "strongly negative"
    elif compound_score < -0.1:
        tone = "negative"
    else:
        tone = "neutral"
    
    # Build summary
    summary = f"""
**Overall Assessment**: The review shows a {tone} sentiment (score: {compound_score:.3f}) with {issues_count} specific issues identified.

**Key Findings**: 
- Sentiment: {sentiment.title()}
- Processing Speed: Deterministic analysis completed in {det_results.get('processing_time', 0):.3f}s vs LLM analysis in {llm_results.get('processing_time', 0):.1f}s
- Issues Detected: {issues_count} specific problems identified
"""
    
    return summary.strip()


def generate_comparison_analysis(det_results: Dict[str, Any], llm_results: Dict[str, Any]) -> str:
    """Compare deterministic vs LLM approaches"""
    
    comparison = f"""
## 🔍 Approach Comparison

### Deterministic Analysis (NLTK)
- **Processing Time**: {det_results.get('processing_time', 0):.3f}s
- **Reproducibility**: 100% (same input → same output)
- **Sentiment**: {det_results.get('sentiment', 'unknown')} (compound: {det_results.get('sentiment_scores', {}).get('compound', 0):.3f})
- **Top Keywords**: {', '.join(det_results.get('top_keywords', [])[:3])}
- **Issues Found**: {det_results.get('issue_count', 0)}

### LLM Analysis (OpenAI)
- **Processing Time**: {llm_results.get('processing_time', 0):.1f}s
- **Reproducibility**: Variable (probabilistic output)
- **Model**: {llm_results.get('model_used', 'unknown')}
- **Tokens Used**: {llm_results.get('tokens_used', 0)}
- **Sentiment**: {llm_results.get('sentiment', 'unknown')}

### Trade-offs Analysis
- **Speed**: Deterministic is {(llm_results.get('processing_time', 1) / det_results.get('processing_time', 1)):.1f}x faster
- **Depth**: LLM provides contextual insights vs deterministic provides precise metrics
- **Cost**: Deterministic is free vs LLM has API costs
- **Reliability**: Deterministic is fully reproducible vs LLM varies with each run
"""
    
    return comparison.strip()


def generate_actionable_insights(det_results: Dict[str, Any], llm_results: Dict[str, Any]) -> str:
    """Generate actionable insights for product team"""
    
    insights = []
    
    # From deterministic analysis
    top_features = det_results.get('top_features', [])
    if top_features:
        top_feature = top_features[0]
        insights.append(f"**{top_feature[0].replace('_', ' ').title()}** is the most mentioned feature category ({top_feature[1]} mentions)")
    
    # From sentiment analysis
    sentiment = det_results.get('sentiment', 'neutral')
    if sentiment == 'negative':
        insights.append("**Immediate Action Required**: Negative sentiment detected - prioritize issue resolution")
    elif sentiment == 'positive':
        insights.append("**Strength to Leverage**: Positive sentiment - identify and amplify successful features")
    
    # From issues
    issues = det_results.get('issues_found', [])
    if issues:
        insights.append(f"**Critical Issues**: {len(issues)} specific problems identified requiring immediate attention")
    
    # From LLM analysis
    llm_insights = llm_results.get('insights', '')
    if llm_insights and llm_insights != "No specific insights extracted":
        insights.append(f"**LLM Insights**: {llm_insights}")
    
    llm_recommendations = llm_results.get('recommendations', '')
    if llm_recommendations and llm_recommendations != "No specific recommendations provided":
        insights.append(f"**AI Recommendations**: {llm_recommendations}")
    
    return '\n'.join(f"• {insight}" for insight in insights)


def generate_next_steps(det_results: Dict[str, Any], llm_results: Dict[str, Any]) -> List[str]:
    """Generate prioritized next steps"""
    
    steps = []
    
    # High priority based on issues
    issues_count = det_results.get('issue_count', 0)
    if issues_count > 0:
        steps.append(f"🔴 **HIGH PRIORITY**: Address {issues_count} identified issues")
    
    # Medium priority based on sentiment
    sentiment = det_results.get('sentiment', 'neutral')
    compound_score = det_results.get('sentiment_scores', {}).get('compound', 0)
    
    if sentiment == 'negative' and compound_score < -0.3:
        steps.append("🟡 **MEDIUM PRIORITY**: Investigate root causes of negative sentiment")
    elif sentiment == 'positive' and compound_score > 0.3:
        steps.append("🟢 **OPPORTUNITY**: Leverage positive feedback for marketing/testimonials")
    
    # Feature-based recommendations
    top_features = det_results.get('top_features', [])
    if top_features:
        for feature, count in top_features[:2]:
            if count > 0:
                steps.append(f"📋 **FEATURE FOCUS**: Analyze {feature.replace('_', ' ')} feedback ({count} mentions)")
    
    # LLM-based recommendations
    llm_recommendations = llm_results.get('recommendations', '')
    if llm_recommendations and llm_recommendations != "No specific recommendations provided":
        steps.append(f"💡 **AI SUGGESTION**: {llm_recommendations}")
    
    return steps


def generate_pm_report(det_results: Dict[str, Any], llm_results: Dict[str, Any], review_text: str = "") -> str:
    """
    Generate comprehensive PM-style report
    
    Args:
        det_results: Results from deterministic analysis
        llm_results: Results from LLM analysis
        review_text: Original review text (optional)
        
    Returns:
        Formatted markdown report
    """
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Check for errors
    if 'error' in det_results:
        return f"❌ **Error in deterministic analysis**: {det_results['error']}"
    
    if 'error' in llm_results:
        return f"❌ **Error in LLM analysis**: {llm_results['error']}"
    
    # Generate report sections
    executive_summary = generate_executive_summary(det_results, llm_results)
    comparison = generate_comparison_analysis(det_results, llm_results)
    insights = generate_actionable_insights(det_results, llm_results)
    next_steps = generate_next_steps(det_results, llm_results)
    
    # Build final report
    report = f"""# 📊 Product Review Analysis Report

**Generated**: {timestamp}  
**Analysis Methods**: Deterministic (NLTK) + Probabilistic (OpenAI)

---

## 🎯 Executive Summary

{executive_summary}

---

## 💡 Key Insights & Recommendations

{insights}

---

{comparison}

---

## 📋 Next Steps

{chr(10).join(next_steps)}

---

## 📈 Detailed Metrics

### Deterministic Analysis Results:
- **Sentiment**: {det_results.get('sentiment', 'unknown')} (compound: {det_results.get('sentiment_scores', {}).get('compound', 0):.3f})
- **Keywords**: {', '.join(det_results.get('top_keywords', []))}
- **Feature Categories**: {dict(det_results.get('feature_categories', {}))}
- **Issues Found**: {det_results.get('issue_count', 0)}
- **Processing Time**: {det_results.get('processing_time', 0):.3f}s

### LLM Analysis Results:
- **Model**: {llm_results.get('model_used', 'unknown')}
- **Tokens Used**: {llm_results.get('tokens_used', 0)}
- **Processing Time**: {llm_results.get('processing_time', 0):.1f}s
- **Sentiment**: {llm_results.get('sentiment', 'unknown')}

---

## 🔄 Methodology Notes

**Deterministic Approach**: Uses NLTK for sentiment analysis, TF-IDF for keyword extraction, and rule-based feature categorization. Results are 100% reproducible.

**Probabilistic Approach**: Uses OpenAI GPT model for contextual understanding and insight generation. Results may vary between runs.

**Trade-off**: Deterministic provides speed and consistency; LLM provides depth and contextual understanding.

---

*Report generated by Reviews Analysis Agent - AI Product Engineer Season 2*
"""
    
    return report


def export_report_json(det_results: Dict[str, Any], llm_results: Dict[str, Any], review_text: str = "") -> str:
    """Export report data as JSON"""
    
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "review_text": review_text,
        "deterministic_results": det_results,
        "llm_results": llm_results,
        "summary": {
            "sentiment_deterministic": det_results.get('sentiment', 'unknown'),
            "sentiment_llm": llm_results.get('sentiment', 'unknown'),
            "issues_count": det_results.get('issue_count', 0),
            "processing_time_deterministic": det_results.get('processing_time', 0),
            "processing_time_llm": llm_results.get('processing_time', 0),
            "speed_advantage": det_results.get('processing_time', 1) / llm_results.get('processing_time', 1) if llm_results.get('processing_time', 0) > 0 else 0
        }
    }
    
    return json.dumps(report_data, indent=2)


if __name__ == "__main__":
    # Test the report generator
    print("Testing Report Generator...")
    
    # Sample results for testing
    sample_det_results = {
        "sentiment": "positive",
        "sentiment_scores": {"compound": 0.5},
        "top_keywords": ["great", "app", "easy"],
        "feature_categories": {"ui_design": 2, "usability": 1},
        "top_features": [("ui_design", 2), ("usability", 1)],
        "issues_found": ["crashes sometimes"],
        "issue_count": 1,
        "processing_time": 0.123
    }
    
    sample_llm_results = {
        "sentiment": "Positive",
        "insights": "User appreciates interface design but has stability concerns",
        "recommendations": "Fix crashing issues, maintain current UI approach",
        "processing_time": 3.45,
        "model_used": "gpt-4",
        "tokens_used": 150
    }
    
    # Generate report
    report = generate_pm_report(sample_det_results, sample_llm_results, "Sample review text")
    print("✅ PM Report Generated:")
    print(report[:500] + "..." if len(report) > 500 else report)
    
    # Generate JSON export
    json_export = export_report_json(sample_det_results, sample_llm_results, "Sample review")
    print(f"\n✅ JSON Export Generated ({len(json_export)} characters)")
    
    print("\n🎉 Report Generator Test Complete!")