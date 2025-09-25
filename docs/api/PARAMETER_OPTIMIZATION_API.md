# Parameter Optimization API Documentation

**Version**: 1.0  
**Last Updated**: September 20, 2025  
**Status**: ✅ **PRODUCTION READY**

## Overview

The Parameter Optimization API provides comprehensive endpoints for managing parameter optimization configurations, running optimization processes, and retrieving results. This API is part of the Volatility Balancing trading system and enables users to optimize trading algorithm parameters for better performance.

## Base URL

```
http://localhost:8000/v1/optimization
```

## Authentication

Currently, the API does not require authentication. In production, this should be secured with appropriate authentication mechanisms.

## API Endpoints

### 1. Create Optimization Configuration

**POST** `/configs`

Creates a new parameter optimization configuration.

#### Request Body

```json
{
  "name": "AAPL Volatility Strategy Optimization",
  "ticker": "AAPL",
  "start_date": "2025-08-22T00:00:00Z",
  "end_date": "2025-09-21T00:00:00Z",
  "parameter_ranges": {
    "trigger_threshold_pct": {
      "min_value": 0.01,
      "max_value": 0.05,
      "step_size": 0.01,
      "parameter_type": "float",
      "name": "Trigger Threshold %",
      "description": "Volatility trigger threshold percentage"
    },
    "rebalance_ratio": {
      "min_value": 1.0,
      "max_value": 3.0,
      "step_size": 0.5,
      "parameter_type": "float",
      "name": "Rebalance Ratio",
      "description": "Rebalancing ratio multiplier"
    }
  },
  "optimization_criteria": {
    "primary_metric": "sharpe_ratio",
    "secondary_metrics": ["total_return", "max_drawdown"],
    "constraints": [
      {
        "metric": "max_drawdown",
        "constraint_type": "max_value",
        "value": -0.1,
        "description": "Maximum drawdown must be less than 10%"
      }
    ],
    "weights": {
      "sharpe_ratio": 1.0,
      "total_return": 0.5,
      "max_drawdown": 0.3
    },
    "minimize": false,
    "description": "Optimize for risk-adjusted returns with drawdown constraints"
  },
  "created_by": "user-uuid",
  "description": "Comprehensive optimization demo for AAPL volatility strategy",
  "max_combinations": 20,
  "batch_size": 5
}
```

#### Response

```json
{
  "id": "c15c26ea-1cd1-4f61-ae66-f79317aa3313",
  "name": "AAPL Volatility Strategy Optimization",
  "ticker": "AAPL",
  "start_date": "2025-08-22T00:00:00Z",
  "end_date": "2025-09-21T00:00:00Z",
  "status": "draft",
  "total_combinations": 20,
  "created_at": "2025-09-20T21:23:27.825506Z",
  "created_by": "user-uuid"
}
```

### 2. Get Optimization Configuration

**GET** `/configs/{config_id}`

Retrieves a specific optimization configuration by ID.

#### Response

```json
{
  "id": "c15c26ea-1cd1-4f61-ae66-f79317aa3313",
  "name": "AAPL Volatility Strategy Optimization",
  "ticker": "AAPL",
  "start_date": "2025-08-22T00:00:00Z",
  "end_date": "2025-09-21T00:00:00Z",
  "status": "completed",
  "total_combinations": 20,
  "created_at": "2025-09-20T21:23:27.825506Z",
  "created_by": "user-uuid"
}
```

### 3. Start Optimization

**POST** `/configs/{config_id}/start`

Starts the optimization process for a configuration.

#### Response

```json
{
  "message": "Optimization started successfully",
  "config_id": "c15c26ea-1cd1-4f61-ae66-f79317aa3313",
  "status": "running"
}
```

### 4. Get Optimization Progress

**GET** `/configs/{config_id}/progress`

Retrieves the current progress of an optimization run.

#### Response

```json
{
  "config_id": "c15c26ea-1cd1-4f61-ae66-f79317aa3313",
  "status": "completed",
  "progress_percentage": 100.0,
  "total_combinations": 20,
  "completed_combinations": 20,
  "failed_combinations": 0,
  "remaining_combinations": 0,
  "started_at": "2025-09-20T21:23:28.000000Z",
  "completed_at": "2025-09-20T21:23:29.000000Z"
}
```

### 5. Get Optimization Results

