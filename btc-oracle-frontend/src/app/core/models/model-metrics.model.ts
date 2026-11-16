export interface ModelMetricRow {
  id?: number;
  model_name: string;
  mae: number;
  rmse: number;
  mape: number;
  r2: number;
  evaluated_at: string;
}

export interface ModelStatus {
  prophet: string;
  lstm: string;
  random_forest: string;
}

export interface RetrainResult {
  status: string;
  message: string;
  metrics: {
    prophet?: any;
    lstm?: any;
    random_forest?: any;
  };
}
