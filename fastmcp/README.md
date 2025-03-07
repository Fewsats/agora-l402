# FastMCP server for Agora E-commerce API

## Overview

This FastMCP server exposes the Agora E-commerce API as a tool provider for AI assistants like Claude, enabling them to search for products, get product details, manage carts, and track orders.

## Installation

First, generate the MCP server code:

```bash
python generate.py
```

This will create a `main.py` file that contains all the Agora API tools ready to be used with FastMCP.

## Setup

1. Copy `.env.example` to `.env` and set your Agora API key:

```bash
cp .env.example .env
# Then edit .env to add your AGORA_API_KEY
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Claude Desktop App

To install the MCP server for use with the Claude desktop app:

```bash
fastmcp install main.py -f .env
```

This will add the server to `$HOME/Library/Application Support/Claude/claude_desktop_config.json` so Claude can access it directly.

You can ask Claude "what tools are available?" to see the list of Agora tools.

### Cursor

To use with Cursor:

1. Add a new command as explained in [the Cursor documentation](https://docs.cursor.com/context/model-context-protocol).
2. Select `type: command`
3. Add the following command:
   ```
   env AGORA_API_KEY=YOUR_API_KEY uv run --with fastmcp fastmcp run path/to/agora-l402/examples/fastmcp/main.py
   ```
   - Make sure to replace `YOUR_API_KEY` with your actual Agora API key.
   - Make sure to replace `path/to/agora-l402/examples/fastmcp/main.py` with the actual path to the main.py file.

## Debugging

To test the tools locally:

```bash
fastmcp dev main.py
```

This will start the development server with an inspector interface where you can test the tools directly.

## Available Tools

The MCP server exposes the following tools from the Agora API:

- `search_trial`: Search for products using the trial endpoint
- `text_search`: Full-featured product search
- `get_product_detail`: Get detailed information about a specific product
- `create_cart`: Create a new shopping cart
- `add_to_cart`: Add products to a cart
- `create_order`: Create a new order
- `track_order`: Track an existing order
- `refresh_token`: Refresh the API token

Each tool returns both the HTTP status code and the data, allowing AI systems to properly handle API responses.
