
import asyncio
import json

from openai import OpenAI
from mcp import Client, StdioServerParameters


MODEL = "gpt-4.1-mini"
MAX_TOOL_ROUNDS = 5

# OpenAI tool definitions corresponding to our MCP server tools.
OPENAI_TOOLS = [
    {
        "type": "function",
        "name": "add_numbers",
        "description": "Add two numbers.",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"},
            },
            "required": ["a", "b"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "multiply_numbers",
        "description": "Multiply two numbers.",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"},
            },
            "required": ["a", "b"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_current_time",
        "description": "Get the current local time of the computer.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "analyze_text",
        "description": "Count the characters, words, and sentences in text.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to analyze",
                }
            },
            "required": ["text"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


def serialize_tool_result(result) -> str:
    """Convert an MCP tool result into text for the model."""
    if result.is_error:
        messages = [
            item.text
            for item in (result.content or [])
            if getattr(item, "text", None)
        ]
        return json.dumps({
            "error": messages or ["MCP tool execution failed"]
        })

    if result.structured_content is not None:
        return json.dumps(result.structured_content, default=str)

    messages = [
        item.text
        for item in (result.content or [])
        if getattr(item, "text", None)
    ]
    return "\n".join(messages) or "Tool completed without text output."


async def main():
    openai_client = OpenAI()

    server = StdioServerParameters(
        command="python",
        args=["mcp_servers/server.py"],
    )

    print("Connecting to MCP server...")

    async with Client(server) as mcp_client:
        discovered = await mcp_client.list_tools()
        available_names = {tool.name for tool in discovered.tools}

        print("MCP tools:", ", ".join(sorted(available_names)))

        # Prevent the model from requesting tools the server does not expose.
        tools = [
            tool
            for tool in OPENAI_TOOLS
            if tool["name"] in available_names
        ]

        if not tools:
            print("No matching tools were found.")
            return

        user_request = input("\nEnter your request: ").strip()

        if not user_request:
            print("Please enter a request.")
            return

        response = openai_client.responses.create(
            model=MODEL,
            instructions=(
                "You are a helpful assistant connected to MCP tools. "
                "Use the available tools when they help answer the user. "
                "Never claim a tool succeeded if it returned an error."
            ),
            input=user_request,
            tools=tools,
        )

        # Continue until the model produces a final answer.
        for round_number in range(MAX_TOOL_ROUNDS):
            function_calls = [
                item
                for item in response.output
                if item.type == "function_call"
            ]

            if not function_calls:
                print("\nAssistant:", response.output_text)
                return

            tool_outputs = []

            for call in function_calls:
                name = call.name

                if name not in available_names:
                    output = json.dumps({
                        "error": f"Tool not available: {name}"
                    })
                else:
                    try:
                        arguments = json.loads(call.arguments)

                        print(f"\nOpenAI selected tool: {name}")
                        print("Arguments:", arguments)

                        result = await mcp_client.call_tool(
                            name,
                            arguments,
                        )
                        output = serialize_tool_result(result)

                    except (ValueError, TypeError) as exc:
                        output = json.dumps({
                            "error": f"Invalid tool arguments: {exc}"
                        })
                    except Exception as exc:
                        output = json.dumps({
                            "error": f"Tool execution failed: {exc}"
                        })

                print("Tool output:", output)

                tool_outputs.append({
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": output,
                })

            response = openai_client.responses.create(
                model=MODEL,
                previous_response_id=response.id,
                input=tool_outputs,
                tools=tools,
            )

        print(
            "\nStopped after reaching the tool-call limit. "
            "Try a simpler request."
        )


if __name__ == "__main__":
    asyncio.run(main())
