import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.services.data_service import merge_and_clean, add_technical_indicators, prepare_ml_features

class TestDataService(unittest.TestCase):
    def setUp(self):
        # Construct a simple daily mock dataset
        self.dates = [datetime.now().date() - timedelta(days=i) for i in range(100, 0, -1)]
        self.mock_data = pd.DataFrame({
            "date": self.dates,
            "open": [60000.0 + i * 100 for i in range(100)],
            "high": [60500.0 + i * 100 for i in range(100)],
            "low": [59500.0 + i * 100 for i in range(100)],
            "close": [60100.0 + i * 100 for i in range(100)],
            "volume": [1e9 + i * 1e6 for i in range(100)],
            "source": ["test_source"] * 100
        })

    def test_merge_and_clean(self):
        # Introduce a duplicate date, a null value, and low outlier
        dirty_df = self.mock_data.copy()
        # Add duplicate row
        dirty_df = pd.concat([dirty_df, dirty_df.iloc[[0]]], ignore_index=True)
        # Add null close
        dirty_df.loc[10, 'close'] = None
        # Add zero close
        dirty_df.loc[20, 'close'] = 0.0
        
        cleaned_df = merge_and_clean(dirty_df)
        
        # Verify deduplication, null removal, and zero removal
        self.assertEqual(len(cleaned_df), 98) # Removed duplicate, null, and zero
        self.assertTrue((cleaned_df['close'] > 0).all())
        self.assertFalse(cleaned_df.duplicated(subset=['date']).any())

    def test_add_technical_indicators(self):
        enriched_df = add_technical_indicators(self.mock_data)
        
        # Ensure all columns required exist and contain float entries (no NaNs left)
        required_cols = [
            "sma_7", "sma_21", "sma_50", "ema_12", "ema_26",
            "rsi_14", "macd", "macd_signal", "bb_mid", "bb_upper",
            "bb_lower", "daily_return", "log_return", "volume_sma", "volatility"
        ]
        
        for col in required_cols:
            self.assertIn(col, enriched_df.columns)
            self.assertFalse(enriched_df[col].isnull().any())
            
    def test_prepare_ml_features(self):
        enriched_df = add_technical_indicators(self.mock_data)
        features_df = prepare_ml_features(enriched_df, target_lead=1)
        
        # Verify target price & direction exist
        self.assertIn("target_price", features_df.columns)
        self.assertIn("target_direction", features_df.columns)
        # Verify direction contains binary values
        self.assertTrue(features_df["target_direction"].isin([0, 1]).all())
        # Verify target_price matches the next day's close price
        self.assertEqual(features_df["target_price"].iloc[0], features_df["close"].iloc[1])

if __name__ == "__main__":
    unittest.main()
