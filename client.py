
import asyncio

from mcp import Client, StdioServerParameters


async def main():
    server = StdioServerParameters(
        command="python",
        args=["mcp_servers/server.py"],
    )

    async with Client(server) as client:
        # Discover available tools
        tools = await client.list_tools()
        
        analysis_result = await client.call_tool(
            "analyze_text",
            {
                "text": "MCP connects AI to tools. Agents can use MCP."
            },
        )

        print("\nText analysis result:")
        print(analysis_result)

        print("Discovered tool names:", [tool.name for tool in tools.tools])

        print("Available tools:")
        for tool in tools.tools:
            print(f"- {tool.name}: {tool.description}")

        # Test calculator
        result = await client.call_tool(
            "add_numbers",
            {"a": 10, "b": 20},
        )
        print("\nCalculator result:")
        print(result)
        
        # Test multiplication
        multiplication_result = await client.call_tool(
            "multiply_numbers",
            {"a": 7, "b": 8},
        )

        print("\nMultiplication result:")
        print(multiplication_result)


        # Test current-time tool
        time_result = await client.call_tool(
            "get_current_time",
            {},
        )
        print("\nCurrent-time result:")
        print(time_result)


if __name__ == "__main__":
    asyncio.run(main())
