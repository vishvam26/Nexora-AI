"""
MCP Tool Registry — Step 13 Model Context Protocol

Decorators and registry functions to map Python methods to standard tool call
definitions that the LLM/Planner can discover and execute dynamically.
"""
import inspect
import logging
from typing import Dict, Any, Callable, List

logger = logging.getLogger("app.services.mcp.tool_registry")


class ToolRegistry:
    """
    Registry holding callable tool functions and metadata schemas.
    """
    _registry: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(cls, name: str, description: str):
        """
        Decorator to register a python function as an MCP tool.
        """
        def decorator(func: Callable):
            sig = inspect.signature(func)
            parameters = {
                "type": "object",
                "properties": {},
                "required": []
            }
            
            # Auto-build JSON Schema parameters from python signature
            for param_name, param in sig.parameters.items():
                if param_name == "self" or param_name == "db":
                    continue # Skip session parameters
                
                # Default type mapping
                param_type = "string"
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == float:
                    param_type = "number"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == list:
                    param_type = "array"

                parameters["properties"][param_name] = {
                    "type": param_type,
                    "description": f"Parameter: {param_name}"
                }
                
                if param.default == inspect.Parameter.empty:
                    parameters["required"].append(param_name)

            cls._registry[name] = {
                "name": name,
                "description": description,
                "callable": func,
                "schema": {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": description,
                        "parameters": parameters
                    }
                }
            }
            logger.info(f"[ToolRegistry] Registered MCP Tool: {name}")
            return func
        return decorator

    @classmethod
    def get_tool_definition(cls, name: str) -> Dict[str, Any]:
        return cls._registry.get(name, {}).get("schema", {})

    @classmethod
    def get_all_tool_definitions(cls) -> List[Dict[str, Any]]:
        return [t["schema"] for t in cls._registry.values()]

    @classmethod
    def execute(cls, name: str, *args, **kwargs) -> Any:
        tool = cls._registry.get(name)
        if not tool:
            raise KeyError(f"Tool '{name}' is not registered.")
        return tool["callable"](*args, **kwargs)
