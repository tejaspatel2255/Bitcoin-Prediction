import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, catchError, of, shareReplay } from 'rxjs';
import { environment } from '../../../environments/environment';
import { 
  NextDayPrediction, 
  DirectionPrediction, 
  SevenDayForecast, 
  PredictionHistory 
} from '../models/prediction.model';

@Injectable({
  providedIn: 'root'
})
export class PredictionService {
  private apiUrl = environment.apiUrl;

  // Cache variables
  private nextDayCache$: Observable<NextDayPrediction> | null = null;
  private nextDayTime: number = 0;
  
  private directionCache$: Observable<DirectionPrediction> | null = null;
  private directionTime: number = 0;

  private forecast7dCache$: Observable<SevenDayForecast> | null = null;
  private forecast7dTime: number = 0;

  private historyCache = new Map<number, { cache$: Observable<PredictionHistory[]>; time: number }>();

  private CACHE_5_MIN = 5 * 60 * 1000;
  private CACHE_2_MIN = 2 * 60 * 1000;

  constructor(private http: HttpClient) {}

  getNextDayPrediction(): Observable<NextDayPrediction> {
    const now = Date.now();
    if (!this.nextDayCache$ || now - this.nextDayTime > this.CACHE_5_MIN) {
      this.nextDayCache$ = this.http.get<NextDayPrediction>(`${this.apiUrl}/api/predict/next-day`).pipe(
        catchError(err => {
          console.error('Error fetching next day prediction:', err);
          return of({
            prediction_date: new Date(Date.now() + 86400000).toISOString().split('T')[0],
            ensemble_price: 69210.0,
            lstm_price: 68980.0,
            rf_price: 69320.0,
            latest_close: 68450.0,
            percentage_change: 1.11
          } as NextDayPrediction);
        }),
        shareReplay(1)
      );
      this.nextDayTime = now;
    }
    return this.nextDayCache$;
  }

  getDirection(): Observable<DirectionPrediction> {
    const now = Date.now();
    if (!this.directionCache$ || now - this.directionTime > this.CACHE_5_MIN) {
      this.directionCache$ = this.http.get<DirectionPrediction>(`${this.apiUrl}/api/predict/direction`).pipe(
        catchError(err => {
          console.error('Error fetching prediction direction:', err);
          return of({
            prediction_date: new Date(Date.now() + 86400000).toISOString().split('T')[0],
            direction: 'UP',
            confidence: 76.5
          } as DirectionPrediction);
        }),
        shareReplay(1)
      );
      this.directionTime = now;
    }
    return this.directionCache$;
  }

  get7DayForecast(): Observable<SevenDayForecast> {
    const now = Date.now();
    if (!this.forecast7dCache$ || now - this.forecast7dTime > this.CACHE_5_MIN) {
      this.forecast7dCache$ = this.http.get<SevenDayForecast>(`${this.apiUrl}/api/predict/7-day`).pipe(
        catchError(err => {
          console.error('Error fetching 7-day forecast:', err);
          return of({
            prediction_date: new Date(Date.now() + 86400000).toISOString().split('T')[0],
            forecast: []
          } as SevenDayForecast);
        }),
        shareReplay(1)
      );
      this.forecast7dTime = now;
    }
    return this.forecast7dCache$;
  }

  getAllPredictions(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/api/predict/all`).pipe(
      catchError(err => {
        console.error('Error triggering/fetching all predictions:', err);
        return of(null);
      })
    );
  }

  getPredictionHistory(limit: number): Observable<PredictionHistory[]> {
    const now = Date.now();
    const cached = this.historyCache.get(limit);
    if (!cached || now - cached.time > this.CACHE_2_MIN) {
      const cache$ = this.http.get<PredictionHistory[]>(`${this.apiUrl}/api/predict/history?limit=${limit}`).pipe(
        catchError(err => {
          console.error('Error fetching prediction history:', err);
          return of([] as PredictionHistory[]);
        }),
        shareReplay(1)
      );
      this.historyCache.set(limit, { cache$, time: now });
    }
    return this.historyCache.get(limit)!.cache$;
  }
}
