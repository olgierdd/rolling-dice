import os
import logging
from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from google.adk.tools import ToolContext
from google.genai import types

load_dotenv()
model = os.getenv("OPENAI_MODEL_NAME", "?")

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

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
            # Player wins if sum is below or equal the goal
            if dice_sum <= goal:
                winning_combinations += 1

    # Calculate probability
    if winning_combinations > 0:
        return winning_combinations / total_combinations
    else:
        return 0


def _caller_metadata(tool_context: ToolContext | None) -> dict[str, str]:
    """Extract caller identifiers from ADK tool context for logging."""
    if tool_context is None:
        return {
            "agent_name": "unknown",
            "user_id": "unknown",
            "session_id": "unknown",
            "app_name": "unknown",
            "invocation_id": "unknown",
        }

    session = getattr(tool_context, "session", None)
    session_id = getattr(session, "id", None) or getattr(session, "session_id", None)
    app_name = getattr(session, "app_name", None)

    return {
        "agent_name": str(getattr(tool_context, "agent_name", None) or "unknown"),
        "user_id": str(getattr(tool_context, "user_id", None) or "unknown"),
        "session_id": str(session_id or "unknown"),
        "app_name": str(app_name or "unknown"),
        "invocation_id": str(getattr(tool_context, "invocation_id", None) or "unknown"),
    }


async def check_wining(tool_context: ToolContext, dices: list[int]) -> dict[str, str | int]:
    total = sum(dices)
    caller = _caller_metadata(tool_context)
    logger.info(
        "check_wining request caller_agent=%s user_id=%s session_id=%s app_name=%s invocation_id=%s dices=%s total=%s",
        caller["agent_name"],
        caller["user_id"],
        caller["session_id"],
        caller["app_name"],
        caller["invocation_id"],
        dices,
        total,
    )

    if total > TARGET:
        logger.info("check_wining result status=Loser total=%s target=%s", total, TARGET)
        return {
            "Status": "Loser",
            "Total" : total,
            "Target" : TARGET
        }
    if total == TARGET:
        logger.info("check_wining result status=Winer total=%s target=%s", total, TARGET)
        return {
            "Status": "Winer",
            "Total" : total,
            "Target": TARGET
        }

    probability = winning_probability(TARGET - total)
    logger.info(
        "check_wining result status=Can be winer total=%s target=%s probability=%s",
        total,
        TARGET,
        f"{probability*100:.1f}%",
    )
    return {
        "Status": "Can be winer",
        "Probability": f"{probability*100:.1f}%",
        "Total": total,
        "Target": TARGET
    }


root_agent = Agent(
    model=model,
    name='check_winning_agent',
    description='Agent that handles check your luck if numbers make you winner, loser or tell probability of winning',
    instruction="""
Evaluate the provided dice sequence and determine whether the player is a loser, a winner, or still has a chance to win (with probability).
For every check, call `check_wining` and pass `dices` as a list of integers only (for example: [2, 5, 6]). Never pass a string.
Treat each request as independent and ignore any dice values from previous messages.
Respond in the same language as the user.
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
