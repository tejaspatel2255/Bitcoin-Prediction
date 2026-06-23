export interface Insight {
  id?: number;
  created_at: string;
  prompt_type: string;
  response_text: string;
}

export interface FullReport {
  market_summary: string;
  prediction_explanation: string;
  risk_analysis: string;
  seven_day_outlook: string;
}
