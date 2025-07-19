"""
Tests for Results Comparison Engine
Simple tests for comparing deterministic vs agent results
"""

import pytest
import sys
import os

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

class TestComparisonEngine:
    """Test comparison between deterministic and agent results"""
    
    def test_compare_sentiment_results(self):
        """Test sentiment comparison between approaches"""
        from src.comparison.engine import ComparisonEngine
        
        engine = ComparisonEngine()
        
        det_result = {
            'sentiment': 'POSITIVE',
            'confidence': 0.8,
            'processing_time': 0.1
        }
        
        agent_result = {
            'sentiment': 'POSITIVE', 
            'confidence': 0.95,
            'processing_time': 5.2
        }
        
        comparison = engine.compare_sentiment(det_result, agent_result)
        
        assert 'agreement' in comparison
        assert 'confidence_diff' in comparison
        assert 'speed_advantage' in comparison
        
        # Should detect agreement
        assert comparison['agreement'] == True
        
        # Should calculate speed advantage
        assert comparison['speed_advantage'] > 1  # Deterministic should be faster
    
    def test_compare_disagreement(self):
        """Test handling of sentiment disagreement"""
        from src.comparison.engine import ComparisonEngine
        
        engine = ComparisonEngine()
        
        det_result = {'sentiment': 'NEGATIVE', 'confidence': 0.7}
        agent_result = {'sentiment': 'POSITIVE', 'confidence': 0.9}
        
        comparison = engine.compare_sentiment(det_result, agent_result)
        
        assert comparison['agreement'] == False
        assert 'disagreement_analysis' in comparison
    
    def test_generate_comparison_report(self):
        """Test complete comparison report generation"""
        from src.comparison.engine import ComparisonEngine
        
        engine = ComparisonEngine()
        
        deterministic_results = {
            'sentiment': 'POSITIVE',
            'keywords': ['great', 'app', 'music'],
            'issues': [],
            'processing_time': 0.05,
            'word_count': 20
        }
        
        agent_results = {
            'sentiment_analysis': {'sentiment': 'POSITIVE', 'confidence': 0.9},
            'topic_extraction': {'topics': ['music quality', 'user experience']},
            'issue_analysis': {'issues': []},
            'insights': {'patterns': ['positive user feedback']},
            'processing_time': 6.8
        }
        
        report = engine.generate_report(deterministic_results, agent_results, "Test review text")
        
        # Check report structure
        assert 'summary' in report
        assert 'sentiment_comparison' in report
        assert 'performance_metrics' in report
        assert 'recommendations' in report
        
        # Check performance metrics
        metrics = report['performance_metrics']
        assert 'speed_advantage' in metrics
        assert 'accuracy_comparison' in metrics
        assert 'cost_analysis' in metrics
    
    def test_calculate_accuracy_score(self):
        """Test accuracy scoring mechanism"""
        from src.comparison.engine import ComparisonEngine
        
        engine = ComparisonEngine()
        
        # Perfect agreement case
        det_result = {'sentiment': 'POSITIVE'}
        agent_result = {'sentiment': 'POSITIVE'}
        
        score = engine.calculate_accuracy_score(det_result, agent_result)
        assert score == 1.0
        
        # Disagreement case
        det_result = {'sentiment': 'NEGATIVE'}
        agent_result = {'sentiment': 'POSITIVE'}
        
        score = engine.calculate_accuracy_score(det_result, agent_result)
        assert score < 1.0
    
    def test_cost_analysis(self):
        """Test cost calculation for different approaches"""
        from src.comparison.engine import ComparisonEngine
        
        engine = ComparisonEngine()
        
        agent_result = {
            'processing_time': 8.0,
            'agent_calls': 4,
            'tokens_used': 1500
        }
        
        cost_analysis = engine.calculate_costs(agent_result)
        
        assert 'deterministic_cost' in cost_analysis
        assert 'agent_cost' in cost_analysis
        assert 'cost_ratio' in cost_analysis
        
        # Deterministic should be cheaper (essentially free)
        assert cost_analysis['deterministic_cost'] == 0
        assert cost_analysis['agent_cost'] > 0
    
    def test_quality_metrics(self):
        """Test quality assessment metrics"""
        from src.comparison.engine import ComparisonEngine
        
        engine = ComparisonEngine()
        
        deterministic_output = {
            'sentiment': 'POSITIVE',
            'keywords': ['good', 'app'],
            'issues': []
        }
        
        agent_output = {
            'sentiment_analysis': {'sentiment': 'POSITIVE'},
            'insights': {'patterns': ['user satisfaction', 'feature appreciation']},
            'issue_analysis': {'issues': []}
        }
        
        quality = engine.assess_quality(deterministic_output, agent_output)
        
        assert 'deterministic_quality' in quality
        assert 'agent_quality' in quality
        assert 'quality_dimensions' in quality
        
        # Quality should be scored 0-1
        assert 0 <= quality['deterministic_quality'] <= 1
        assert 0 <= quality['agent_quality'] <= 1


class TestReportGenerator:
    """Test PM report generation from comparison results"""
    
    def test_generate_pm_report(self):
        """Test PM-style report generation"""
        from src.comparison.report_generator import PMReportGenerator
        
        generator = PMReportGenerator()
        
        comparison_data = {
            'summary': {'agreement_rate': 0.85, 'total_reviews': 10},
            'performance_metrics': {'speed_advantage': 120, 'cost_ratio': 0},
            'sentiment_comparison': {'accuracy': 0.9},
            'insights_quality': {'agent_advantage': 0.7}
        }
        
        report = generator.generate_pm_report(comparison_data)
        
        # Should be markdown format
        assert isinstance(report, str)
        assert '# ' in report  # Should have headers
        assert 'Executive Summary' in report
        assert 'Key Findings' in report
        assert 'Recommendations' in report
    
    def test_export_json_report(self):
        """Test JSON export functionality"""
        from src.comparison.report_generator import PMReportGenerator
        
        generator = PMReportGenerator()
        
        data = {
            'deterministic': {'sentiment': 'POSITIVE'},
            'agents': {'sentiment': 'POSITIVE'},
            'comparison': {'agreement': True}
        }
        
        json_report = generator.export_json(data)
        
        assert isinstance(json_report, str)
        
        # Should be valid JSON
        import json
        parsed = json.loads(json_report)
        assert 'deterministic' in parsed
        assert 'agents' in parsed
        assert 'comparison' in parsed


class TestValidation:
    """Test input validation and error handling"""
    
    def test_empty_results_handling(self):
        """Test handling of empty or invalid results"""
        from src.comparison.engine import ComparisonEngine
        
        engine = ComparisonEngine()
        
        # Empty deterministic results
        comparison = engine.compare_sentiment({}, {'sentiment': 'POSITIVE'})
        assert 'error' in comparison or 'agreement' in comparison
        
        # Empty agent results  
        comparison = engine.compare_sentiment({'sentiment': 'POSITIVE'}, {})
        assert 'error' in comparison or 'agreement' in comparison
    
    def test_malformed_data_handling(self):
        """Test handling of malformed input data"""
        from src.comparison.engine import ComparisonEngine
        
        engine = ComparisonEngine()
        
        # Missing required fields
        det_result = {'not_sentiment': 'invalid'}
        agent_result = {'wrong_field': 'data'}
        
        comparison = engine.compare_sentiment(det_result, agent_result)
        assert 'error' in comparison or comparison is not None


if __name__ == "__main__":
    pytest.main([__file__])