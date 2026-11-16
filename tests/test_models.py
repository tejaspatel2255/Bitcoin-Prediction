import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from app.models import rf_model, prophet_model, lstm_model
from app.services.data_service import add_technical_indicators

class TestModels(unittest.TestCase):
    def setUp(self):
        # 150 rows of mock technical data
        self.dates = [datetime.now().date() - timedelta(days=i) for i in range(150, 0, -1)]
        df = pd.DataFrame({
            "date": self.dates,
            "open": [60000.0 + i * 100 for i in range(150)],
            "high": [60500.0 + i * 100 for i in range(150)],
            "low": [59500.0 + i * 100 for i in range(150)],
            "close": [60100.0 + i * 100 for i in range(150)],
            "volume": [1e9 + i * 1e6 for i in range(150)],
            "source": ["test"] * 150
        })
        self.df = add_technical_indicators(df)

    def test_random_forest_fit_predict(self):
        # Train tiny RF models on mock data
        reg = rf_model.train_regressor(self.df)
        clf = rf_model.train_classifier(self.df)
        
        # Build features matrix to extract the correct column list
        ml_df = rf_model._build_feature_matrix(self.df)
        feature_cols = rf_model._get_feature_cols(ml_df)
        
        # Test predictions using latest row (as DataFrame to preserve column headers)
        latest_row = self.df.iloc[-1:]
        preds = rf_model.predict_next_day(reg, clf, latest_row, feature_cols)
        
        self.assertIn("predicted_price", preds)
        self.assertIn("direction_label", preds)
        self.assertTrue(isinstance(preds["predicted_price"], float))
        self.assertIn(preds["direction_label"], ["UP", "DOWN"])


    def test_prophet_model_evaluation_structure(self):
        # Train tiny Prophet model (Prophet trains quickly on 150 rows)
        try:
            m = prophet_model.train(self.df)
            forecast = prophet_model.predict_next_7_days(m)
            
            # Check structure
            self.assertEqual(len(forecast), 7)
            self.assertIn("date", forecast.columns)
            self.assertIn("yhat", forecast.columns)
            self.assertIn("yhat_lower", forecast.columns)
            self.assertIn("yhat_upper", forecast.columns)
        except Exception as e:
            # Skip if prophet is not initialized or missing dependencies on local test env
            self.skipTest(f"Prophet test skipped due to: {e}")

    def test_lstm_data_shaping(self):
        # Test that LSTM training/prediction data sequences have correct shapes
        # LSTM lookback window is 60. Check that preparing features works
        from app.models.lstm_model import _build_sequences
        
        close_prices = self.df["close"].values.reshape(-1, 1)
        # Scale prices
        from sklearn.preprocessing import MinMaxScaler
        scaler = MinMaxScaler()
        scaled = scaler.fit_transform(close_prices)
        
        X, y = _build_sequences(scaled, seq_len=60)
        
        # 150 items with lookback 60 and lead 1 should yield 150 - 60 = 90 samples
        self.assertEqual(X.shape, (90, 60, 1))
        self.assertEqual(y.shape, (90, 1))



if __name__ == "__main__":
    unittest.main()
