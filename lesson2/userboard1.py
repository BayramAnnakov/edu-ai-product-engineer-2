from dotenv import load_dotenv

load_dotenv()

import asyncio
from agents import Agent, Runner

# Define the product idea and hypotheses
product_idea = """
Schengen 90/180 Calculator App:
- Product Idea: A mobile app to automatically track Schengen visa days,
  including support for multiple passports and maintaining historical data.
- Hypotheses to test:
    1. Users struggle with manually tracking Schengen days.
    2. Users are willing to pay for an enhanced, automated tracking solution.
"""

# Create the facilitator agent with instructions to lead and validate the product idea discussion.
facilitator_agent = Agent(
    name="Facilitator",
    instructions=(
        "You are a facilitator leading a virtual board meeting to validate new product ideas. "
        "Introduce the product idea, request feedback from customer personas, and provide a neutral summary "
        "of the discussion."
    )
)

# Create customer persona agents with instructions tailored to their background.
julia = Agent(
    name="Julia",
    instructions=(
        "You are a 29-year-old freelance designer who frequently travels between Spain and Germany. "
        "You often struggle with manually tracking your Schengen days. Provide honest feedback on the product idea."
    )
)

raj = Agent(
    name="Raj",
    instructions=(
        "You are a 35-year-old software developer and digital nomad based mostly in Lisbon. "
        "You value automated solutions that reduce repetitive tasks. Offer detailed feedback on the product idea."
    )
)

chloe = Agent(
    name="Chloe",
    instructions=(
        "You are a 27-year-old content creator who travels extensively across EU countries. "
        "Manual tracking of Schengen days is tedious for you. Share your perspective on the product idea and mention desired features."
    )
)

# List of customer agents
customer_agents = [julia, raj, chloe]


async def main():
    print("=== Virtual User Board Simulation ===\n")
    
    # Facilitator introduces the product idea and asks for initial feedback.
    facilitator_intro = (
        f"Introducing product idea:\n{product_idea}\n"
        "Please share your initial impressions on this idea."
    )
    fac_result = await Runner.run(facilitator_agent, facilitator_intro)
    print("Facilitator Intro:", fac_result.final_output, "\n")
    
    # Initial feedback round: each customer persona responds based on the product idea.
    print("----- Initial Feedback -----\n")
    for agent in customer_agents:
        # Construct a prompt that includes the product idea and instructs the agent to respond in character.
        prompt = f"{product_idea}\nAs {agent.name}, please share your thoughts."
        result = await Runner.run(agent, prompt)
        print(f"{agent.name}:", result.final_output, "\n")
    
    # Facilitator follow-up: ask probing questions to validate key hypotheses.
    follow_up_prompt = (
        "Thank you for your feedback. To further validate our hypotheses, please answer the following: "
        "Do you often struggle with manually tracking Schengen days? Would you consider paying for an app that automates this process "
        "and offers advanced features such as support for multiple passports and historical data tracking? Please elaborate."
    )
    fac_result_followup = await Runner.run(facilitator_agent, follow_up_prompt)
    print("Facilitator Follow-up:", fac_result_followup.final_output, "\n")
    
    # Follow-up round: each customer persona gives additional details.
    print("----- Follow-up Feedback -----\n")
    for agent in customer_agents:
        prompt = f"{follow_up_prompt}\nAs {agent.name}, please provide additional details."
        result = await Runner.run(agent, prompt)
        print(f"{agent.name} (follow-up):", result.final_output, "\n")
    
    # Facilitator summarizes the discussion.
    summary_prompt = (
        "Based on the feedback received from the customer personas, it appears that there is a consistent need for an "
        "automated solution to track Schengen days. Features such as multiple passport support and historical data "
        "management are particularly valued. This feedback will be instrumental in refining the product idea further."
    )
    fac_result_summary = await Runner.run(facilitator_agent, summary_prompt)
    print("Facilitator Summary:", fac_result_summary.final_output)

if __name__ == "__main__":
    asyncio.run(main())
