export interface BTCPrice {
  price: number;
  change_24h: number;
  market_cap: number;
  volume: number;
}

export interface BTCHistoricalRow {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  source: string;
  sma_7?: number;
  sma_21?: number;
  sma_50?: number;
  ema_12?: number;
  ema_26?: number;
  rsi_14?: number;
  macd?: number;
  macd_signal?: number;
  bb_mid?: number;
  bb_upper?: number;
  bb_lower?: number;
  daily_return?: number;
  log_return?: number;
  volume_sma?: number;
  volatility?: number;
}
