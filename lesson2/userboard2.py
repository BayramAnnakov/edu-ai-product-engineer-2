from dotenv import load_dotenv

load_dotenv()

import asyncio
from agents import Agent, Runner

# Define the product idea and hypotheses (taken from the initial transcript)
product_idea = """
Schengen 90/180 Calculator App:
- Product Idea: A mobile app to automatically track Schengen visa days,
  including support for multiple passports and maintaining historical data.
- Hypotheses to test:
    1. Users struggle with manually tracking Schengen days.
    2. Users are willing to pay for an enhanced, automated tracking solution.
"""

# Define the questions that the facilitator should ask (as in the transcript)
# These are taken from the transcript "Schengen App Pre-Test Simulation"
facilitator_questions = [
    "What are your initial thoughts on the idea of a Schengen 90/180 Calculator App?",
    "How do you currently handle the tracking of your Schengen days?",
    "What features would you find most valuable in an automated solution? For example, support for multiple passports or historical data?",
    "Would you be willing to pay for a premium version that offers these advanced tracking features? Why or why not?"
]

# Create the facilitator agent with instructions to lead and validate the product idea discussion.
facilitator_agent = Agent(
    name="Facilitator",
    instructions=(
        "You are a facilitator leading a virtual board meeting to validate a new product idea. "
        "You will introduce the product idea and ask a series of questions exactly as specified. "
        "Ensure to prompt the customer personas for their honest and detailed opinions, without predefining their answers."
    )
)

# Create customer persona agents with instructions tailored to their background.
julia = Agent(
    name="Julia",
    instructions=(
        "You are a 29-year-old freelance designer who frequently travels between Spain and Germany. "
        "Manual tracking of your Schengen days is challenging and frustrating. Provide candid, creative feedback while staying in character."
    )
)

raj = Agent(
    name="Raj",
    instructions=(
        "You are a 35-year-old software developer and digital nomad based mostly in Lisbon. "
        "You appreciate automation that removes repetitive tasks. Offer detailed and thoughtful insights on the product idea."
    )
)

chloe = Agent(
    name="Chloe",
    instructions=(
        "You are a 27-year-old content creator who travels extensively across EU countries. "
        "Manual tracking of travel days is tedious for you, and you seek solutions that simplify this process. "
        "Share honest opinions on the product idea and suggest features that would delight you."
    )
)

# List of customer agents
customer_agents = [julia, raj, chloe]

async def main():
    print("=== Virtual User Board Simulation ===\n")
    
    # Facilitator introduces the product idea
    facilitator_intro = (
        f"Introducing product idea:\n{product_idea}\n"
        "Let's begin our discussion."
    )
    fac_result = await Runner.run(facilitator_agent, facilitator_intro)
    print("Facilitator Intro:", fac_result.final_output, "\n")
    
    # For each question from the transcript, have the facilitator ask the question and each persona respond.
    for idx, question in enumerate(facilitator_questions, start=1):
        # Facilitator asks the question
        fac_question_prompt = f"Question {idx}: {question}"
        fac_question_result = await Runner.run(facilitator_agent, fac_question_prompt)
        print("Facilitator asks:", fac_question_result.final_output, "\n")
        
        # Each customer agent responds creatively based on the question context and the product idea.
        print(f"----- Responses for Question {idx} -----\n")
        for agent in customer_agents:
            prompt = f"{product_idea}\nQuestion: {question}\nAs {agent.name}, please share your thoughts."
            result = await Runner.run(agent, prompt)
            print(f"{agent.name}:", result.final_output, "\n")
    
    # Facilitator summarizes the discussion based on all the feedback.
    summary_prompt = (
        "Based on the discussion, please summarize the key takeaways regarding the need for an automated "
        "Schengen days tracking app and the value of features like multiple passport support and historical data management."
    )
    fac_summary_result = await Runner.run(facilitator_agent, summary_prompt)
    print("Facilitator Summary:", fac_summary_result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
