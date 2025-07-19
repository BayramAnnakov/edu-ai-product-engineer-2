"""
Tests for OpenAI Agents SDK Integration
Simple tests focusing on core agent functionality
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os
import json

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

class TestAgentCoordinator:
    """Test Agent Coordinator functionality"""
    
    def test_coordinator_initialization(self):
        """Test that coordinator initializes correctly"""
        from src.agents.coordinator import AgentCoordinator
        
        coordinator = AgentCoordinator()
        
        assert coordinator.model == "gpt-4.1"
        assert hasattr(coordinator, 'agents')
        assert len(coordinator.agents) == 4  # 4 specialized agents
    
    def test_process_review_structure(self):
        """Test that agent processing returns correct structure"""
        from src.agents.coordinator import AgentCoordinator
        
        coordinator = AgentCoordinator()
        
        # Mock OpenAI responses
        mock_responses = {
            'sentiment': {'sentiment': 'POSITIVE', 'confidence': 0.9, 'emotions': ['joy']},
            'topics': {'topics': ['music quality', 'user interface'], 'categories': ['audio', 'ui']},
            'issues': {'issues': [{'type': 'crash', 'severity': 'high'}]},
            'insights': {'patterns': ['user satisfaction'], 'recommendations': ['fix crashes']}
        }
        
        with patch.object(coordinator, '_call_agent') as mock_call:
            mock_call.side_effect = lambda agent, text: mock_responses.get(agent, {})
            
            result = coordinator.process_review("Test review text")
            
            # Check structure
            assert 'sentiment_analysis' in result
            assert 'topic_extraction' in result
            assert 'issue_analysis' in result
            assert 'insights' in result
            assert 'processing_time' in result
            assert 'agent_calls' in result
    
    def test_agent_error_handling(self):
        """Test handling of agent failures"""
        from src.agents.coordinator import AgentCoordinator
        
        coordinator = AgentCoordinator()
        
        with patch.object(coordinator, '_call_agent') as mock_call:
            mock_call.side_effect = Exception("API Error")
            
            result = coordinator.process_review("Test review")
            
            # Should handle errors gracefully
            assert 'error' in result or all(key in result for key in ['sentiment_analysis', 'topic_extraction'])
    
    def test_performance_requirement(self):
        """Test that agent processing meets time requirements"""
        import time
        from src.agents.coordinator import AgentCoordinator
        
        coordinator = AgentCoordinator()
        
        # Mock fast responses
        with patch.object(coordinator, '_call_agent') as mock_call:
            mock_call.return_value = {'result': 'mocked'}
            
            start_time = time.time()
            result = coordinator.process_review("Test review text")
            end_time = time.time()
            
            processing_time = end_time - start_time
            assert processing_time < 15  # Should be under 15 seconds total
            assert result['processing_time'] < 15


class TestSentimentAgent:
    """Test Sentiment Analysis Agent"""
    
    def test_sentiment_agent_positive(self):
        """Test sentiment agent with positive review"""
        from src.agents.sentiment_agent import SentimentAgent
        
        agent = SentimentAgent()
        
        # Mock OpenAI response
        mock_response = {
            "sentiment": "POSITIVE",
            "confidence": 0.95,
            "emotions": ["joy", "satisfaction"],
            "intensity": "high"
        }
        
        with patch('openai.ChatCompletion.create') as mock_openai:
            mock_openai.return_value.choices[0].message.content = json.dumps(mock_response)
            
            result = agent.analyze("I love this app! It's fantastic!")
            
            assert result['sentiment'] == 'POSITIVE'
            assert result['confidence'] > 0.9
            assert 'emotions' in result
    
    def test_sentiment_agent_structured_output(self):
        """Test that sentiment agent returns structured JSON"""
        from src.agents.sentiment_agent import SentimentAgent
        
        agent = SentimentAgent()
        
        with patch('openai.ChatCompletion.create') as mock_openai:
            mock_openai.return_value.choices[0].message.content = '{"sentiment": "NEGATIVE", "confidence": 0.8}'
            
            result = agent.analyze("This app is terrible")
            
            # Should be valid JSON structure
            assert isinstance(result, dict)
            assert 'sentiment' in result
            assert 'confidence' in result


class TestTopicAgent:
    """Test Topic Extraction Agent"""
    
    def test_topic_extraction(self):
        """Test topic extraction functionality"""
        from src.agents.topic_agent import TopicAgent
        
        agent = TopicAgent()
        
        mock_response = {
            "topics": ["music quality", "user interface", "crashes"],
            "categories": ["audio", "ui", "stability"],
            "importance_scores": [0.9, 0.7, 0.8]
        }
        
        with patch('openai.ChatCompletion.create') as mock_openai:
            mock_openai.return_value.choices[0].message.content = json.dumps(mock_response)
            
            result = agent.extract_topics("The music quality is great but the UI crashes")
            
            assert 'topics' in result
            assert isinstance(result['topics'], list)
            assert len(result['topics']) > 0


class TestIssueAgent:
    """Test Issue Analysis Agent"""
    
    def test_issue_detection(self):
        """Test issue detection and prioritization"""
        from src.agents.issue_agent import IssueAgent
        
        agent = IssueAgent()
        
        mock_response = {
            "issues": [
                {
                    "type": "crash",
                    "severity": "high",
                    "description": "App crashes when switching playlists",
                    "impact": "user_experience",
                    "recommendation": "Fix playlist switching logic"
                }
            ]
        }
        
        with patch('openai.ChatCompletion.create') as mock_openai:
            mock_openai.return_value.choices[0].message.content = json.dumps(mock_response)
            
            result = agent.detect_issues("App crashes when I switch playlists")
            
            assert 'issues' in result
            assert isinstance(result['issues'], list)
            if result['issues']:
                issue = result['issues'][0]
                assert 'type' in issue
                assert 'severity' in issue


class TestInsightsAgent:
    """Test Insights Generation Agent"""
    
    def test_insights_generation(self):
        """Test creative insights generation"""
        from src.agents.insights_agent import InsightsAgent
        
        agent = InsightsAgent()
        
        mock_response = {
            "patterns": ["Users love music quality but hate crashes"],
            "trends": ["Increasing complaints about stability"],
            "recommendations": ["Prioritize stability over new features"],
            "hypotheses": ["Crashes correlate with playlist size"]
        }
        
        with patch('openai.ChatCompletion.create') as mock_openai:
            mock_openai.return_value.choices[0].message.content = json.dumps(mock_response)
            
            result = agent.generate_insights("Music app with quality issues")
            
            assert 'patterns' in result or 'insights' in result
            assert isinstance(result.get('patterns', result.get('insights', [])), list)


class TestAgentTools:
    """Test Agent Tool Functions"""
    
    def test_sentiment_tool(self):
        """Test sentiment analysis tool"""
        from src.agents.tools import sentiment_analyzer_tool
        
        result = sentiment_analyzer_tool("Great app!")
        
        assert isinstance(result, dict)
        assert 'sentiment' in result
    
    def test_topic_tool(self):
        """Test topic modeling tool"""
        from src.agents.tools import topic_modeler_tool
        
        result = topic_modeler_tool("Music streaming with good quality")
        
        assert isinstance(result, dict)
        assert 'topics' in result or 'categories' in result


if __name__ == "__main__":
    pytest.main([__file__])