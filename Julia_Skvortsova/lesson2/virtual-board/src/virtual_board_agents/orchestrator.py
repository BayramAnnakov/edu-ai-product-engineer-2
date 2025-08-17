"""
Virtual Board Orchestrator using OpenAI Agents SDK
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
from ..models import SessionReport
from ..constants import Phase
from ..config import BoardConfig
from .session import VirtualBoardSession


class VirtualBoardOrchestrator:
    """
    Production-ready orchestrator using OpenAI Agents SDK with full agent capabilities
    """
    
    # Default questions for each phase when config is empty
    DEFAULT_QUESTIONS = {
        Phase.WARMUP: [
            "What are your initial thoughts on {product_name}?",
            "What challenges do you currently face in this area?"
        ],
        Phase.DIVERGE: [
            "What are your thoughts on this product concept?",
            "What features would be most valuable to you?",
            "What concerns or challenges do you see?"
        ],
        Phase.REFLECT: [
            "Based on the themes we've discussed, which resonate most with you?",
            "Are there any important perspectives we haven't considered?"
        ],
        Phase.CONVERGE: [
            "If you had to choose between ease of use and advanced features, which would you prioritize?",
            "What's the maximum you would pay for this solution?"
        ],
        Phase.CLOSURE: [
            "What's the biggest risk you see with this product?",
            "What would make you NOT use this product?",
            "What are we missing or overlooking?"
        ]
    }
    
    
    def __init__(self, config: BoardConfig):
        self.config = config
        self.session = VirtualBoardSession(config)
        self.start_time = datetime.now()
    
    def _get_phase_questions(self, phase: Phase) -> list:
        """Get questions for a specific phase from config with intelligent defaults"""
        questions_config = getattr(self.config, 'questions', None)
        
        if not questions_config:
            raw_questions = []
        else:
            # Phase enum values directly match config attribute names
            raw_questions = getattr(questions_config, phase.value, [])
        
        # Use defaults if no config questions, with product name substitution
        if not raw_questions:
            default_questions = self.DEFAULT_QUESTIONS.get(phase, [])
            return [q.format(product_name=self.config.product.name) for q in default_questions]
        
        # Handle mixed string/dict format in config
        questions = []
        for q in raw_questions:
            if isinstance(q, dict):
                questions.append(q)  # Keep dict format for diverge phase processing
            elif hasattr(q, 'model_dump'):  # Pydantic model
                questions.append(q.model_dump())  # Convert to dict
            else:
                questions.append(str(q))  # Convert to string
        
        return questions
    
    async def run_session(self) -> SessionReport:
        """Run complete virtual board session with SDK agents"""
        print("🚀 Starting Virtual Board Session (SDK Version)...")
        print(f"Product: {self.config.product.name}")
        print(f"Personas: {', '.join(p.name for p in self.config.personas)}")
        print(f"Hypotheses: {', '.join(h.id for h in self.config.hypotheses)}")
        
        try:
            # Introduce the product to all personas
            await self._introduce_product()
            
            # Run phases
            await self._run_warmup_phase()
            await self._run_diverge_phase()
            
            # Check coverage before reflect phase
            if self.session.state.coverage_percentage() >= 0.7:
                await self._run_reflect_phase()
            else:
                print("⚠️ Skipping reflect phase due to low coverage")
            
            await self._run_converge_phase()
            await self._run_closure_phase()
            
            # Export session data
            await self._export_session_data()
            
            # Generate report
            report = self._generate_report()
            
            # Export production metrics
            self._export_production_metrics()
            
            return report
            
        except Exception as e:
            print(f"❌ Session failed: {e}")
            # Export what we have for debugging
            await self._export_session_data()
            self._export_production_metrics()
            raise
    
    async def _introduce_product(self) -> None:
        """Introduce the product to all personas before starting questions"""
        print("\n=== PRODUCT INTRODUCTION ===")
        
        
        print(f"\n📢 Introducing product to all personas...")
        print(f"Product: {self.config.product.name}")
        
        # Store the product introduction as context for all future questions
        self.product_context = f"Product: {self.config.product.name}\nDescription: {self.config.product.description}"
        
        # Optionally, we could ask personas to acknowledge the product
        # For now, we'll just set the context
        print("✅ Product introduction complete")
    
    async def _run_warmup_phase(self) -> None:
        """Warmup phase: Initial impressions using config warmup questions"""
        print("\n=== WARMUP PHASE ===")
        self.session.transition_phase(Phase.WARMUP)
        
        # Get warmup questions from config (includes intelligent defaults)
        warmup_questions = self._get_phase_questions(Phase.WARMUP)
        
        for idx, question in enumerate(warmup_questions, 1):
            print(f"\n📝 Warmup Question {idx}/{len(warmup_questions)}: {question}", flush=True)
            
            # Use helper for ask and analyze pattern
            await self._ask_and_analyze_all(
                question=question,
                context=self.product_context,
                check_bias=True,
                generate_followups=False  # No follow-ups in warmup
            )
            
            print(f"\n📊 Warmup Question {idx} completed", flush=True)
        
        print(f"\n✅ Warmup phase completed with {len(warmup_questions)} questions")
    
    async def _run_diverge_phase(self) -> None:
        """Diverge phase: Broad exploration using config diverge questions"""
        print("\n=== DIVERGE PHASE ===")
        self.session.transition_phase(Phase.DIVERGE)
        
        # Get diverge questions from config (includes intelligent defaults)
        diverge_questions = self._get_phase_questions(Phase.DIVERGE)
        
        for idx, question_config in enumerate(diverge_questions, 1):
            # Handle both string questions and question objects with covers
            if isinstance(question_config, dict):
                question = question_config.get('text', '')
                covers = question_config.get('covers', [])
                print(f"\n📝 Question {idx}/{len(diverge_questions)}: {question}")
                if covers:
                    print(f"   Targets hypotheses: {', '.join(covers)}")
            else:
                question = str(question_config)
                print(f"\n📝 Question {idx}/{len(diverge_questions)}: {question}")
            
            # Use helper for the full ask-analyze-followup pattern
            await self._ask_and_analyze_all(
                question=question,
                context=self.product_context,
                check_bias=True,
                check_drift_interval=3,  # Check drift every 3 questions
                generate_followups=True,  # Generate follow-ups in diverge
                question_idx=idx
            )
            
            # Check coverage
            coverage = self.session.state.coverage_percentage()
            print(f"\n📊 Hypothesis coverage: {coverage:.0%}")
        
        print(f"\n✅ Diverge phase completed with {len(diverge_questions)} diverge questions")
    
    async def _run_reflect_phase(self) -> None:
        """Reflect phase: Share synthesized themes"""
        print("\n=== REFLECT PHASE ===")
        self.session.transition_phase(Phase.REFLECT)
        
        # Cluster themes from diverge phase
        theme_clusters = await self.session.cluster_themes_for_phase(Phase.DIVERGE)
        
        print(f"\n🎯 Found {len(theme_clusters)} theme clusters")
        for cluster in theme_clusters[:3]:  # Top 3
            print(f"  - {cluster.theme_name}: {cluster.frequency} mentions by {len(cluster.personas_mentioned)} personas")
        
        # Share themes with personas for validation
        if theme_clusters:
            themes_summary = "\n".join([
                f"- {c.theme_name}: {c.representative_quotes[0][:256]}..."
                for c in theme_clusters[:5]
            ])
            
            question = f"Here are the main themes we've heard so far:\n{themes_summary}\n\nWhich of these resonate most with you and why?"
            
            # Use helper for theme validation
            await self._ask_and_analyze_all(
                question=question,
                context=f"{self.product_context}\n\nTheme validation phase",
                check_bias=False,  # Theme sharing doesn't need bias check
                generate_followups=False  # No follow-ups in reflect phase
            )
    
    async def _run_converge_phase(self) -> None:
        """Converge phase: Trade-offs and priorities using config converge questions"""
        print("\n=== CONVERGE PHASE ===")
        self.session.transition_phase(Phase.CONVERGE)
        
        # Get converge questions from config (includes intelligent defaults)
        converge_questions = self._get_phase_questions(Phase.CONVERGE)
        
        print(f"\n🎯 Running {len(converge_questions)} converge questions")
        
        for idx, question in enumerate(converge_questions, 1):
            print(f"\n📝 Converge Question {idx}/{len(converge_questions)}: {question}")
            
            # Use helper for converge questions
            await self._ask_and_analyze_all(
                question=question,
                context=self.product_context,
                check_bias=True,
                generate_followups=False  # No follow-ups in converge phase
            )
        
        # Get conflicting views from memory for additional insights
        conflicts = []
        for theme in self.session.memory_manager.memory.get_consensus_themes():
            theme_conflicts = self.session.memory_manager.memory.get_conflicting_views(theme)
            conflicts.extend(theme_conflicts)
        
        if conflicts:
            print(f"\n⚔️ Identified {len(conflicts)} conflicting viewpoints across themes")
        
        print(f"\n✅ Converge phase completed with {len(converge_questions)} questions")
    
    async def _run_closure_phase(self) -> None:
        """Closure phase: Final insights and red team using config closure questions"""
        print("\n=== CLOSURE PHASE ===")
        self.session.transition_phase(Phase.CLOSURE)
        
        # Synthesize session insights first
        insights = await self.session.synthesize_session_insights()
        
        print("\n🔍 Key Insights:")
        if isinstance(insights, dict):
            for key, value in insights.items():
                if isinstance(value, list):
                    print(f"\n{key}:")
                    for item in value[:3]:
                        print(f"  - {item}")
        
        # Get closure questions from config (includes intelligent defaults)
        closure_questions = self._get_phase_questions(Phase.CLOSURE)
        
        print(f"\n🔴 Running {len(closure_questions)} closure questions")
        
        for idx, question in enumerate(closure_questions, 1):
            print(f"\n📝 Closure Question {idx}/{len(closure_questions)}: {question}")
            
            # Use helper for closure questions
            results = await self._ask_and_analyze_all(
                question=question,
                context=self.product_context,
                check_bias=False,  # Red team questions can be provocative
                generate_followups=False  # No follow-ups in closure
            )
            
            # Print final themes if any
            for persona_id, result in results.items():
                if result['analysis'].themes:
                    print(f"  Final themes: {', '.join(result['analysis'].themes[:2])}")
        
        print(f"\n✅ Closure phase completed with {len(closure_questions)} critical questions")
    
    async def _ask_and_analyze_all(
        self,
        question: str,
        context: Optional[str] = None,
        check_bias: bool = True,
        check_drift_interval: Optional[int] = None,
        generate_followups: bool = False,
        question_idx: Optional[int] = None
    ) -> Dict[str, Dict]:
        """
        Helper method to handle the common pattern of:
        1. Check question bias
        2. Ask all personas
        3. Analyze each response
        4. Optionally check drift
        5. Optionally generate follow-ups
        
        Returns dict mapping persona_id to {'response', 'analysis', 'followup'}
        """
        results = {}
        
        # Step 1: Check for bias if requested
        if check_bias:
            bias_check = await self.session.check_question_bias(question, context)
            if bias_check.has_bias:
                print(f"⚠️ Bias detected ({bias_check.severity}): {bias_check.recommendation}")
        
        # Step 2: Ask all personas
        responses = await self.session.ask_all_personas(
            question, 
            context=context or self.product_context
        )
        
        # Step 3-5: Process each response
        for persona_id, response in responses.items():
            result = {'response': response}
            
            # Analyze response
            analysis = await self.session.analyze_response(
                persona_id, response, question
            )
            result['analysis'] = analysis
            
            # Print summary
            print(f"\n{self._get_persona_name(persona_id)}: {response}")
            print(f"  Themes: {', '.join(analysis.themes[:3])}")
            if hasattr(analysis, 'hypotheses_hit') and analysis.hypotheses_hit:
                print(f"  Hypotheses hit: {analysis.hypotheses_hit}")
            if hasattr(analysis, 'sentiment'):
                print(f"  Sentiment: {analysis.sentiment:+.2f}")
            
            # Check for drift if requested
            if check_drift_interval and question_idx and question_idx % check_drift_interval == 0:
                drift_detected = await self.session.check_persona_drift(persona_id, response)
                if drift_detected:
                    print(f"  ⚠️ Persona drift detected!")
            
            # Generate follow-up if requested
            if generate_followups:
                followup = await self.session.generate_followup(
                    persona_id, response, analysis
                )
                
                if followup:
                    print(f"\n  Follow-up for {self._get_persona_name(persona_id)}: {followup.question}")
                    print(f"  Rationale: {followup.rationale}")
                    
                    # Ask and analyze follow-up
                    followup_response = await self.session.ask_persona(
                        persona_id, 
                        followup.question,
                        context=context or self.product_context
                    )
                    
                    followup_analysis = await self.session.analyze_response(
                        persona_id, followup_response, followup.question
                    )

                    print(f"\n{self._get_persona_name(persona_id)}: {followup_response}")
                    
                    result['followup'] = {
                        'question': followup.question,
                        'response': followup_response,
                        'analysis': followup_analysis
                    }
                else:
                    print(f"\n  No follow-up needed for {self._get_persona_name(persona_id)}")
            
            results[persona_id] = result
        
        return results
    
    def _get_persona_name(self, persona_id: str) -> str:
        """Get persona name by ID"""
        persona = next((p for p in self.config.personas if p.id == persona_id), None)
        return persona.name if persona else persona_id
    
    async def _export_session_data(self) -> None:
        """Export all session data including complete conversation flow"""
        print("\n💾 Exporting complete session data...")
        
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        
        # Export memory state (includes all responses and interactions)
        memory_file = data_dir / f"memory_vb_{timestamp}.json"
        memory_state = self.session.memory_manager.memory.export_memory_state()
        
        with open(memory_file, 'w', encoding='utf-8') as f:
            json.dump(memory_state, f, indent=2, ensure_ascii=False, default=str)
        
        # Export complete session state with all answers and analyses
        state_file = data_dir / f"state_vb_{timestamp}.json"
        state_data = {
            "session_metadata": self.session.get_session_metadata(),
            "final_state": self.session.state.model_dump(),
            "product": self.config.product.model_dump(),
            "personas": [p.model_dump() for p in self.config.personas],
            "hypotheses": [h.model_dump() for h in self.config.hypotheses],
            "configuration": {
                "questions": getattr(self.config, 'questions', {}).model_dump() if hasattr(getattr(self.config, 'questions', {}), 'model_dump') else {},
                "phase_config": getattr(self.config, 'phase_config', {}).model_dump() if hasattr(getattr(self.config, 'phase_config', {}), 'model_dump') else {},
                "followup_criteria": getattr(self.config, 'followup_criteria', {}).model_dump() if hasattr(getattr(self.config, 'followup_criteria', {}), 'model_dump') else {},
                "policy": getattr(self.config, 'policy', {})
            }
        }
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, indent=2, ensure_ascii=False, default=str)
        
        # Export detailed conversation flow by phase
        conversation_file = data_dir / f"conversation_flow_{timestamp}.json"
        conversation_data = self._build_conversation_export()
        
        with open(conversation_file, 'w', encoding='utf-8') as f:
            json.dump(conversation_data, f, indent=2, ensure_ascii=False, default=str)
        
        # Export human-readable summary
        summary_file = data_dir / f"session_summary_{timestamp}.md"
        summary_content = self._build_markdown_summary()
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        # Export simple conversation log
        log_file = data_dir / f"conversation_log_{timestamp}.txt"
        log_content = self._build_conversation_log()
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(log_content)
        
        print(f"  ✅ Exported: {memory_file.name}")
        print(f"  ✅ Exported: {state_file.name}")
        print(f"  ✅ Exported: {conversation_file.name}")
        print(f"  ✅ Exported: {summary_file.name}")
        print(f"  ✅ Exported: {log_file.name}")
    
    def _build_conversation_export(self) -> dict:
        """Build detailed conversation flow export"""
        return {
            "session_info": {
                "product": self.config.product.name,
                "start_time": self.start_time.isoformat(),
                "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
                "total_questions": len([a for a in self.session.state.answers]),
                "total_responses": len(self.session.state.answers),
                "total_analyses": len(self.session.state.analyses),
                "total_followups": len(self.session.state.follow_ups)
            },
            "personas": {
                persona.id: {
                    "name": persona.name,
                    "background": persona.background,
                    "responses": [
                        {
                            "question": answer.question,
                            "response": answer.response,
                            "phase": answer.phase.value if hasattr(answer.phase, 'value') else str(answer.phase),
                            "timestamp": answer.timestamp.isoformat() if hasattr(answer, 'timestamp') else None
                        }
                        for answer in self.session.state.get_persona_answers(persona.id)
                    ]
                }
                for persona in self.config.personas
            },
            "phases": {
                phase.value: {
                    "questions": self._get_phase_questions(phase),
                    "responses": [a.model_dump() for a in self.session.state.get_phase_answers(phase)]
                }
                for phase in Phase
            },
            "analyses": [analysis.model_dump() for analysis in self.session.state.analyses],
            "follow_ups": [followup.model_dump() for followup in self.session.state.follow_ups],
            "hypothesis_coverage": self.session.state.hypothesis_coverage,
            "final_coverage_percentage": self.session.state.coverage_percentage()
        }
    
    def _build_markdown_summary(self) -> str:
        """Build human-readable markdown summary"""
        coverage = self.session.state.coverage_percentage()
        
        summary = f"""# Virtual Board Session Summary
        
