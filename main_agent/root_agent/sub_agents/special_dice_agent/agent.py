import os
from typing import Any

from dotenv import load_dotenv
import random
from google.adk.tools import ToolContext
from google.adk.agents.llm_agent import Agent
from google.genai import types

load_dotenv()
model = os.getenv("OPENAI_MODEL_NAME", "?")

def special_dice_roll(tool_context: ToolContext) -> dict[str, list[int]]:
  """Roll a biased six-sided die that favors 4, 5, and 6."""
  sides = [1, 2, 3, 4, 5, 6]
  weights = [1, 1, 1, 2, 3, 5]

  # Roll two dice
  dice1:int = random.choices(sides, weights=weights, k=1)[0]
  dice2:int = random.choices(sides, weights=weights, k=1)[0]
  rolled = [dice1, dice2]

  # Automatically store in session state
  existing = tool_context.state.get("dice_numbers", [])
  existing.extend(rolled)
  tool_context.state["dice_numbers"] = existing

  return {
      "rolled": rolled,
      "all_numbers": existing
  }


special_dice_agent = Agent(
    model=model,
    name='special_dice_agent',
    description='Remote A2A dice agent that rolls six-sided dies.',
    instruction="""
      You roll six-sided dies.
      For every roll request, call the special_dice_roll tool.
      The returned values must always be between 1 and 6.
    """,
    tools=[special_dice_roll],
    generate_content_config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.OFF,
            ),
        ]
    ),
)
