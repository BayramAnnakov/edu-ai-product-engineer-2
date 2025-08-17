"""
Shared memory implementation for Virtual Board agents
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
import json
from collections import defaultdict
from ..constants import AgentType, MemoryEntryType


@dataclass
class MemoryEntry:
    """Single entry in shared memory"""
    timestamp: datetime
    agent_id: str
    entry_type: str  # 'response', 'analysis', 'insight', 'question'
    content: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


class SharedMemory:
    """
    Shared memory store for agent coordination and knowledge sharing.
    Implements a simple in-memory store with categorized access.
    """
    
    def __init__(self):
        # Categorized memory stores
        self.responses: Dict[str, List[MemoryEntry]] = defaultdict(list)  # by persona_id
        self.analyses: List[MemoryEntry] = []
        self.insights: List[MemoryEntry] = []
        self.questions: List[MemoryEntry] = []
        self.themes: Dict[str, List[MemoryEntry]] = defaultdict(list)  # by theme
        self.hypotheses: Dict[str, List[MemoryEntry]] = defaultdict(list)  # by hypothesis_id
        
        # Cross-references for quick lookup
        self.persona_themes: Dict[str, set] = defaultdict(set)  # persona_id -> themes
        self.theme_personas: Dict[str, set] = defaultdict(set)  # theme -> persona_ids
        
        # Session metadata
        self.session_start = datetime.now()
        self.interaction_count = 0
    
    def store_response(self, persona_id: str, question: str, response: str, phase: str) -> None:
        """Store a persona response"""
        entry = MemoryEntry(
            timestamp=datetime.now(),
            agent_id=persona_id,
            entry_type=MemoryEntryType.RESPONSE,
            content={
                "question": question,
                "response": response,
                "phase": phase
            }
        )
        self.responses[persona_id].append(entry)
        self.interaction_count += 1
    
    def store_analysis(self, analysis: Dict[str, Any], persona_id: str) -> None:
        """Store an analysis result"""
        entry = MemoryEntry(
            timestamp=datetime.now(),
            agent_id=AgentType.ANALYST,
            entry_type=MemoryEntryType.ANALYSIS,
            content=analysis,
            metadata={"persona_id": persona_id}
        )
        self.analyses.append(entry)
        
        # Update theme mappings
        for theme in analysis.get("themes", []):
            self.themes[theme].append(entry)
            self.persona_themes[persona_id].add(theme)
            self.theme_personas[theme].add(persona_id)
        
        # Update hypothesis mappings
        for hyp_id in analysis.get("hypotheses_hit", []):
            self.hypotheses[hyp_id].append(entry)
    
    def store_insight(self, insight: str, supporting_data: Dict[str, Any]) -> None:
        """Store a synthesized insight"""
        entry = MemoryEntry(
            timestamp=datetime.now(),
            agent_id=AgentType.FACILITATOR,
            entry_type=MemoryEntryType.INSIGHT,
            content={
                "insight": insight,
                "supporting_data": supporting_data
            }
        )
        self.insights.append(entry)
    
    def store_question(self, question: str, target_personas: List[str], metadata: Dict[str, Any]) -> None:
        """Store a facilitator question"""
        entry = MemoryEntry(
            timestamp=datetime.now(),
            agent_id=AgentType.FACILITATOR,
            entry_type=MemoryEntryType.QUESTION,
            content={
                "question": question,
                "target_personas": target_personas
            },
            metadata=metadata
        )
        self.questions.append(entry)
    
    def get_persona_history(self, persona_id: str) -> List[Dict[str, Any]]:
        """Get all responses from a specific persona"""
        return [
            {
                "timestamp": entry.timestamp.isoformat(),
                "question": entry.content["question"],
                "response": entry.content["response"],
                "phase": entry.content["phase"]
            }
            for entry in self.responses.get(persona_id, [])
        ]
    
    def get_theme_distribution(self) -> Dict[str, Dict[str, Any]]:
        """Get theme distribution across personas"""
        distribution = {}
        for theme, personas in self.theme_personas.items():
            distribution[theme] = {
                "count": len(self.themes[theme]),
                "personas": list(personas),
                "percentage": len(personas) / len(self.responses) * 100 if self.responses else 0
            }
        return distribution
    
    def get_hypothesis_coverage(self) -> Dict[str, float]:
        """Calculate hypothesis coverage based on stored analyses"""
        coverage = {}
        total_analyses = len(self.analyses)
        
        if total_analyses == 0:
            return coverage
        
        for hyp_id, entries in self.hypotheses.items():
            # Coverage is percentage of analyses that hit this hypothesis
            coverage[hyp_id] = len(entries) / total_analyses
        
        return coverage
    
    def get_conflicting_views(self, theme: str) -> List[Dict[str, Any]]:
        """Find conflicting views on a specific theme"""
        theme_entries = self.themes.get(theme, [])
        conflicting = []
        
        # Group by sentiment
        positive = []
        negative = []
        
        for entry in theme_entries:
            if entry.entry_type == MemoryEntryType.ANALYSIS:
                sentiment = entry.content.get("sentiment", 0)
                persona_id = entry.metadata.get("persona_id")
                
                if sentiment > 0.3:
                    positive.append(persona_id)
                elif sentiment < -0.3:
                    negative.append(persona_id)
        
        if positive and negative:
            conflicting.append({
                "theme": theme,
                "positive_personas": positive,
                "negative_personas": negative,
                "conflict_type": "sentiment"
            })
        
        return conflicting
    
    def get_consensus_themes(self, min_personas: int = 2) -> List[str]:
        """Get themes mentioned by at least min_personas"""
        return [
            theme for theme, personas in self.theme_personas.items()
            if len(personas) >= min_personas
        ]
    
    def get_recent_context(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent interaction context across all agents"""
        all_entries = []
        
        # Collect all entries
        for persona_entries in self.responses.values():
            all_entries.extend(persona_entries)
        all_entries.extend(self.analyses)
        all_entries.extend(self.insights)
        all_entries.extend(self.questions)
        
        # Sort by timestamp and return most recent
        all_entries.sort(key=lambda x: x.timestamp, reverse=True)
        
        return [
            {
                "timestamp": entry.timestamp.isoformat(),
                "agent_id": entry.agent_id,
                "type": entry.entry_type,
                "content": entry.content
            }
            for entry in all_entries[:limit]
        ]
    
    def export_memory_state(self) -> Dict[str, Any]:
        """Export full memory state for persistence"""
        return {
            "session_start": self.session_start.isoformat(),
            "interaction_count": self.interaction_count,
            "personas": {
                pid: self.get_persona_history(pid)
                for pid in self.responses
            },
            "theme_distribution": self.get_theme_distribution(),
            "hypothesis_coverage": self.get_hypothesis_coverage(),
            "consensus_themes": self.get_consensus_themes(),
            "total_analyses": len(self.analyses),
            "total_insights": len(self.insights)
        }