## Product
**{self.config.product.name}**

{self.config.product.description}

## Session Overview
- **Start Time**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
- **Duration**: {(datetime.now() - self.start_time).total_seconds():.1f} seconds
- **Total Responses**: {len(self.session.state.answers)}
- **Total Analyses**: {len(self.session.state.analyses)}
- **Hypothesis Coverage**: {coverage:.1%}

## Hypotheses
"""
        
        for hypothesis in self.config.hypotheses:
            coverage_pct = self.session.state.hypothesis_coverage.get(hypothesis.id, 0.0)
            summary += f"- **{hypothesis.id}**: {hypothesis.description} ({coverage_pct:.1%} coverage)\n"
        
        summary += "\n## Personas\n"
        for persona in self.config.personas:
            persona_answers = self.session.state.get_persona_answers(persona.id)
            summary += f"\n### {persona.name} ({persona.id})\n"
            summary += f"{persona.background}\n"
            summary += f"**Total Responses**: {len(persona_answers)}\n"
            
            if persona_answers:
                summary += "\n**Key Responses**:\n"
                for answer in persona_answers[:3]:  # Show first 3
                    summary += f"- Q: {answer.question[:80]}...\n"
                    summary += f"  A: {answer.response[:150]}...\n\n"
        
        summary += "\n## Key Themes\n"
        # Add theme information from analyses
        all_themes = []
        for analysis in self.session.state.analyses:
            all_themes.extend(analysis.themes)
        
        # Count theme frequency
        theme_counts = {}
        for theme in all_themes:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        # Sort by frequency
        sorted_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)
        
        for theme, count in sorted_themes[:10]:  # Top 10 themes
            summary += f"- **{theme}**: {count} mentions\n"
        
        summary += "\n## Session Files\n"
        timestamp = self.start_time.strftime('%Y%m%d_%H%M%S')
        summary += f"- `memory_vb_{timestamp}.json` - Complete memory state\n"
        summary += f"- `state_vb_{timestamp}.json` - Session state and configuration\n"
        summary += f"- `conversation_flow_{timestamp}.json` - Detailed conversation flow\n"
        summary += f"- `conversation_log_{timestamp}.txt` - Simple conversation log\n"
        summary += f"- `traces_vb_{timestamp}.json` - Execution traces and metrics\n"

        return summary
    
    def _build_conversation_log(self) -> str:
        """Build simple conversation log with all interactions"""
        log = f"VIRTUAL BOARD CONVERSATION LOG\n"
        log += f"=" * 50 + "\n"
        log += f"Product: {self.config.product.name}\n"
        log += f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        log += f"Duration: {(datetime.now() - self.start_time).total_seconds():.1f}s\n"
        log += f"Total Interactions: {len(self.session.state.answers)}\n"
        log += f"=" * 50 + "\n\n"
        
        # Group answers by question and show all persona responses
        questions_asked = {}
        for answer in self.session.state.answers:
            if answer.question not in questions_asked:
                questions_asked[answer.question] = []
            questions_asked[answer.question].append(answer)
        
        # Sort by phase and timestamp
        phase_order = {"warmup": 1, "diverge": 2, "reflect": 3, "converge": 4, "closure": 5}
        
        for question, answers in questions_asked.items():
            # Sort answers by timestamp
            answers.sort(key=lambda x: x.timestamp)
            first_answer = answers[0]
            phase_name = first_answer.phase.value.upper()
            
            log += f"[{phase_name}] QUESTION:\n"
            log += f"{question}\n"
            log += f"-" * 40 + "\n"
            
            for answer in answers:
                log += f"\n{answer.persona_id.upper()}:\n"
                log += f"{answer.response}\n"
                
                # Find corresponding analysis
                analysis = next((a for a in self.session.state.analyses 
                               if a.persona_id == answer.persona_id and a.question == answer.question), None)
                
                if analysis:
                    log += f"  Themes: {', '.join(analysis.themes) if analysis.themes else 'None'}\n"
                    log += f"  Hypotheses hit: {analysis.hypotheses_hit}\n"
                    log += f"  Sentiment: {analysis.sentiment:+.2f}\n"
            
            log += f"\n" + "=" * 50 + "\n\n"
        
        # Add follow-ups if any
        if self.session.state.follow_ups:
            log += f"FOLLOW-UP QUESTIONS GENERATED:\n"
            log += f"-" * 40 + "\n"
            for followup in self.session.state.follow_ups:
                log += f"\nFor {followup.persona_id}:\n"
                log += f"Q: {followup.question}\n"
                log += f"Rationale: {followup.rationale}\n"
                log += f"Priority: {followup.priority:.2f}\n"
            log += f"\n" + "=" * 50 + "\n\n"
        
        # Add session summary
        coverage = self.session.state.coverage_percentage()
        log += f"SESSION SUMMARY:\n"
        log += f"-" * 40 + "\n"
        log += f"Hypothesis Coverage: {coverage:.1%}\n"
        log += f"Total Responses: {len(self.session.state.answers)}\n"
        log += f"Total Analyses: {len(self.session.state.analyses)}\n"
        log += f"Follow-ups Generated: {len(self.session.state.follow_ups)}\n\n"
        
        # Hypothesis coverage breakdown
        log += f"HYPOTHESIS COVERAGE:\n"
        for hypothesis in self.config.hypotheses:
            coverage_pct = self.session.state.hypothesis_coverage.get(hypothesis.id, 0.0)
            log += f"- {hypothesis.id}: {coverage_pct:.1%} - {hypothesis.description}\n"
        
        log += f"\n" + "=" * 50 + "\n"
        log += f"End of conversation log\n"
        
        return log
    
    def _export_production_metrics(self) -> None:
        """Export production metrics (traces, guardrails, errors)"""
        print("\n📊 Exporting production metrics...")
        
        data_dir = Path("data")
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        
        # Export traces
        traces_file = data_dir / f"traces_vb_{timestamp}.json"
        traces_data = {
            "traces": self.session.tracer.export_traces(),
            "error_count": len(self.session.tracer.get_error_traces()),
            "total_traces": len(self.session.tracer.traces)
        }
        
        with open(traces_file, 'w', encoding='utf-8') as f:
            json.dump(traces_data, f, indent=2, ensure_ascii=False, default=str)
        
        # Export guardrail violations
        if self.session.guardrails.violations:
            violations_file = data_dir / f"violations_vb_{timestamp}.json"
            violations_data = [
                {
                    "type": v.guardrail_type.value,
                    "message": v.message,
                    "severity": v.severity,
                    "timestamp": v.timestamp.isoformat(),
                    "context": v.context
                }
                for v in self.session.guardrails.violations
            ]
            
            with open(violations_file, 'w', encoding='utf-8') as f:
                json.dump(violations_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"  ⚠️ {len(violations_data)} guardrail violations logged")
        
        # Export error summary
        if self.session.error_handler.error_counts:
            errors_file = data_dir / f"errors_vb_{timestamp}.json"

            with open(errors_file, 'w', encoding='utf-8') as f:
                json.dump(self.session.error_handler.error_counts, f, indent=2, default=str)
            
            print(f"  ❌ {sum(self.session.error_handler.error_counts.values())} errors handled")
        
        print(f"  ✅ Exported: {traces_file.name}")
    
    def _generate_report(self) -> SessionReport:
        """Generate final session report"""
        end_time = datetime.now()
        
        # Get memory insights
        memory_state = self.session.memory_manager.memory.export_memory_state()
        
        # Extract key insights
        key_insights = []
        
        # Add consensus themes
        consensus_themes = memory_state.get("consensus_themes", [])
        if consensus_themes:
            key_insights.append(f"Consensus themes: {', '.join(consensus_themes)}")
        
        # Add coverage insight
        coverage = self.session.state.coverage_percentage()
        key_insights.append(f"Hypothesis coverage: {coverage:.0%}")
        
        # Add sentiment summary
        avg_sentiment = self._calculate_average_sentiment()
        if avg_sentiment is not None:
            sentiment_desc = "positive" if avg_sentiment > 0.3 else "negative" if avg_sentiment < -0.3 else "mixed"
            key_insights.append(f"Overall sentiment: {sentiment_desc} ({avg_sentiment:+.2f})")
        
        # Generate recommendations
        recommendations = []
        
        if coverage < 0.6:
            recommendations.append("Low hypothesis coverage - consider additional research")
        
        if avg_sentiment and avg_sentiment > 0.5:
            recommendations.append("Strong positive response - proceed with development")
        elif avg_sentiment and avg_sentiment < -0.2:
            recommendations.append("Significant concerns raised - address before proceeding")
        
        # Add production insights
        error_count = len(self.session.tracer.get_error_traces())
        if error_count > 0:
            recommendations.append(f"Session had {error_count} errors - review traces for improvements")
        
        return SessionReport(
            start_time=self.start_time,
            end_time=end_time,
            product_name=self.config.product.name,
            hypotheses_tested=self.config.get_hypothesis_ids(),
            coverage_achieved=coverage,
            key_insights=key_insights,
            recommendations=recommendations,
            raw_data={
                "memory_state": memory_state,
                "production_metrics": {
                    "total_traces": len(self.session.tracer.traces),
                    "error_traces": error_count,
                    "guardrail_violations": len(self.session.guardrails.violations)
                }
            }
        )
    
    def _calculate_average_sentiment(self) -> Optional[float]:
        """Calculate average sentiment across all analyses"""
        sentiments = [a.sentiment for a in self.session.state.analyses]
        return sum(sentiments) / len(sentiments) if sentiments else None