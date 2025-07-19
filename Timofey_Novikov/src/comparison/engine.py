"""
Simple Comparison Engine
Compares results between deterministic and LLM approaches
Following TDD - keeping it simple
"""

from typing import Dict, Any, List
import time


class ComparisonEngine:
    """Simple engine for comparing deterministic vs LLM analysis results"""
    
    def __init__(self):
        """Initialize comparison engine"""
        self.name = "SimpleComparisonEngine"
        self.version = "1.0.0"
    
    def compare_sentiment(self, det_result: Dict[str, Any], agent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare sentiment analysis results between approaches
        
        Args:
            det_result: Deterministic analysis result
            agent_result: Agent/LLM analysis result
            
        Returns:
            Comparison results dictionary
        """
        try:
            # Extract sentiments
            det_sentiment = det_result.get('sentiment')
            agent_sentiment = agent_result.get('sentiment')
            
            if not det_sentiment or not agent_sentiment:
                return {'error': 'Missing sentiment data'}
            
            # Check agreement
            agreement = det_sentiment == agent_sentiment
            
            # Calculate confidence difference
            det_confidence = det_result.get('confidence', 0)
            agent_confidence = agent_result.get('confidence', 0)
            confidence_diff = abs(det_confidence - agent_confidence)
            
            # Calculate speed advantage
            det_time = det_result.get('processing_time', 0)
            agent_time = agent_result.get('processing_time', 0)
            
            if det_time > 0 and agent_time > 0:
                speed_advantage = agent_time / det_time
            else:
                speed_advantage = 0
            
            result = {
                'agreement': agreement,
                'confidence_diff': confidence_diff,
                'speed_advantage': speed_advantage,
                'deterministic_sentiment': det_sentiment,
                'agent_sentiment': agent_sentiment
            }
            
            # Add disagreement analysis if needed
            if not agreement:
                result['disagreement_analysis'] = {
                    'deterministic': det_sentiment,
                    'agent': agent_sentiment,
                    'potential_reasons': ['context_interpretation', 'sarcasm_detection', 'threshold_differences']
                }
            
            return result
            
        except Exception as e:
            return {'error': f'Comparison failed: {str(e)}'}
    
    def calculate_accuracy_score(self, det_result: Dict[str, Any], agent_result: Dict[str, Any]) -> float:
        """
        Calculate accuracy score between approaches
        
        Args:
            det_result: Deterministic result
            agent_result: Agent result
            
        Returns:
            Accuracy score (0.0 to 1.0)
        """
        try:
            det_sentiment = det_result.get('sentiment')
            agent_sentiment = agent_result.get('sentiment')
            
            if det_sentiment == agent_sentiment:
                return 1.0
            else:
                return 0.0  # Simple binary accuracy for now
                
        except Exception:
            return 0.0
    
    def calculate_costs(self, agent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate cost analysis for different approaches
        
        Args:
            agent_result: Agent processing result
            
        Returns:
            Cost analysis dictionary
        """
        # Simple cost model
        deterministic_cost = 0  # Essentially free
        
        # Estimate LLM cost based on processing time and calls
        agent_calls = agent_result.get('agent_calls', 1)
        tokens_used = agent_result.get('tokens_used', 1000)  # Default estimate
        
        # Rough GPT-4 pricing: $0.03 per 1K tokens
        agent_cost = (tokens_used / 1000) * 0.03 * agent_calls
        
        cost_ratio = agent_cost / max(deterministic_cost, 0.001)  # Avoid division by zero
        
        return {
            'deterministic_cost': deterministic_cost,
            'agent_cost': round(agent_cost, 4),
            'cost_ratio': round(cost_ratio, 2),
            'cost_per_insight': round(agent_cost, 4)
        }
    
    def assess_quality(self, det_output: Dict[str, Any], agent_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess quality of outputs from both approaches
        
        Args:
            det_output: Deterministic analysis output
            agent_output: Agent analysis output
            
        Returns:
            Quality assessment dictionary
        """
        # Simple quality scoring
        det_quality = 0.0
        agent_quality = 0.0
        
        # Score deterministic output
        if 'sentiment' in det_output:
            det_quality += 0.3
        if 'keywords' in det_output and det_output['keywords']:
            det_quality += 0.3
        if 'issues' in det_output:
            det_quality += 0.2
        if det_output.get('processing_time', 0) < 1.0:  # Fast processing
            det_quality += 0.2
        
        # Score agent output
        if 'sentiment_analysis' in agent_output:
            agent_quality += 0.3
        if 'insights' in agent_output and agent_output['insights']:
            agent_quality += 0.4  # Higher weight for insights
        if 'issue_analysis' in agent_output:
            agent_quality += 0.3
        
        return {
            'deterministic_quality': min(det_quality, 1.0),
            'agent_quality': min(agent_quality, 1.0),
            'quality_dimensions': {
                'speed': 1.0 if det_output.get('processing_time', 0) < 1.0 else 0.5,
                'depth': 1.0 if 'insights' in agent_output else 0.3,
                'consistency': 1.0,  # Deterministic is always consistent
                'creativity': 0.8 if 'insights' in agent_output else 0.1
            }
        }
    
    def generate_report(self, det_results: Dict[str, Any], agent_results: Dict[str, Any], review_text: str) -> Dict[str, Any]:
        """
        Generate comprehensive comparison report
        
        Args:
            det_results: Deterministic analysis results
            agent_results: Agent analysis results
            review_text: Original review text
            
        Returns:
            Complete comparison report
        """
        start_time = time.time()
        
        try:
            # Perform comparisons
            sentiment_comparison = self.compare_sentiment(det_results, agent_results)
            accuracy_score = self.calculate_accuracy_score(det_results, agent_results)
            cost_analysis = self.calculate_costs(agent_results)
            quality_assessment = self.assess_quality(det_results, agent_results)
            
            # Performance metrics
            det_time = det_results.get('processing_time', 0)
            agent_time = agent_results.get('processing_time', 0)
            
            processing_time = time.time() - start_time
            
            report = {
                'summary': {
                    'review_length': len(review_text) if review_text else 0,
                    'agreement_rate': accuracy_score,
                    'processing_comparison': {
                        'deterministic_time': det_time,
                        'agent_time': agent_time,
                        'speed_ratio': agent_time / max(det_time, 0.001)
                    }
                },
                'sentiment_comparison': sentiment_comparison,
                'performance_metrics': {
                    'speed_advantage': sentiment_comparison.get('speed_advantage', 0),
                    'accuracy_comparison': accuracy_score,
                    'cost_analysis': cost_analysis
                },
                'quality_assessment': quality_assessment,
                'recommendations': self._generate_recommendations(sentiment_comparison, cost_analysis, quality_assessment),
                'metadata': {
                    'comparison_time': round(processing_time, 3),
                    'engine_version': self.version,
                    'timestamp': time.time()
                }
            }
            
            return report
            
        except Exception as e:
            return {
                'error': f'Report generation failed: {str(e)}',
                'processing_time': time.time() - start_time
            }
    
    def _generate_recommendations(self, sentiment_comp: Dict[str, Any], cost_analysis: Dict[str, Any], quality_assessment: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on comparison results"""
        recommendations = []
        
        # Agreement recommendations
        if sentiment_comp.get('agreement'):
            recommendations.append("Both approaches agree on sentiment - high confidence in result")
        else:
            recommendations.append("Sentiment disagreement detected - manual review recommended")
        
        # Cost recommendations
        agent_cost = cost_analysis.get('agent_cost', 0)
        if agent_cost > 0.05:
            recommendations.append("Consider using deterministic approach for high-volume analysis")
        
        # Quality recommendations
        det_quality = quality_assessment.get('deterministic_quality', 0)
        agent_quality = quality_assessment.get('agent_quality', 0)
        
        if agent_quality > det_quality + 0.2:
            recommendations.append("Agent provides significantly better insights - worth the cost")
        elif det_quality > agent_quality:
            recommendations.append("Deterministic approach sufficient for this type of analysis")
        
        return recommendations