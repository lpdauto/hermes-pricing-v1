"""PRICING_V1 Hermes plugin registration."""

from . import schemas, tools

def register(ctx):
    ctx.register_tool(
        name="pricing_v1",
        toolset="pricing_v1",
        schema=schemas.PRICING_V1,
        handler=tools.handle_pricing,
    )
