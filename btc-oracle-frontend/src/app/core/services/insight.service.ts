import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, catchError, of } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Insight, FullReport } from '../models/insight.model';

@Injectable({
  providedIn: 'root'
})
export class InsightService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getMarketSummary(): Observable<Insight> {
    return this.http.get<Insight>(`${this.apiUrl}/api/insights/summary`).pipe(
      catchError(err => {
        console.error('Error fetching market summary:', err);
        return of({
          created_at: new Date().toISOString(),
          prompt_type: 'market_summary',
          response_text: 'Bitcoin is consolidating support above SMA 21 levels.'
        } as Insight);
      })
    );
  }

  getRiskAnalysis(): Observable<Insight> {
    return this.http.get<Insight>(`${this.apiUrl}/api/insights/risk`).pipe(
      catchError(err => {
        console.error('Error fetching risk analysis:', err);
        return of({
          created_at: new Date().toISOString(),
          prompt_type: 'risk_analysis',
          response_text: 'Overall risk is currently rated as Medium with stable volatility.'
        } as Insight);
      })
    );
  }

  get7DayOutlook(): Observable<Insight> {
    // 7-day outlook uses /api/insights/outlook or full-report based on backend endpoints
    return this.http.get<Insight>(`${this.apiUrl}/api/insights/outlook`).pipe(
      catchError(err => {
        console.error('Error fetching 7-day outlook:', err);
        return of({
          created_at: new Date().toISOString(),
          prompt_type: 'seven_day_outlook',
          response_text: 'Outlook remains cautiously bullish targeting a high of $70,500.'
        } as Insight);
      })
    );
  }

  getFullReport(): Observable<FullReport> {
    return this.http.get<FullReport>(`${this.apiUrl}/api/insights/full-report`).pipe(
      catchError(err => {
        console.error('Error fetching full report:', err);
        return of({
          market_summary: 'Bitcoin (BTC) is consolidating around the $68,450 support levels. Indicators are pointing to a positive bias.',
          prediction_explanation: "Tomorrow's ensemble model predicts a target price of $69,210 (+1.11%).",
          risk_analysis: 'The technical risk is currently assessed as MEDIUM. Support holds firm above SMA 21.',
          seven_day_outlook: 'Prophet projections indicate a steady target peak of $71,200 with an overall BULLISH outlook.'
        } as FullReport);
      })
    );
  }

  getInsightHistory(limit: number): Observable<Insight[]> {
    return this.http.get<Insight[]>(`${this.apiUrl}/api/insights/history?limit=${limit}`).pipe(
      catchError(err => {
        console.error('Error fetching insights history:', err);
        return of([] as Insight[]);
      })
    );
  }

  refreshInsightSegment(segment: string): Observable<Insight> {
    return this.http.get<Insight>(`${this.apiUrl}/api/insights/${segment}`).pipe(
      catchError(err => {
        console.error(`Error refreshing insight segment ${segment}:`, err);
        return of({
          created_at: new Date().toISOString(),
          prompt_type: segment,
          response_text: `Failed to refresh ${segment}. Backend offline.`
        } as Insight);
      })
    );
  }
}
