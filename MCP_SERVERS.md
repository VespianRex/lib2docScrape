# MCP Servers Integration

This project now includes multiple Model Context Protocol (MCP) servers to enhance AI capabilities:

## Integrated MCP Servers

1. **Context7 MCP** - The original server for retrieving library documentation
2. **Memory MCP** - Provides persistent memory using a local knowledge graph
3. **Brave Search MCP** - Integrates web and local search capabilities
4. **Sequential Thinking MCP** - Facilitates structured problem-solving through step-by-step thinking

## Usage

### Building the Docker Image

```bash
docker build -t lib2docscrape .
```

### Running the Container

```bash
docker run -it lib2docscrape
```

### Configuration

For the Brave Search MCP server to work properly, you'll need to provide an API key. You can do this by setting the `BRAVE_API_KEY` environment variable when running the container:

```bash
docker run -it -e BRAVE_API_KEY=your_api_key_here lib2docscrape
```

## MCP Server Details

### Memory MCP
Provides persistent memory using a local knowledge graph, allowing AI to remember information across sessions.

Key features:
- Entity management with observations
- Relation tracking between entities
- Knowledge graph persistence

### Brave Search MCP
Integrates the Brave Search API for both web and local search capabilities.

Key features:
- Web search with pagination and filtering
- Local search for businesses and services
- Automatic fallback to web search when no local results are found

### Sequential Thinking MCP
Facilitates structured problem-solving through a step-by-step thinking process.

Key features:
- Break down complex problems into manageable steps
- Revise and refine thoughts as understanding deepens
- Branch into alternative paths of reasoning

## Note on Docker Configuration

The Dockerfile is configured to run all MCP servers simultaneously. The Context7 MCP server runs in the foreground, while the other servers run as background processes.