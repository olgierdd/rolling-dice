import os
from typing import Any

from dotenv import load_dotenv
import random
from google.adk.tools import ToolContext
from google.adk.agents.llm_agent import Agent
from google.genai import types

load_dotenv()
model = os.getenv("OPENAI_MODEL_NAME", "?")

def special_dice_roll(tool_context: ToolContext, roll_type: str = "hard") -> dict[str, list[int]]:
  """Roll a biased six-sided die.

  Args:
    roll_type: Type of roll - "soft" (favors 1, 2, 3) or "hard" (favors 4, 5, 6).
              Defaults to "hard".
  """
  sides = [1, 2, 3, 4, 5, 6]

  # Choose weights based on roll type
  if roll_type.lower() == "soft":
    weights = [6, 5, 1, 1, 1, 1]
  else:  # default to "hard"
    weights = [1, 1, 1, 1, 4, 5]

  # Roll two dice
  dice1: int = random.choices(sides, weights=weights, k=1)[0]
  dice2: int = random.choices(sides, weights=weights, k=1)[0]
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
      You can specify roll_type as either 'soft' (favors 1, 2, 3) or 'hard' (favors 4, 5, 6).
      If the user doesn't specify, default to 'hard'.
      The returned values must always be between 1 and 6.
      Always respond in the language used in the user’s request.
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