**GET** `/configs/{config_id}/results`

Retrieves all optimization results for a configuration.

#### Response

```json
[
  {
    "id": "11e0d103-9b35-4f66-8e9f-c672721f82f7",
    "config_id": "c15c26ea-1cd1-4f61-ae66-f79317aa3313",
    "parameter_combination": {
      "trigger_threshold_pct": 0.01,
      "rebalance_ratio": 1.0
    },
    "combination_id": "c15c26ea-1cd1-4f61-ae66-f79317aa3313_0",
    "metrics": {
      "total_return": 0.0,
      "sharpe_ratio": 0.9630381381920707,
      "max_drawdown": -0.03920082065407615,
      "volatility": 0.09014341507150087,
      "calmar_ratio": 0.0,
      "sortino_ratio": 1.0992185639386027,
      "win_rate": 0.5108651770633537,
      "profit_factor": 1.778406859805127,
      "trade_count": 22,
      "avg_trade_duration": 5.005936588696002
    },
    "status": "completed",
    "error_message": null,
    "created_at": "2025-09-20T21:24:54.381290Z",
    "completed_at": "2025-09-20T21:24:54.481668Z",
    "execution_time_seconds": null
  }
]
```

### 6. Generate Heatmap Data

**GET** `/configs/{config_id}/heatmap?x_parameter={param}&y_parameter={param}&metric={metric}`

Generates heatmap data for visualization.

#### Query Parameters

- `x_parameter`: Parameter to use for X-axis (e.g., "trigger_threshold_pct")
- `y_parameter`: Parameter to use for Y-axis (e.g., "rebalance_ratio")
- `metric`: Metric to visualize (e.g., "sharpe_ratio")

#### Response

```json
{
  "config_id": "c15c26ea-1cd1-4f61-ae66-f79317aa3313",
  "x_parameter": "trigger_threshold_pct",
  "y_parameter": "rebalance_ratio",
  "metric": "sharpe_ratio",
  "cells": [
    {
      "x_value": 0.01,
      "y_value": 1.0,
      "metric_value": 0.7403984964805943,
      "combination_id": "c15c26ea-1cd1-4f61-ae66-f79317aa3313_0",
      "is_valid": true,
      "error_message": null
    }
  ],
  "x_values": [0.01, 0.02, 0.03, 0.04],
  "y_values": [1.0, 1.5, 2.0, 2.5, 3.0],
  "statistics": {
    "min": 0.5950578124232944,
    "max": 1.4675990017084115,
    "mean": 0.9486128503344805,
    "count": 20,
    "valid_count": 20,
    "invalid_count": 0
  },
  "created_at": "2025-09-20T21:26:11.071083Z"
}
```

### 7. Get Available Metrics

**GET** `/metrics`

Retrieves all available optimization metrics.

#### Response

```json
{
  "metrics": [
    {
      "name": "TOTAL_RETURN",
      "display_name": "Total Return",
      "description": "Optimize for Total Return",
      "unit": "percentage"
    },
    {
      "name": "SHARPE_RATIO",
      "display_name": "Sharpe Ratio",
      "description": "Optimize for Sharpe Ratio",
      "unit": "ratio"
    },
    {
      "name": "MAX_DRAWDOWN",
      "display_name": "Max Drawdown",
      "description": "Optimize for Max Drawdown",
      "unit": "percentage"
    }
  ]
}
```

### 8. Get Parameter Types

**GET** `/parameter-types`

Retrieves all supported parameter types.

#### Response

```json
{
  "parameter_types": [
    {
      "name": "FLOAT",
      "display_name": "Float",
      "description": "Parameter type: float"
    },
    {
      "name": "INTEGER",
      "display_name": "Integer",
      "description": "Parameter type: integer"
    },
    {
      "name": "BOOLEAN",
      "display_name": "Boolean",
      "description": "Parameter type: boolean"
    },
    {
      "name": "CATEGORICAL",
      "display_name": "Categorical",
      "description": "Parameter type: categorical"
    }
  ]
}
```

## Optimization Modes

### Single-Goal Optimization

You can now optimize for a single metric without requiring secondary metrics:

```json
{
  "optimization_criteria": {
    "primary_metric": "sharpe_ratio",
    "secondary_metrics": [],
    "constraints": [],
    "weights": {
      "sharpe_ratio": 1.0
    },
    "minimize": false,
    "description": "Single-goal optimization for Sharpe ratio"
  }
}
```

