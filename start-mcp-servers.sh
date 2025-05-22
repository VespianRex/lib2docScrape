#!/bin/sh
# Start all MCP servers in background

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Starting MCP Servers..."

# Start Memory server
npx @modelcontextprotocol/server-memory & 
PID_MEMORY=$!
echo "Memory Server started (PID: $PID_MEMORY)"

# Start Brave Search server ONLY if API key is provided
PID_BRAVE=""
if [ -n "$BRAVE_API_KEY" ]; then
  echo "BRAVE_API_KEY provided. Starting Brave Search Server..."
  BRAVE_API_KEY=$BRAVE_API_KEY npx @modelcontextprotocol/server-brave-search & 
  PID_BRAVE=$!
  echo "Brave Search Server started (PID: $PID_BRAVE)"
else
  echo "BRAVE_API_KEY not set. Skipping Brave Search Server startup."
fi

# Start Sequential Thinking server
npx @modelcontextprotocol/server-sequential-thinking & 
PID_SEQ=$!
echo "Sequential Thinking Server started (PID: $PID_SEQ)"

echo "Background servers launched."
echo "Starting Context7 MCP server in foreground..."

# Run Context7 MCP server in the FOREGROUND as the main process
# The script will wait here until this command exits
exec npx @upstash/context7-mcp

# The script will only reach here if the above command fails immediately
echo "Error: Context7 MCP server failed to start or exited unexpectedly."
exit 1
