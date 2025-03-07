from inspect import signature, getdoc
from agora_l402.core import Agora
from textwrap import dedent

def generate_mcp_tools():
    agora = Agora()
    tools = agora.as_tools()
    
    header = '''
    from typing import Dict, List
    from fastmcp import FastMCP
    from agora_l402.core import Agora
    import os
    import json

    # Create FastMCP and Agora instances
    mcp = FastMCP("Agora E-commerce MCP Server")
    agora = Agora(api_key=os.environ.get("AGORA_API_KEY"))

    '''
    
    tool_template = '''
    @mcp.tool()
    async def {name}({params}) -> str:
        """{docstring}"""
        r = agora.{name}({args})
        return r.status_code, r.text
    '''
    
    footer = '''
    if __name__ == "__main__":
        mcp.run()
    '''
    
    generated_code = [dedent(header)]
    
    for tool_func in tools:
        tool_name = tool_func.__name__
        sig = signature(tool_func)
        
        # Skip the 'self' parameter
        parameters = list(sig.parameters.items())
        if parameters and parameters[0][0] == 'self':
            parameters = parameters[1:]
        
        params = ', '.join(f"{p}: {v.annotation.__name__ if hasattr(v.annotation, '__name__') else 'str'}" 
                         for p, v in parameters)
        args = ', '.join(p for p, _ in parameters)
        docstring = getdoc(tool_func) or f"{tool_name} function"
        
        tool_code = dedent(tool_template).format(
            name=tool_name,
            params=params,
            docstring=docstring,
            args=args
        )
        generated_code.append(tool_code)
    
    generated_code.append(dedent(footer))
    
    with open('main.py', 'w') as f:
        f.write('\n'.join(generated_code))

if __name__ == "__main__":
    generate_mcp_tools()
