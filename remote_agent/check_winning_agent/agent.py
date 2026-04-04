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

from google.adk.agents.llm_agent import Agent
from google.genai import types

TARGET = 21
def winning_probability(goal: int) -> float:
    """
    Calculate the probability of winning when throwing two dice.

    A player wins if the sum of two dice is below the target number.
    Each die has numbers from 1 to 6.

    Args:
        goal: The target number. Player wins if sum < goal.

    Returns:
        The probability of winning (between 0 and 1).

    Example:
        >>> winning_probability(10)
        0.75  # 27 winning combinations out of 36 total
    """
    winning_combinations = 0
    total_combinations = 0

    # Iterate through all possible combinations of two dice
    for die1 in range(1, 7):
        for die2 in range(1, 7):
            total_combinations += 1
            dice_sum = die1 + die2
            # Player wins if sum is below the goal
            if dice_sum < goal:
                winning_combinations += 1

    # Calculate probability
    if winning_combinations > 0:
        return winning_combinations / total_combinations
    else:
        return 0


async def check_wining(dices: list[int]) -> str:
    total = sum(dices)
    print("check luck")
    for dice in dices:
        print(dice)
    if total > TARGET:
        return f"Looser, total is: {total}"
    if total == TARGET:
        return "Winer"

    probability = winning_probability(TARGET - total)
    return f"The winning probability is {probability*100:.0f}%, total is: {total}"


root_agent = Agent(
    model='gemini-2.5-flash',
    name='check_winning_agent',
    description='check winning agent that can tell if the current list of dice numbers make you winner, looser or tell probability of winning',
    instruction="""
      You check whether for sequence of dices numbers you are winner, looser or tell you the probability of winning.
      When checking, call the check_wining tool with a list of integers for dices. Be sure to pass in a list of integers. You should never pass in a string.
      You should not rely on the previous history on numbers.
    """,
    tools=[
        check_wining,
    ],
    # Disallow transfers as it uses output_schema
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    generate_content_config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(  # avoid false alarm about rolling dice.
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.OFF,
            ),
        ]
    ),
)
