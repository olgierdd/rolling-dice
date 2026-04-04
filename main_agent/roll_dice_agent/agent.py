
import random
from ast import List

from google.adk.agents.llm_agent import Agent
from google.genai import types


def roll_dice() -> int:
  """Roll a six-sided die and return a value from 1 to 6."""
  return random.randint(1, 6)


root_agent = Agent(
    model='gemini-2.5-flash',
    name='roll_dice_agent',
    description='Remote A2A dice agent that rolls two six-sided dies.',
    instruction="""
      You roll two six-sided dies.
      For every roll request, call the roll_dice tool.
      The returned values must always be between 1 and 6.
    """,
    tools=[roll_dice],
    generate_content_config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.OFF,
            ),
        ]
    ),
)

