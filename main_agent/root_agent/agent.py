import random

from google.adk.agents.llm_agent import Agent
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.tools.example_tool import ExampleTool
from google.adk.tools import ToolContext
from google.genai import types

print("-" * 10)
print(AGENT_CARD_WELL_KNOWN_PATH)
print("-" * 10)


# --- Roll Die Sub-Agent ---
def roll_two_dices(sides: int) -> int:
  """Roll a die and return the rolled result."""
  return [random.randint(1, 6), random.randint(1, 6)]


roll_agent = Agent(
    name="roll_agent",
    description="Handles rolling two dices of six sizes.",
    instruction="""
      You are responsible for rolling two dices based on the user's request.
      When asked to roll a dies, you must call the roll_two_dices tool and get two dices numbers.
    """,
    tools=[roll_two_dices],
    generate_content_config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(  # avoid false alarm about rolling dice.
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.OFF,
            ),
        ]
    ),
)


# --- State management tools ---
def store_dice_numbers(numbers: list[int], tool_context: ToolContext) -> str:
    """Store the rolled dice numbers into session state.

    Call this tool every time after rolling dice to persist the numbers.

    Args:
        numbers: A list of integers representing the dice numbers just rolled.

    Returns:
        A confirmation message with all stored numbers.
    """
    existing = tool_context.state.get("dice_numbers", [])
    existing.extend(numbers)
    tool_context.state["dice_numbers"] = existing
    return f"Stored. All dice numbers so far: {existing}"


def get_all_dice_numbers(tool_context: ToolContext) -> list[int]:
    """Retrieve all stored dice numbers from session state.

    Call this tool when the user asks to check luck, so you can pass all
    accumulated numbers to the check_winning_agent.

    Returns:
        A list of all stored dice numbers.
    """
    return tool_context.state.get("dice_numbers", [])


def start_game(tool_context: ToolContext) -> str:
    """Reset the game by clearing all stored dice numbers and session history.

    Call this tool when the user says "start the game".
    It clears all accumulated dice numbers from state and removes all
    previous conversation events so the game starts fresh.

    Returns:
        A confirmation that the game has been reset.
    """
    # Clear stored dice numbers
    tool_context.state["dice_numbers"] = []

    # Clear all previous conversation events (history)
    tool_context.session.events.clear()

    return "Game reset! All previous dice numbers and history have been cleared. Ready to roll!"


example_tool = ExampleTool([
    {
        "input": {
            "role": "user",
            "parts": [{"text": "Start the game"}],
        },
        "output": [
            {"role": "model", "parts": [{"text": "I'll reset everything and start a fresh game!"}]}
        ],
    },
    {
        "input": {
            "role": "user",
            "parts": [{"text": "Roll a two 6-sided die."}],
        },
        "output": [
            {"role": "model", "parts": [{"text": "I rolled dices 4 and 5 for you. Let me store them."}]}
        ],
    },
    {
        "input": {
            "role": "user",
            "parts": [{"text": "Roll again"}],
        },
        "output": [
            {"role": "model", "parts": [{"text": "I rolled dices 2 and 6 for you. Let me store them. All stored numbers so far: [4, 5, 2, 6]"}]}
        ],
    },
    {
        "input": {
            "role": "user",
            "parts": [{"text": "Check my luck"}],
        },
        "output": [
            {
                "role": "model",
                "parts": [{"text": "I have stored numbers [4, 5, 2, 6]. I will pass all of them to check_winning_agent."}],
            }
        ],
    },
])

check_winning_agent = RemoteA2aAgent(
    name="check_winning_agent",
    description="Agent that handles checking if numbers make you winner, looser or tell probability of winning",
    agent_card=(
        f"http://localhost:8001/a2a/check_winning_agent{AGENT_CARD_WELL_KNOWN_PATH}"
    ),
)


root_agent = Agent(
    model="gemini-2.5-flash",
    name="root_agent",
    instruction="""
      You are a helpful assistant that rolls two dice at a time and accumulates the results across turns.

      IMPORTANT WORKFLOW:
      1. When the user asks "start the game":
         a. Call the start_game tool to clear all stored dice numbers and conversation history.
         b. Confirm to the user that the game has been reset and they can start rolling.

      2. When the user asks to "roll dices" (or "roll again"):
         a. Delegate to roll_agent to get two dice numbers.
         b. ALWAYS call the store_dice_numbers tool after receiving those two numbers.
         c. Report the rolled numbers to the user.

      3. When the user asks to "check my luck":
         a. First call get_all_dice_numbers to retrieve ALL stored numbers from state.
         b. Delegate to check_winning_agent and pass ALL the stored numbers.
         c. Report the result to the user.

      You MUST call store_dice_numbers after every roll so that numbers accumulate.
      You MUST call get_all_dice_numbers before delegating to check_winning_agent.
      You MUST call start_game when the user says "start the game" to reset everything.
    """,
    global_instruction=(
        "You are DicePrimeBot, ready to roll dice and check luck."
    ),
    sub_agents=[roll_agent, check_winning_agent],
    tools=[example_tool, store_dice_numbers, get_all_dice_numbers, start_game],
    generate_content_config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(  # avoid false alarm about rolling dice.
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.OFF,
            ),
        ]
    ),
)

