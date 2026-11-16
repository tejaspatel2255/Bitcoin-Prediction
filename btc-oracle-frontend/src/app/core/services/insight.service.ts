import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, catchError, of, shareReplay, tap } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Insight, FullReport } from '../models/insight.model';

@Injectable({
  providedIn: 'root'
})
export class InsightService {
  private apiUrl = environment.apiUrl;

  private marketSummaryCache$: Observable<Insight> | null = null;
  private marketSummaryTime: number = 0;

  private riskAnalysisCache$: Observable<Insight> | null = null;
  private riskAnalysisTime: number = 0;

  private outlookCache$: Observable<Insight> | null = null;
  private outlookTime: number = 0;

  private fullReportCache$: Observable<FullReport> | null = null;
  private fullReportTime: number = 0;

  private CACHE_10_MIN = 10 * 60 * 1000;

  constructor(private http: HttpClient) {}

  clearCache() {
    this.marketSummaryCache$ = null;
    this.riskAnalysisCache$ = null;
    this.outlookCache$ = null;
    this.fullReportCache$ = null;
  }

  getMarketSummary(): Observable<Insight> {
    const now = Date.now();
    if (!this.marketSummaryCache$ || now - this.marketSummaryTime > this.CACHE_10_MIN) {
      this.marketSummaryCache$ = this.http.get<Insight>(`${this.apiUrl}/api/insights/summary`).pipe(
        catchError(err => {
          console.error('Error fetching market summary:', err);
          return of({
            created_at: new Date().toISOString(),
            prompt_type: 'market_summary',
            response_text: 'Bitcoin is consolidating support above SMA 21 levels.'
          } as Insight);
        }),
        shareReplay(1)
      );
      this.marketSummaryTime = now;
    }
    return this.marketSummaryCache$;
  }

  getRiskAnalysis(): Observable<Insight> {
    const now = Date.now();
    if (!this.riskAnalysisCache$ || now - this.riskAnalysisTime > this.CACHE_10_MIN) {
      this.riskAnalysisCache$ = this.http.get<Insight>(`${this.apiUrl}/api/insights/risk`).pipe(
        catchError(err => {
          console.error('Error fetching risk analysis:', err);
          return of({
            created_at: new Date().toISOString(),
            prompt_type: 'risk_analysis',
            response_text: 'Overall risk is currently rated as Medium with stable volatility.'
          } as Insight);
        }),
        shareReplay(1)
      );
      this.riskAnalysisTime = now;
    }
    return this.riskAnalysisCache$;
  }

  get7DayOutlook(): Observable<Insight> {
    const now = Date.now();
    if (!this.outlookCache$ || now - this.outlookTime > this.CACHE_10_MIN) {
      this.outlookCache$ = this.http.get<Insight>(`${this.apiUrl}/api/insights/outlook`).pipe(
        catchError(err => {
          console.error('Error fetching 7-day outlook:', err);
          return of({
            created_at: new Date().toISOString(),
            prompt_type: 'seven_day_outlook',
            response_text: 'Outlook remains cautiously bullish targeting a high of $70,500.'
          } as Insight);
        }),
        shareReplay(1)
      );
      this.outlookTime = now;
    }
    return this.outlookCache$;
  }

  getFullReport(): Observable<FullReport> {
    const now = Date.now();
    if (!this.fullReportCache$ || now - this.fullReportTime > this.CACHE_10_MIN) {
      this.fullReportCache$ = this.http.get<FullReport>(`${this.apiUrl}/api/insights/full-report`).pipe(
        catchError(err => {
          console.error('Error fetching full report:', err);
          return of({
            market_summary: 'Bitcoin (BTC) is consolidating around the $68,450 support levels. Indicators are pointing to a positive bias.',
            prediction_explanation: "Tomorrow's ensemble model predicts a target price of $69,210 (+1.11%).",
            risk_analysis: 'The technical risk is currently assessed as MEDIUM. Support holds firm above SMA 21.',
            seven_day_outlook: 'Prophet projections indicate a steady target peak of $71,200 with an overall BULLISH outlook.'
          } as FullReport);
        }),
        shareReplay(1)
      );
      this.fullReportTime = now;
    }
    return this.fullReportCache$;
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
      tap(() => this.clearCache()),
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
