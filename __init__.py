"""PRICING_V1 Hermes plugin registration."""

def register(ctx):
    from .tools import register_tools
    register_tools(ctx)
