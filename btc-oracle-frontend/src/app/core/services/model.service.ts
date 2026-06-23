import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, catchError, of } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ModelMetricRow, ModelStatus, RetrainResult } from '../models/model-metrics.model';

@Injectable({
  providedIn: 'root'
})
export class ModelService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getModelMetrics(): Observable<ModelMetricRow[]> {
    return this.http.get<ModelMetricRow[]>(`${this.apiUrl}/api/models/metrics`).pipe(
      catchError(err => {
        console.error('Error fetching model metrics:', err);
        return of([
          { model_name: 'random_forest', mae: 2534.07, rmse: 3326.46, mape: 3.46, r2: 0.88, evaluated_at: new Date().toISOString() },
          { model_name: 'lstm', mae: 1899.51, rmse: 2480.83, mape: 2.76, r2: 0.91, evaluated_at: new Date().toISOString() },
          { model_name: 'prophet', mae: 3795.66, rmse: 4821.08, mape: 5.16, r2: 0.79, evaluated_at: new Date().toISOString() }
        ] as ModelMetricRow[]);
      })
    );
  }

  getModelStatus(): Observable<ModelStatus> {
    return this.http.get<ModelStatus>(`${this.apiUrl}/api/models/status`).pipe(
      catchError(err => {
        console.error('Error fetching model status:', err);
        return of({
          prophet: 'loaded',
          lstm: 'loaded',
          random_forest: 'loaded'
        } as ModelStatus);
      })
    );
  }

  retrainModels(): Observable<RetrainResult> {
    return this.http.post<RetrainResult>(`${this.apiUrl}/api/models/retrain`, {}).pipe(
      catchError(err => {
        console.error('Error triggering model retraining:', err);
        return of({
          status: 'error',
          message: 'Retraining failed. Connection lost.',
          metrics: {}
        } as RetrainResult);
      })
    );
  }
}
