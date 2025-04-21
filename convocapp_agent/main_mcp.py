import json

from contextlib import asynccontextmanager
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP, Context
from mcp.types import TextContent
from convocapp_agent.clients.studio import StudioClient, studio as studio_client
from convocapp_agent.models.mcp_models import LLMClassifyResponse
from model_router import call_model
from prompts.prompt_builder import render_prompt

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
    prompt = render_prompt("classify_and_extract.txt.tmpl", user_input=user_input)
    raw_response = call_model(prompt, "classify_action_match")
    studio: StudioClient = ctx.request_context.lifespan_context["studio"]

    reasoning = [
        "Analyzed user message for intent classification",
        "Prompt used: classify_action_match.txt.tmpl",
        f"Model returned: {raw_response.strip()}",
    ]

    parsed = LLMClassifyResponse.model_validate(json.loads(raw_response.strip()))
    tool_name = parsed.tool_call.name if parsed.tool_call else None
    if tool_name:
        result = f"Intent detected. Tool to call: {tool_name}."
        reasoning.append(f"Mapped intent to tool: {tool_name}")

        if tool_name == "create_match":
            result = await studio.create_match(**parsed.tool_call.parameters)
            print("RESULT", result)
    else:
        # result = "I'm not sure how to help with that. Please try rephrasing."
        result = parsed.response
        reasoning.append("No matching tool found, answering question")

    print("Reasoning =====>", reasoning)

    return [TextContent(type="text", text=result)]


if __name__ == "__main__":
    mcp.run("sse")