class MemoryManager:
    """
    Manages shared memory access for agents with context building
    """
    
    def __init__(self):
        self.memory = SharedMemory()
    
    def build_persona_context(self, persona_id: str) -> str:
        """Build context string for a persona based on their history"""
        history = self.memory.get_persona_history(persona_id)
        
        if not history:
            return "This is your first response in the discussion."
        
        context_parts = [f"You have participated in {len(history)} previous exchanges."]
        
        # Add recent responses
        recent = history[-2:]  # Last 2 responses
        if recent:
            context_parts.append("\nYour recent responses:")
            for item in recent:
                context_parts.append(f"- Q: {item['question']}")
                context_parts.append(f"  A: {item['response'][:100]}...")
        
        return "\n".join(context_parts)
    
    def build_analysis_context(self) -> str:
        """Build context for the analyst based on recent patterns"""
        theme_dist = self.memory.get_theme_distribution()
        coverage = self.memory.get_hypothesis_coverage()
        
        context_parts = []
        
        # Top themes
        if theme_dist:
            top_themes = sorted(theme_dist.items(), key=lambda x: x[1]['count'], reverse=True)[:3]
            context_parts.append("Top themes so far:")
            for theme, data in top_themes:
                context_parts.append(f"- {theme}: mentioned by {len(data['personas'])} personas")
        
        # Coverage status
        if coverage:
            context_parts.append("\nHypothesis coverage:")
            for hyp_id, cov in coverage.items():
                context_parts.append(f"- {hyp_id}: {cov:.0%}")
        
        return "\n".join(context_parts)
    
    def build_facilitator_context(self) -> str:
        """Build context for the facilitator based on discussion state"""
        consensus = self.memory.get_consensus_themes()
        recent = self.memory.get_recent_context(3)
        
        context_parts = []
        
        if consensus:
            context_parts.append(f"Consensus themes: {', '.join(consensus)}")
        
        if recent:
            context_parts.append("\nRecent activity:")
            for item in recent:
                context_parts.append(f"- {item['agent_id']}: {item['type']}")
        
        context_parts.append(f"\nTotal interactions: {self.memory.interaction_count}")
        
        return "\n".join(context_parts)