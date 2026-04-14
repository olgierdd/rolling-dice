import logging
import random
import os
import sys
import certifi
import truststore
from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.tools import ToolContext, ExampleTool
from google.adk.tools.example_tool import Example
from google.genai import types
from .sub_agents.special_dice_agent.agent import special_dice_agent

load_dotenv()
model = os.getenv("OPENAI_MODEL_NAME", "?")
logger = logging.getLogger(__name__)

def _configure_remote_agent_tls() -> None:
    """Set a trusted CA bundle path for outgoing HTTPS calls to remote agents."""
    custom_ca_bundle = os.getenv("REMOTE_AGENT_CA_BUNDLE")
    if custom_ca_bundle:
        os.environ["SSL_CERT_FILE"] = custom_ca_bundle
        os.environ["REQUESTS_CA_BUNDLE"] = custom_ca_bundle
        os.environ["CURL_CA_BUNDLE"] = custom_ca_bundle
        logger.info("Using custom CA bundle for remote agent TLS: %s", custom_ca_bundle)
        return

    # Prefer the OS trust store (works better on Windows than OpenSSL defaults).
    truststore.inject_into_ssl()
    logger.info("Using system trust store for remote agent TLS verification.")

    # Keep CA bundle variables populated for libraries that read env vars directly.
    default_ca_bundle = certifi.where()
    os.environ.setdefault("SSL_CERT_FILE", default_ca_bundle)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", default_ca_bundle)
    os.environ.setdefault("CURL_CA_BUNDLE", default_ca_bundle)


REMOTE_AGENT_HOST = os.getenv("REMOTE_AGENT_HOST", "https://mystairdesign.com").rstrip("/")
CHECK_WINNING_AGENT_CARD_URL = (
    f"{REMOTE_AGENT_HOST}/a2a/check_winning_agent{AGENT_CARD_WELL_KNOWN_PATH}"
)

_configure_remote_agent_tls()

# --- Roll Die Tool with automatic storage ---
def roll_two_dices_and_store(tool_context: ToolContext) -> dict:
  """Roll two six-sided dice and automatically store the results.

  This tool rolls two dice, stores the numbers in session state,
  and returns both the rolled numbers and all accumulated numbers.

  Returns:
      A dict with 'rolled' (the two new numbers) and 'all_numbers' (all stored numbers).
  """
  # Roll two dice
  dice1 = random.randint(1, 6)
  dice2 = random.randint(1, 6)
  rolled = [dice1, dice2]

  # Automatically store in session state
  existing = tool_context.state.get("dice_numbers", [])
  existing.extend(rolled)
  tool_context.state["dice_numbers"] = existing

  return {
      "rolled": rolled,
      "all_numbers": existing
  }


# --- State management tools ---

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


example_tool: ExampleTool = ExampleTool([
    Example(
        input=types.Content(role="user", parts=[types.Part(text="Start the game")]),
        output=[types.Content(role="model", parts=[types.Part(text="I'll reset everything and start a fresh game!")])],
    ),
    Example(
        input=types.Content(role="user", parts=[types.Part(text="Roll a two 6-sided die.")]),
        output=[types.Content(role="model", parts=[types.Part(text="I rolled dices 4 and 5 for you. Let me store them.")])],
    ),
    Example(
        input=types.Content(role="user", parts=[types.Part(text="Roll again")]),
        output=[types.Content(role="model", parts=[types.Part(text="I rolled dices 2 and 6 for you. Let me store them. All stored numbers so far: [4, 5, 2, 6]")])],
    ),
])

check_winning_agent = RemoteA2aAgent(
    name="check_winning_agent",
    description="Agent that handles check your luck if numbers make you winner, loser or tell probability of winning",
    agent_card=CHECK_WINNING_AGENT_CARD_URL,
)
logger.info("** Operating Sustem: %s", sys.platform)
logger.info("** Winning Agent URL: %s", CHECK_WINNING_AGENT_CARD_URL)

root_agent = Agent(
    model=model,
    name="root_agent",
    instruction="""
      You are a helpful assistant that rolls two dice at a time and accumulates the results across turns.

      IMPORTANT WORKFLOW:
      1. When the user asks "start the game" or "play again":
         a. Call the start_game tool to clear all stored dice numbers and conversation history.
         b. Confirm to the user that the game has been reset and they can start rolling.

      2. When the user asks to "roll dices" or "roll again":
         a. Call the roll_two_dices_and_store tool - this will automatically roll AND store the numbers.
         b. Report the rolled numbers to the user.
         
      3. Wen the user asks to "special dice roll" or "roll dice hard" or "roll dice soft":
         a. Call the special_dice_agent - this will automatically roll AND store the numbers. Pass roll_type as soft or hard.
         b. Report the rolled numbers to the user.

      4. When the user asks to "check my luck" or "am I lucky":
         a. First call get_all_dice_numbers tool to retrieve ALL stored numbers from state.
         b. After getting the numbers, you MUST make a function call to transfer_to_agent with agent_name="check_winning_agent".
            Include all the dice numbers in your message parameter so check_winning_agent knows what numbers to check.
            DO NOT just say "transfer" in text - you must actually invoke the transfer_to_agent function!
         c. Report the result to the user.
         
      5. When the user asks "should I play" or "should I roll":
         a. First call get_all_dice_numbers tool to retrieve ALL stored numbers from state.
         b. After getting the numbers, you MUST make a function call to transfer_to_agent with agent_name="check_winning_agent".
            Include all the dice numbers in your message parameter so check_winning_agent knows what numbers to check.
            DO NOT just say "transfer" in text - you must actually invoke the transfer_to_agent function!
         c. If Target - Total is less than 4, advise the user to stop playing as it is too risky.

      CRITICAL RULES:
      - When checking luck, you MUST actually CALL the transfer_to_agent function, not just mention it in text.
      - Never say "Transfer to check_winning_agent" as text output - instead make the actual function call.
      - You MUST call start_game when the user says "start the game" to reset everything.
      
      SUB-AGENTS:
      - check_winning_agent: Checks if dice numbers make you a winner, loser, or calculates winning probability.
        ALWAYS invoke via transfer_to_agent(agent_name="check_winning_agent", message="Check these dice numbers: [...]")
    """,
    global_instruction=(
        "You are Dice Bot, ready to roll dice and check luck."
    ),
    sub_agents=[check_winning_agent, special_dice_agent],
    tools=[example_tool, roll_two_dices_and_store, get_all_dice_numbers, start_game],
    generate_content_config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(  # avoid false alarm about rolling dice.
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.OFF,
            ),
        ]
    ),
)

