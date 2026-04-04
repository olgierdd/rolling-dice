# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import random

from google.adk.agents.llm_agent import Agent
from google.genai import types


def roll_dice() -> int:
  """Roll a six-sided die and return a value from 1 to 6."""
  return random.randint(1, 6)


root_agent = Agent(
    model='gemini-2.5-flash',
    name='roll_dice_agent',
    description='Remote A2A dice agent that rolls a six-sided die.',
    instruction="""
      You roll a six-sided die.
      For every roll request, call the roll_dice tool.
      The returned value must always be between 1 and 6.
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

