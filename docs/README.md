# Volatility Balancing — Docs Index

## Overview

This documentation covers the Volatility Balancing trading system, which provides automated volatility-triggered trading with configurable order sizing strategies.

## Key Features

- **Volatility-Triggered Trading**: Automatic buy/sell based on price thresholds
- **Extensible Order Sizing**: Multiple strategies (Proportional, Fixed Percentage, Original)
- **Guardrail Protection**: Maintains asset allocation within specified bounds
- **Dividend Handling**: Automatic ex-dividend date processing and anchor adjustments
- **Real-time Simulation**: Backtesting with the same logic as live trading

## Documentation Structure

### Product Specifications

- [Volatility Trading Specification](product/volatility_trading_spec_v1.md) - Complete functional specification

### Architecture

- [Order Sizing Strategies](architecture/order_sizing_strategies.md) - Detailed guide to order sizing strategies
- [Component Architecture](architecture/component_architecture.md) - System component overview
- [System Architecture](architecture/system_architecture_v1.md) - High-level system design

### Development

- [Developer Notes](DEVELOPER_NOTES.md) - Development setup and guidelines
- [Migration Guide](MIGRATION.md) - System migration procedures

### API

- [OpenAPI Specification](api/openapi.yaml) - Complete API documentation
- [API README](api/OPENAPI_README.md) - API usage guide

---

_Last updated: 2025-01-11_
