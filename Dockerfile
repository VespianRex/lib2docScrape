FROM node:18-alpine
WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Install MCP servers with individual error handling
RUN npm install -g @modelcontextprotocol/server-memory && \
    npm install -g @modelcontextprotocol/server-brave-search && \
    npm install -g @modelcontextprotocol/server-sequential-thinking && \
    npm install -g @upstash/context7-mcp && \
    npm install -g mcp-wsl-exec || \
    (echo "Error: Failed to install required MCP servers" && exit 1)

# Copy application files
COPY . .

# Copy the startup script and make it executable
COPY start-mcp-servers.sh /app/
RUN chmod +x /app/start-mcp-servers.sh

# Run the startup script
CMD ["/app/start-mcp-servers.sh"]
