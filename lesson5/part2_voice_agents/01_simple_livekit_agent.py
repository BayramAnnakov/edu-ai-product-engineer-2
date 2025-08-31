"""
Simple LiveKit Voice Agent with OpenAI Realtime API.

Uses OpenAI's Realtime API (gpt-4o-realtime) for low-latency voice interactions.
Based on LiveKit's latest Agent pattern.
"""

from dotenv import load_dotenv
load_dotenv()

from typing import Annotated
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import openai, noise_cancellation
from livekit.agents.llm import function_tool


class PMAssistant(Agent):
    """Product Manager Assistant Agent"""
    
    def __init__(self) -> None:
        super().__init__(
            instructions="""
            You are a helpful Product Manager assistant. You can help with:
            - Sprint planning and retrospectives
            - Product metrics analysis
            - Feature prioritization
            - User story creation
            
            Be concise and data-driven in your responses.
            """
        )
    
    @function_tool()
    async def create_user_story(
        self,
        feature: Annotated[str, "The feature to implement"],
        user_type: Annotated[str, "The type of user"],
        benefit: Annotated[str, "The benefit to the user"]
    ) -> str:
        """Create a formatted user story"""
        
        story = f"""
User Story Created:

As a {user_type},
I want {feature},
So that {benefit}.

Acceptance Criteria:
1. Feature is accessible to {user_type}
2. {benefit} is achieved
3. Performance metrics are tracked

This story has been added to your backlog.
"""
        return story
    
    @function_tool()
    async def analyze_sprint_velocity(
        self,
        completed_points: Annotated[int, "Story points completed"],
        planned_points: Annotated[int, "Story points planned"]
    ) -> str:
        """Analyze sprint performance"""
        
        velocity_percentage = (completed_points / planned_points * 100) if planned_points > 0 else 0
        
        analysis = f"""
Sprint Velocity Analysis:

Planned: {planned_points} points
Completed: {completed_points} points
Velocity: {velocity_percentage:.1f}%

"""
        
        if velocity_percentage >= 90:
            analysis += "Excellent sprint performance! The team is delivering as planned."
        elif velocity_percentage >= 70:
            analysis += "Good sprint performance. Consider if any blockers affected completion."
        else:
            analysis += "Sprint velocity is below target. Review estimation accuracy and identify blockers."
        
        return analysis


async def entrypoint(ctx: agents.JobContext):
    """Entry point for the voice agent"""
    
    # Create the PM assistant agent
    assistant = PMAssistant()
    
    # Create session with OpenAI Realtime model
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            voice="coral"  
        ),
    )
    
    
    
    # Start the session
    await session.start(
        room=ctx.room,
        agent=assistant,
        room_input_options=RoomInputOptions(
            # Use noise cancellation for better audio quality
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
    
    # Generate initial greeting
    await session.generate_reply(
        instructions="Greet the user and introduce yourself as their Product Management assistant. Briefly mention what you can help with. Speak in English."
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))