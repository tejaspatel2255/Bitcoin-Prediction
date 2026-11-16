export interface NextDayPrediction {
  prediction_date: string;
  ensemble_price: number;
  lstm_price: number;
  rf_price: number;
  latest_close: number;
  percentage_change: number;
}

export interface DirectionPrediction {
  prediction_date: string;
  direction: 'UP' | 'DOWN';
  confidence: number;
}

export interface ForecastDay {
  date: string;
  yhat: number;
  yhat_lower: number;
  yhat_upper: number;
}

export interface SevenDayForecast {
  prediction_date: string;
  forecast: ForecastDay[];
}

export interface PredictionHistory {
  prediction_date: string;
  model_used: string;
  prediction_type: string;
  predicted_value: number;
  actual_value: number;
  confidence_score: number;
  error_pct?: number;
}

export interface AllPredictions {
  next_day: NextDayPrediction;
  direction: DirectionPrediction;
  forecast_7d: SevenDayForecast;
}
