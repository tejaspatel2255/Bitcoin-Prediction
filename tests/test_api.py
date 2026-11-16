import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from fastapi.testclient import TestClient
from main import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "online")

    @patch("app.services.supabase_service.supabase")
    @patch("app.models.model_manager.load_all_models")
    def test_health_endpoint(self, mock_load, mock_supabase):
        mock_load.return_value = {"prophet": "loaded", "lstm": "loaded", "random_forest": "loaded"}
        # Mock Supabase client connection
        mock_supabase.is_mock = False
        
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

    @patch("app.api.routes.data.get_historical_data")
    def test_historical_data_endpoint(self, mock_get_hist):
        # Mock 5 rows of database results
        mock_get_hist.return_value = pd.DataFrame([
            {"date": "2026-06-20", "open": 64000.0, "high": 64500.0, "low": 63800.0, "close": 64200.0, "volume": 1.2e10, "source": "yfinance"},
            {"date": "2026-06-21", "open": 64200.0, "high": 64600.0, "low": 63900.0, "close": 64300.0, "volume": 1.3e10, "source": "yfinance"},
        ])
        response = self.client.get("/api/data/historical?days=2")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.json(), list))

    @patch("app.api.routes.predictions.get_predictions")
    def test_predictions_history_endpoint(self, mock_get_preds):
        mock_get_preds.return_value = [
            {"id": 1, "model_used": "ensemble", "prediction_type": "price_forecast_1d", "predicted_value": 65000.0, "prediction_date": "2026-06-22"}
        ]
        response = self.client.get("/api/predict/history?limit=1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["model_used"], "ensemble")

    @patch("app.api.routes.insights.get_latest_insights")
    def test_insights_history_endpoint(self, mock_get_insights):
        mock_get_insights.return_value = [
            {"id": 1, "prompt_type": "market_summary", "response_text": "Bullish consolidations."}
        ]
        response = self.client.get("/api/insights/history?limit=1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["prompt_type"], "market_summary")

    @patch("app.api.routes.models.get_model_metrics")
    def test_models_metrics_endpoint(self, mock_get_metrics):
        mock_get_metrics.return_value = [
            {"id": 1, "model_name": "random_forest", "mae": 450.0, "rmse": 600.0, "mape": 0.72, "r2": 0.93}
        ]
        response = self.client.get("/api/models/metrics?limit=1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["model_name"], "random_forest")

if __name__ == "__main__":
    unittest.main()
