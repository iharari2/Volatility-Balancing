# =========================
# backend/tests/integration/test_optimization_api.py
# =========================

from uuid import uuid4


class TestOptimizationAPI:
    def test_create_optimization_config(self, client):
        """Test creating an optimization configuration."""
        config_data = {
            "name": "Test Optimization",
            "ticker": "AAPL",
            "start_date": "2024-09-24T00:00:00Z",
            "end_date": "2025-09-25T00:00:00Z",
            "parameter_ranges": {
                "trigger_threshold": {
                    "min_value": 0.01,
                    "max_value": 0.05,
                    "step_size": 0.01,
                    "parameter_type": "float",
                    "name": "trigger_threshold",
                    "description": "Price movement percentage that triggers a rebalancing trade",
                }
            },
            "optimization_criteria": {
                "primary_metric": "total_return",
                "secondary_metrics": ["sharpe_ratio"],
                "constraints": [],
                "weights": {"total_return": 1.0, "sharpe_ratio": 0.5},
                "minimize": False,
                "description": "",
            },
            "created_by": "550e8400-e29b-41d4-a716-446655440000",
            "description": "Test optimization configuration",
            "max_combinations": 100,
            "batch_size": 10,
        }

        response = client.post("/v1/optimization/configs", json=config_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Optimization"
        assert data["ticker"] == "AAPL"
        assert data["status"] == "draft"
        assert "id" in data
        assert "created_at" in data

    def test_create_optimization_config_invalid_weights(self, client):
        """Test creating config with invalid weights fails."""
        config_data = {
            "name": "Test Optimization",
            "ticker": "AAPL",
            "start_date": "2024-09-24T00:00:00Z",
            "end_date": "2025-09-25T00:00:00Z",
            "parameter_ranges": {},
            "optimization_criteria": {
                "primary_metric": "total_return",
                "secondary_metrics": ["sharpe_ratio"],
                "constraints": [],
                "weights": {
                    "total_return": 1.0
                    # Missing sharpe_ratio weight
                },
                "minimize": False,
                "description": "",
            },
            "created_by": "550e8400-e29b-41d4-a716-446655440000",
            "description": "Test optimization configuration",
            "max_combinations": 100,
            "batch_size": 10,
        }

        response = client.post("/v1/optimization/configs", json=config_data)

        assert response.status_code == 400
        assert "Weight not specified for metric" in response.json()["detail"]

    def test_create_optimization_config_no_secondary_metrics(self, client):
        """Test creating config without secondary metrics fails."""
        config_data = {
            "name": "Test Optimization",
            "ticker": "AAPL",
            "start_date": "2024-09-24T00:00:00Z",
            "end_date": "2025-09-25T00:00:00Z",
            "parameter_ranges": {},
            "optimization_criteria": {
                "primary_metric": "total_return",
                "secondary_metrics": [],  # Empty secondary metrics
                "constraints": [],
                "weights": {"total_return": 1.0},
                "minimize": False,
                "description": "",
            },
            "created_by": "550e8400-e29b-41d4-a716-446655440000",
            "description": "Test optimization configuration",
            "max_combinations": 100,
            "batch_size": 10,
        }

        response = client.post("/v1/optimization/configs", json=config_data)

        assert response.status_code == 400
        assert "At least one secondary metric must be specified" in response.json()["detail"]

    def test_get_optimization_config(self, client):
        """Test getting an optimization configuration."""
        # First create a config
        config_data = self._create_test_config_data()
        create_response = client.post("/v1/optimization/configs", json=config_data)
        assert create_response.status_code == 200
        config_id = create_response.json()["id"]

        # Then get it
        response = client.get(f"/v1/optimization/configs/{config_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == config_id
        assert data["name"] == config_data["name"]

    def test_get_optimization_config_not_found(self, client):
        """Test getting a non-existent configuration."""
        fake_id = str(uuid4())
        response = client.get(f"/v1/optimization/configs/{fake_id}")

        assert response.status_code == 404

    def test_list_optimization_configs(self, client):
        """Test listing optimization configurations."""
        # Create multiple configs
        for i in range(3):
            config_data = self._create_test_config_data(name=f"Test Config {i}")
            response = client.post("/v1/optimization/configs", json=config_data)
            assert response.status_code == 200

        # List all configs
        response = client.get("/v1/optimization/configs")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        assert all("id" in config for config in data)

    def test_list_optimization_configs_with_pagination(self, client):
        """Test listing configs with pagination."""
        # Create multiple configs
        for i in range(5):
            config_data = self._create_test_config_data(name=f"Test Config {i}")
            response = client.post("/v1/optimization/configs", json=config_data)
            assert response.status_code == 200

        # List with limit
        response = client.get("/v1/optimization/configs?limit=2&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_start_optimization(self, client):
        """Test starting an optimization."""
        # Create a config
        config_data = self._create_test_config_data()
        create_response = client.post("/v1/optimization/configs", json=config_data)
        assert create_response.status_code == 200
        config_id = create_response.json()["id"]

        # Start optimization
        response = client.post(f"/v1/optimization/configs/{config_id}/start")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "started" in data["message"].lower()

    def test_start_optimization_not_found(self, client):
        """Test starting optimization for non-existent config."""
        fake_id = str(uuid4())
        response = client.post(f"/v1/optimization/configs/{fake_id}/start")

        assert response.status_code == 404

    def test_get_optimization_progress(self, client):
        """Test getting optimization progress."""
        # Create and start a config
        config_data = self._create_test_config_data()
        create_response = client.post("/v1/optimization/configs", json=config_data)
        assert create_response.status_code == 200
        config_id = create_response.json()["id"]

        start_response = client.post(f"/v1/optimization/configs/{config_id}/start")
        assert start_response.status_code == 200

        # Get progress
        response = client.get(f"/v1/optimization/configs/{config_id}/progress")

        assert response.status_code == 200
        data = response.json()
        assert "config_id" in data
        assert "total_combinations" in data
        assert "completed_combinations" in data
        assert "failed_combinations" in data

    def test_get_optimization_progress_not_running(self, client):
        """Test getting progress for non-running optimization."""
        # Create a config but don't start it
        config_data = self._create_test_config_data()
        create_response = client.post("/v1/optimization/configs", json=config_data)
        assert create_response.status_code == 200
        config_id = create_response.json()["id"]

        # Try to get progress
        response = client.get(f"/v1/optimization/configs/{config_id}/progress")

        assert response.status_code == 400
        assert "not running" in response.json()["detail"].lower()

    def test_get_optimization_results(self, client):
        """Test getting optimization results."""
        # Create and start a config
        config_data = self._create_test_config_data()
        create_response = client.post("/v1/optimization/configs", json=config_data)
        assert create_response.status_code == 200
        config_id = create_response.json()["id"]

        start_response = client.post(f"/v1/optimization/configs/{config_id}/start")
        assert start_response.status_code == 200

        # Get results
        response = client.get(f"/v1/optimization/configs/{config_id}/results")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_optimization_results_with_sorting(self, client):
        """Test getting results with sorting."""
        # Create and start a config
        config_data = self._create_test_config_data()
        create_response = client.post("/v1/optimization/configs", json=config_data)
        assert create_response.status_code == 200
        config_id = create_response.json()["id"]

        start_response = client.post(f"/v1/optimization/configs/{config_id}/start")
        assert start_response.status_code == 200

        # Get results with sorting
        response = client.get(
            f"/v1/optimization/configs/{config_id}/results?sort_by=total_return&ascending=false"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_optimization_results_with_limit(self, client):
        """Test getting results with limit."""
        # Create and start a config
        config_data = self._create_test_config_data()
        create_response = client.post("/v1/optimization/configs", json=config_data)
        assert create_response.status_code == 200
        config_id = create_response.json()["id"]

        start_response = client.post(f"/v1/optimization/configs/{config_id}/start")
        assert start_response.status_code == 200

        # Get results with limit
        response = client.get(f"/v1/optimization/configs/{config_id}/results?limit=5")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5

    def test_get_optimization_metrics(self, client):
        """Test getting available optimization metrics."""
        response = client.get("/v1/optimization/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert isinstance(data["metrics"], list)
        assert len(data["metrics"]) > 0

    def test_get_optimization_parameter_types(self, client):
        """Test getting available parameter types."""
        response = client.get("/v1/optimization/parameter-types")

        assert response.status_code == 200
        data = response.json()
        assert "parameter_types" in data
        assert isinstance(data["parameter_types"], list)
        assert len(data["parameter_types"]) > 0

    def test_create_optimization_config_with_constraints(self, client):
        """Test creating config with constraints."""
        config_data = {
            "name": "Test Optimization with Constraints",
            "ticker": "AAPL",
            "start_date": "2024-09-24T00:00:00Z",
            "end_date": "2025-09-25T00:00:00Z",
            "parameter_ranges": {
                "trigger_threshold": {
                    "min_value": 0.01,
                    "max_value": 0.05,
                    "step_size": 0.01,
                    "parameter_type": "float",
                    "name": "trigger_threshold",
                    "description": "Price movement percentage that triggers a rebalancing trade",
                }
            },
            "optimization_criteria": {
                "primary_metric": "total_return",
                "secondary_metrics": ["sharpe_ratio", "max_drawdown"],
                "constraints": [
                    {
                        "metric": "sharpe_ratio",
                        "constraint_type": "min_value",
                        "value": 1.0,
                        "weight": 2.0,
                        "description": "Sharpe ratio must be at least 1.0",
                    },
                    {
                        "metric": "max_drawdown",
                        "constraint_type": "max_value",
                        "value": -0.10,
                        "weight": 1.5,
                        "description": "Maximum drawdown must be less than 10%",
                    },
                ],
                "weights": {"total_return": 1.0, "sharpe_ratio": 0.5, "max_drawdown": 0.3},
                "minimize": False,
                "description": "",
            },
            "created_by": "550e8400-e29b-41d4-a716-446655440000",
            "description": "Test optimization with constraints",
            "max_combinations": 100,
            "batch_size": 10,
        }

        response = client.post("/v1/optimization/configs", json=config_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Optimization with Constraints"

    def _create_test_config_data(self, name="Test Optimization"):
        """Helper to create test configuration data."""
        return {
            "name": name,
            "ticker": "AAPL",
            "start_date": "2024-09-24T00:00:00Z",
            "end_date": "2025-09-25T00:00:00Z",
            "parameter_ranges": {
                "trigger_threshold": {
                    "min_value": 0.01,
                    "max_value": 0.05,
                    "step_size": 0.01,
                    "parameter_type": "float",
                    "name": "trigger_threshold",
                    "description": "Price movement percentage that triggers a rebalancing trade",
                }
            },
            "optimization_criteria": {
                "primary_metric": "total_return",
                "secondary_metrics": ["sharpe_ratio"],
                "constraints": [],
                "weights": {"total_return": 1.0, "sharpe_ratio": 0.5},
                "minimize": False,
                "description": "",
            },
            "created_by": "550e8400-e29b-41d4-a716-446655440000",
            "description": "Test optimization configuration",
            "max_combinations": 100,
            "batch_size": 10,
        }
