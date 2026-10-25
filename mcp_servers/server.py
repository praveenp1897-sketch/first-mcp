
from datetime import datetime

from mcp.server import MCPServer

mcp = MCPServer("My First MCP Server")


@mcp.tool()
def add_numbers(a: float, b: float) -> float:
    """Add two numbers and return the result."""
    return a + b


@mcp.tool()
def get_current_time() -> str:
    """Return the current local time."""
    return datetime.now().astimezone().isoformat()

@mcp.tool()
def multiply_numbers(a: float, b: float) -> float:
    """Multiply two numbers and return the result."""
    return a * b

@mcp.tool()
def analyze_text(text: str) -> dict:
    """Analyze text and return its character, word, and sentence counts."""
    cleaned_text = text.strip()

    if not cleaned_text:
        raise ValueError("Text cannot be empty.")

    sentences = [
        sentence
        for sentence in cleaned_text.replace("!", ".").replace("?", ".").split(".")
        if sentence.strip()
    ]

    return {
        "character_count": len(cleaned_text),
        "word_count": len(cleaned_text.split()),
        "sentence_count": len(sentences),
    }



if __name__ == "__main__":
    mcp.run(transport="stdio")
