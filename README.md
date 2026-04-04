# rolling-dice

# A2A Basic Sample Agent

This sample demonstrates the **Agent-to-Agent (A2A)** architecture in the Agent Development Kit (ADK), showcasing how multiple agents can work together to handle complex tasks. The sample implements an agent that can roll dice and check if numbers are prime.

## Overview

The A2A Basic sample consists of:

- **Root Agent** (`root_agent`): The main orchestrator that delegates tasks to specialized sub-agents
- **Roll Agent** (`roll_agent`): A local sub-agent that handles dice rolling operations
- **Prime Agent** (`prime_agent`): A remote A2A agent that checks if numbers are prime, this agent is running on a separate A2A server

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌────────────────────┐
│   Root Agent    │───▶│   Roll Agent     │    │   Remote Prime     │
│  (Local)        │    │   (Local)        │    │   Agent            │
│                 │    │                  │    │  (localhost:8001)  │
│                 │───▶│                  │◀───│                    │
└─────────────────┘    └──────────────────┘    └────────────────────┘
```

## Key Features

### 1. **Local Sub-Agent Integration**
- The `roll_agent` demonstrates how to create and integrate local sub-agents
- Handles dice rolling with configurable number of sides
- Uses a simple function tool (`roll_die`) for random number generation

### 2. **Remote A2A Agent Integration**
- The `prime_agent` shows how to connect to remote agent services
- Communicates with a separate service via HTTP at `http://localhost:8001/a2a/check_prime_agent`
- Demonstrates cross-service agent communication

### 3. **Agent Orchestration**
- The root agent intelligently delegates tasks based on user requests
- Can chain operations (e.g., "roll a die and check if it's prime")
- Provides clear workflow coordination between multiple agents

### 4. **Example Tool Integration**
- Includes an `ExampleTool` with sample interactions for context
- Helps the agent understand expected behavior patterns

## Setup and Usage

### Prerequisites
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp dot_env main_agent/.env
cp dot_env remote_agent/.env
# configure LLM key
```

1. **Start the Remote Prime Agent server**:
   ```bash
   # Start the remote a2a server that serves the check prime agent on port 8001
   adk api_server --a2a --port 8001 remote_agent
   ```

2. **Run the Main Agent**:
   ```bash
   # In a separate terminal, run the adk web server
   adk web main_agent --port 8002
   ```

### Example Interactions

curl -sS http://localhost:8002/list-apps | cat
curl -sS http://localhost:8001/a2a/check_prime_agent/.well-known/agent-card.json | python -m json.tool

Once both services are running, you can interact with the root agent:

**Simple Dice Rolling:**
```
User: Roll a 6-sided die
Bot: I rolled a 4 for you.
```

**Prime Number Checking:**
```
User: Is 7 a prime number?
Bot: Yes, 7 is a prime number.
```

**Combined Operations:**
```
User: Roll a 10-sided die and check if it's prime
Bot: I rolled an 8 for you.
Bot: 8 is not a prime number.
```

## Code Structure

### Main Agent (`agent.py`)

- **`roll_die(sides: int)`**: Function tool for rolling dice
- **`roll_agent`**: Local agent specialized in dice rolling
- **`prime_agent`**: Remote A2A agent configuration
- **`root_agent`**: Main orchestrator with delegation logic

### Remote Prime Agent (`remote_a2a/check_prime_agent/`)

- **`agent.py`**: Implementation of the prime checking service
- **`agent.json`**: Agent card of the A2A agent
- **`check_prime(nums: list[int])`**: Prime number checking algorithm


## Extending the Sample

You can extend this sample by:

- Adding more mathematical operations (factorization, square roots, etc.)
- Creating additional remote agent
- Implementing more complex delegation logic
- Adding persistent state management
- Integrating with external APIs or databases

## Deployment to Other Environments

When deploying the remote A2A agent to different environments (e.g., Cloud Run, different hosts/ports), you **must** update the `url` field in the agent card JSON file:

### Local Development
```json
{
  "url": "http://localhost:8001/a2a/check_prime_agent",
  ...
}
```

### Cloud Run Example
```json
{
  "url": "https://your-service-abc123-uc.a.run.app/a2a/check_prime_agent",
  ...
}
```

### Custom Host/Port Example
```json
{
  "url": "https://your-domain.com:9000/a2a/check_prime_agent",
  ...
}
```

**Important:** The `url` field in `remote_a2a/check_prime_agent/agent.json` must point to the actual RPC endpoint where your remote A2A agent is deployed and accessible.

## Troubleshooting

**Connection Issues:**
- Ensure the local ADK web server is running on port 8000
- Ensure the remote A2A server is running on port 8001
- Check that no firewall is blocking localhost connections
- **Verify the `url` field in `remote_a2a/check_prime_agent/agent.json` matches the actual deployed location of your remote A2A server**
- Verify the agent card URL passed to RemoteA2AAgent constructor matches the running A2A server


**Agent Not Responding:**
- Check the logs for both the local ADK web server on port 8000 and remote A2A server on port 8001
- Verify the agent instructions are clear and unambiguous
- **Double-check that the RPC URL in the agent.json file is correct and accessible**


### running

```bash
adk web main_agent --port 8002 
adk api_server --a2a --port 8001 remote_agent
```