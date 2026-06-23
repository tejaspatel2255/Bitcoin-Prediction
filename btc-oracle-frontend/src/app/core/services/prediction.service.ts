import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, catchError, of } from 'rxjs';
import { environment } from '../../../environments/environment';
import { 
  NextDayPrediction, 
  DirectionPrediction, 
  SevenDayForecast, 
  AllPredictions, 
  PredictionHistory 
} from '../models/prediction.model';

@Injectable({
  providedIn: 'root'
})
export class PredictionService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getNextDayPrediction(): Observable<NextDayPrediction> {
    return this.http.get<NextDayPrediction>(`${this.apiUrl}/api/predict/next-day`).pipe(
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
      })
    );
  }

  getDirection(): Observable<DirectionPrediction> {
    return this.http.get<DirectionPrediction>(`${this.apiUrl}/api/predict/direction`).pipe(
      catchError(err => {
        console.error('Error fetching prediction direction:', err);
        return of({
          prediction_date: new Date(Date.now() + 86400000).toISOString().split('T')[0],
          direction: 'UP',
          confidence: 76.5
        } as DirectionPrediction);
      })
    );
  }

  get7DayForecast(): Observable<SevenDayForecast> {
    return this.http.get<SevenDayForecast>(`${this.apiUrl}/api/predict/7-day`).pipe(
      catchError(err => {
        console.error('Error fetching 7-day forecast:', err);
        return of({
          prediction_date: new Date(Date.now() + 86400000).toISOString().split('T')[0],
          forecast: []
        } as SevenDayForecast);
      })
    );
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
    return this.http.get<PredictionHistory[]>(`${this.apiUrl}/api/predict/history?limit=${limit}`).pipe(
      catchError(err => {
        console.error('Error fetching prediction history:', err);
        return of([] as PredictionHistory[]);
      })
    );
  }
}
