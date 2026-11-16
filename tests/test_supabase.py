import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime

from app.services import supabase_service

class TestSupabaseService(unittest.TestCase):
    @patch("app.services.supabase_service.supabase")
    def test_insert_historical_data_mock(self, mock_supabase):
        # Setup mock behavior
        mock_execute = MagicMock()
        mock_execute.execute.return_value = MagicMock(data=[{"date": "2026-06-22", "close": 64000.0}])
        mock_supabase.table.return_value = mock_execute
        
        # Call function under test
        df = pd.DataFrame([{
            "date": datetime.now().date(),
            "open": 63000.0,
            "high": 65000.0,
            "low": 62000.0,
            "close": 64000.0,
            "volume": 1.5e10,
            "source": "yfinance"
        }])
        
        res = supabase_service.insert_historical_data(df)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["count"], 1)

    @patch("app.services.supabase_service.supabase")
    def test_get_historical_data_mock(self, mock_supabase):
        # Setup mock table response
        mock_execute = MagicMock()
        mock_execute.select.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[
                {"date": "2026-06-22", "open": 63000.0, "high": 65000.0, "low": 62000.0, "close": 64000.0, "volume": 1.5e10, "source": "yfinance"}
            ]
        )
        mock_supabase.table.return_value = mock_execute
        
        df = supabase_service.get_historical_data(days=1)
        self.assertFalse(df.empty)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["close"], 64000.0)

    @patch("app.services.supabase_service.supabase")
    def test_insert_prediction_mock(self, mock_supabase):
        mock_execute = MagicMock()
        mock_execute.insert.return_value.execute.return_value = MagicMock(data=[{"id": 1}])
        mock_supabase.table.return_value = mock_execute
        
        pred_record = {
            "model_used": "ensemble",
            "prediction_type": "price_forecast_1d",
            "predicted_value": 65000.0,
            "prediction_date": "2026-06-22"
        }
        res = supabase_service.insert_prediction(pred_record)
        self.assertEqual(res["status"], "success")

if __name__ == "__main__":
    unittest.main()
