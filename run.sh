#!/bin/bash
# Setup and run script for Epic Task Manager

echo "Epic Task Manager - Setup & Run Script"
echo "============================================="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# Install dependencies
echo "Installing/updating dependencies..."
uv pip install -e . --quiet

echo ""
echo "Available commands:"
echo ""
echo "1. Run MCP Inspector (recommended for testing):"
echo "   uv run fastmcp dev main.py"
echo ""
echo "2. Run server directly (for Cursor/production):"
echo "   uv run python main.py"
echo ""
echo "3. Install in Cursor:"
echo "   Already configured in ~/.cursor/mcp.json"
echo ""

# Ask user what they want to do
read -p "What would you like to do? [1/2/3/exit]: " choice

case $choice in
    1)
        echo "Starting MCP Inspector..."
        uv run fastmcp dev main.py
        ;;
    2)
        echo "Starting server in stdio mode..."
        uv run python main.py
        ;;
    3)
        echo "Configuration already set in ~/.cursor/mcp.json"
        echo "Please restart Cursor to load the new MCP server."
        ;;
    exit)
        echo "Goodbye!"
        ;;
    *)
        echo "Invalid choice. Please run the script again."
        ;;
esac
