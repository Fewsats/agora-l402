
from typing import Dict, List
from fastmcp import FastMCP
from agora_l402.core import Agora
import os
import json

# Create FastMCP and Agora instances
mcp = FastMCP("Agora E-commerce MCP Server")
agora = Agora(api_key=os.environ.get("AGORA_API_KEY"))



@mcp.tool()
async def search_trial(query: str, price_min: int, price_max: int, sort: str, order: str) -> str:
    """Search for products using the trial endpoint.

Args:
    query (str): Search query text
    price_min (int, optional): Minimum price for filtering products (default: 0)
    price_max (int, optional): Maximum price for filtering products
    sort (str, optional): Sorting field: price:relevance
    order (str, optional): Sorting order: asc or desc
    
Returns:
    dict: Search results with products matching the query

Example:
    search_trial("shoes", [100, 1000], "price:relevance", "desc")"""
    r = agora.search_trial(query, price_min, price_max, sort, order)
    return r.status_code, r.text


@mcp.tool()
async def get_product_detail(slug: str) -> str:
    """Retrieve detailed information about a specific product.

Args:
    slug (str): The unique identifier of the product to retrieve
    
Returns:
    dict: Detailed information about the requested product

Example:
    agora.get_product_detail("calzuro-without-pistachio-eb12f468-48a2-48af-9f5e-3fda5f6c135c-1708446961787")"""
    r = agora.get_product_detail(slug)
    return r.status_code, r.text


@mcp.tool()
async def create_cart(custom_user_id: str, items: List) -> str:
    """Create a new cart for a user.

Args:
    custom_user_id (str, optional): Unique identifier for the user
    items (list, optional): List of items to add to the cart
        Each item should be a dict with:
        - variantId (int): Variant ID of the product
        - product (int/str): Product ID
        - quantity (int): Quantity of the product
        
Returns:
    dict: Response with cart creation status

Example:
    agora.create_cart("user123", [
        {"variantId": 123, "product": "678f71a9356a36f784ee2e88", "quantity": 1}
    ])"""
    r = agora.create_cart(custom_user_id, items)
    return r.status_code, r.text


@mcp.tool()
async def add_to_cart(product_id: str, variant_id: str, quantity: int, custom_user_id: str) -> str:
    """Add a product to an existing cart.

Args:
    product_id (str/int): ID of the product to add
    variant_id (str/int): Variant ID of the product
    quantity (int, optional): Quantity of the product (default: 1)
    custom_user_id (str, optional): Unique identifier for the user
    
Returns:
    dict: Response with cart update status

Example:
    agora.add_to_cart("678f71a9356a36f784ee2e88", "2061038485517", 2, "user123")"""
    r = agora.add_to_cart(product_id, variant_id, quantity, custom_user_id)
    return r.status_code, r.text


@mcp.tool()
async def create_order(encrypted_payment_info: str, shipping_address: Dict, current_user: Dict) -> str:
    """Create a new order from cart items.

Args:
    encrypted_payment_info (str): Encrypted payment information
    shipping_address (dict): Dictionary containing shipping address details:
        - addressFirst (str): Street address
        - city (str): City name
        - state (str): State/province
        - country (str): Country name
        - addressName (str): Name associated with address
        - zipCode (str): Postal/ZIP code
    current_user (dict): Dictionary containing user information:
        - firstname (str): User's first name
        - lastname (str): User's last name
        - email (str): User's email address
        - _id (str): User's ID
        
Returns:
    dict: Order creation response with success status and order ID

Example:
    agora.create_order(
        "encrypted_data",
        {
            "addressFirst": "123 Main St",
            "city": "New York",
            "state": "NY",
            "country": "US",
            "addressName": "Home",
            "zipCode": "10001"
        },
        {
            "firstname": "John",
            "lastname": "Doe",
            "email": "john@example.com",
            "_id": "user123"
        }
    )"""
    r = agora.create_order(encrypted_payment_info, shipping_address, current_user)
    return r.status_code, r.text


@mcp.tool()
async def track_order(order_id: str) -> str:
    """Track an existing order by its ID.

Args:
    order_id (str): Unique identifier of the order to track
    
Returns:
    dict: Detailed order information including items, status, and shipping details

Example:
    agora.track_order("67c8577b3e370f07d12c7722")"""
    r = agora.track_order(order_id)
    return r.status_code, r.text


@mcp.tool()
async def refresh_token(refresh_token_str: str) -> str:
    """Refresh API key and token by providing a valid refresh token.

Args:
    refresh_token_str (str): The refresh token to validate and retrieve
                           a new API key and refresh token
    
Returns:
    dict: Object containing new API key, refresh token, and expiration time
          with the following structure:
          {
            "status": "success",
            "data": {
              "apiKey": "...",
              "refreshToken": "...",
              "expiresAt": "..."
            }
          }

Raises:
    ValueError: If the refresh token is invalid or missing"""
    r = agora.refresh_token(refresh_token_str)
    return r.status_code, r.text


@mcp.tool()
async def create_payment_intent(offer_id: str, amount: int, title: str, description: str, currency: str) -> str:
    """Create a payment intent for a product or cart.

Args:
    offer_id (str): Unique identifier for this offer (variant_id for items, user_id for carts)
    amount (int): Payment amount in cents
    title (str): Offer title
    description (str): Offer description
    currency (str, optional): Payment currency (default: USD)
    
Returns:
    dict: Created payment options for product / cart.

Example:
    agora.create_payment_intent(
        "12345",
        1999, # 19.99 USD in cents
        title="Altra Shoes",
        description="Altra Escalanta v4 running shoes"
    )"""
    r = agora.create_payment_intent(offer_id, amount, title, description, currency)
    return r.status_code, r.text


if __name__ == "__main__":
    mcp.run()
