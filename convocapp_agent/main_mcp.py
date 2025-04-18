from contextlib import asynccontextmanager
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP, Context
from mcp.types import TextContent
from convocapp_agent.clients.studio import StudioClient, studio as studio_client
from model_router import call_model
from prompts.prompt_builder import render_prompt

import datetime

load_dotenv()


@asynccontextmanager
async def lifespan(_server: FastMCP):
    print("LIFESPAN STARTING...")
    try:
        await studio_client.connect()
        yield {"studio": studio_client}
    finally:
        await studio_client.cleanup()
        print("LIFESPAN ENDED")


mcp = FastMCP("convocapp-agent", version="0.1.0", lifespan=lifespan, port=8000)


# Fallback reasoning tool to classify user intent (for mcp/perform equivalent)
@mcp.tool(
    name="classify_action_match",
    description="Classifies user intent and suggests tool usage",
)
async def classify_action_match(ctx: Context, user_input: str) -> list[TextContent]:
    prompt = render_prompt("classify_action_match.txt.tmpl", user_input=user_input)
    raw_response = call_model(prompt, task="classification")
    studio: StudioClient = ctx.request_context.lifespan_context["studio"]

    reasoning = [
        "Analyzed user message for intent classification",
        "Prompt used: classify_action_match.txt.tmpl",
        f"Model returned: {raw_response.strip()}",
    ]

    tool_name = None
    if "1" in raw_response:
        tool_name = "create_match"
    elif "2" in raw_response:
        tool_name = "get_match_info"
    elif "3" in raw_response:
        tool_name = "add_players"
    elif "4" in raw_response:
        tool_name = "edit_match"

    if tool_name:
        result = f"Intent detected. Tool to call: {tool_name}."
        reasoning.append(f"Mapped intent to tool: {tool_name}")

        if tool_name == "create_match":
            result = await studio.create_match(datetime.datetime.now(), "Alliance Arena Stadium")
            print("RESULT", result)
    else:
        result = "I'm not sure how to help with that. Please try rephrasing."
        reasoning.append("No matching tool found")

    return [TextContent(type="text", text=f"{result}\n\nReasoning:\n" + "\n".join(reasoning))]


if __name__ == "__main__":
    mcp.run("sse")