### Multi-Goal Optimization

For more complex optimization, you can include secondary metrics with configurable weights:

```json
{
  "optimization_criteria": {
    "primary_metric": "sharpe_ratio",
    "secondary_metrics": ["total_return", "max_drawdown"],
    "constraints": [],
    "weights": {
      "sharpe_ratio": 1.0,
      "total_return": 0.5,
      "max_drawdown": 0.3
    },
    "minimize": false,
    "description": "Multi-goal optimization with custom weights"
  }
}
```

### Weight Configuration

- **Primary metric**: Typically has weight 1.0 (highest influence)
- **Secondary metrics**: Usually have weights 0.1-0.5 (lower influence)
- **Higher weights**: More influence on the final optimization score
- **Weight range**: 0.0 to 10.0 (recommended: 0.1-1.0)

## Data Models

### ParameterRange

```json
{
  "min_value": 0.01,
  "max_value": 0.05,
  "step_size": 0.01,
  "parameter_type": "float",
  "name": "Trigger Threshold %",
  "description": "Volatility trigger threshold percentage",
  "categorical_values": null
}
```

### OptimizationCriteria

```json
{
  "primary_metric": "sharpe_ratio",
  "secondary_metrics": ["total_return", "max_drawdown"],
  "constraints": [
    {
      "metric": "max_drawdown",
      "constraint_type": "max_value",
      "value": -0.1,
      "description": "Maximum drawdown must be less than 10%"
    }
  ],
  "weights": {
    "sharpe_ratio": 0.5,
    "total_return": 0.3,
    "max_drawdown": 0.2
  },
  "minimize": false,
  "description": "Optimize for risk-adjusted returns with drawdown constraints"
}
```

## Error Handling

### Common Error Responses

#### 400 Bad Request

```json
{
  "detail": "Validation error message"
}
```

#### 404 Not Found

```json
{
  "detail": "Configuration not found"
}
```

#### 500 Internal Server Error

```json
{
  "detail": "Internal server error: error message"
}
```

## Rate Limiting

Currently, there are no rate limits implemented. In production, appropriate rate limiting should be added based on usage patterns.

## Examples

### Complete Optimization Workflow

1. **Create Configuration**

```bash
curl -X POST "http://localhost:8000/v1/optimization/configs" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Optimization",
    "ticker": "AAPL",
    "start_date": "2025-08-22T00:00:00Z",
    "end_date": "2025-09-21T00:00:00Z",
    "parameter_ranges": {
      "trigger_threshold_pct": {
        "min_value": 0.01,
        "max_value": 0.03,
        "step_size": 0.01,
        "parameter_type": "float",
        "name": "Trigger Threshold %",
        "description": "Volatility trigger threshold percentage"
      }
    },
    "optimization_criteria": {
      "primary_metric": "sharpe_ratio",
      "secondary_metrics": ["total_return"],
      "constraints": [],
      "weights": {
        "sharpe_ratio": 1.0,
        "total_return": 0.5
      },
      "minimize": false,
      "description": "Test optimization"
    },
    "created_by": "test-user",
    "description": "Test optimization",
    "max_combinations": 3,
    "batch_size": 3
  }'
```

2. **Start Optimization**

```bash
curl -X POST "http://localhost:8000/v1/optimization/configs/{config_id}/start"
```

3. **Check Progress**

```bash
curl -X GET "http://localhost:8000/v1/optimization/configs/{config_id}/progress"
```

4. **Get Results**

```bash
curl -X GET "http://localhost:8000/v1/optimization/configs/{config_id}/results"
```

5. **Generate Heatmap**

```bash
curl -X GET "http://localhost:8000/v1/optimization/configs/{config_id}/heatmap?x_parameter=trigger_threshold_pct&y_parameter=rebalance_ratio&metric=sharpe_ratio"
```

## Testing

The API can be tested using the provided demo scripts:

```bash
# Run comprehensive demo
python demo_optimization_system.py

# Run simple test
python test_optimization_simple.py

# Run API test
python test_optimization_api.py
```

## Interactive Documentation

Visit `http://localhost:8000/docs` for interactive API documentation with Swagger UI, where you can test all endpoints directly from your browser.

---

_API Documentation generated on September 20, 2025_
