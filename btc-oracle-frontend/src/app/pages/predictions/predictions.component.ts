import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgChartsModule } from 'ng2-charts';
import { ChartConfiguration } from 'chart.js';
import { TopbarComponent } from '../../shared/components/topbar/topbar.component';
import { PredictionCardComponent } from '../../shared/components/prediction-card/prediction-card.component';
import { PredictionService } from '../../core/services/prediction.service';
import { lastValueFrom } from 'rxjs';
import { CurrencyFormatPipe } from '../../shared/pipes/currency-format.pipe';
import { PercentFormatPipe } from '../../shared/pipes/percent-format.pipe';
import { BTC_ORANGE, BULL_GREEN, BEAR_RED } from '../../core/chart-config';

@Component({
  selector: 'app-predictions',
  standalone: true,
  imports: [
    CommonModule,
    NgChartsModule,
    TopbarComponent,
    PredictionCardComponent,
    CurrencyFormatPipe,
    PercentFormatPipe
  ],
  templateUrl: './predictions.component.html',
  styleUrl: './predictions.component.scss'
})
export class PredictionsComponent implements OnInit {
  lastUpdatedTime = signal<string>('Just now');
  
  // Model Predictions
  ensemblePred = signal<any>({ predicted: 69210, low: 67800, high: 70600, direction: 'Bullish', confidence: 76.5 });
  lstmPred = signal<any>({ predicted: 68980, low: 67600, high: 70300, direction: 'Bullish', confidence: 68.0 });
  rfPred = signal<any>({ predicted: 69320, low: 67900, high: 70700, direction: 'Bullish', confidence: 81.2 });

  predictionHistory = signal<any[]>([]);

  // Gauge configurations
  gaugeData: any = { datasets: [] };
  gaugeOptions: ChartConfiguration<'doughnut'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '80%',
    rotation: -90,
    circumference: 180,
    plugins: {
      legend: { display: false },
      tooltip: { enabled: false }
    }
  };

  constructor(private predictionService: PredictionService) {}

  async ngOnInit() {
    await this.loadPredictionDetails();
  }

  private async loadPredictionDetails() {
    try {
      const pred = await lastValueFrom(this.predictionService.getNextDayPrediction());
      const dir = await lastValueFrom(this.predictionService.getDirection());
      const hist = await lastValueFrom(this.predictionService.getPredictionHistory(10));

      if (pred) {
        // Compute ranges
        const devPct = 0.02; // 2% deviation boundary
        this.ensemblePred.set({
          predicted: pred.ensemble_price,
          low: pred.ensemble_price * (1 - devPct),
          high: pred.ensemble_price * (1 + devPct),
          direction: pred.ensemble_price >= pred.latest_close ? 'Bullish' : 'Bearish',
          confidence: dir?.confidence || 76.5
        });

        this.lstmPred.set({
          predicted: pred.lstm_price,
          low: pred.lstm_price * (1 - devPct),
          high: pred.lstm_price * (1 + devPct),
          direction: pred.lstm_price >= pred.latest_close ? 'Bullish' : 'Bearish',
          confidence: 68.0
        });

        this.rfPred.set({
          predicted: pred.rf_price,
          low: pred.rf_price * (1 - devPct),
          high: pred.rf_price * (1 + devPct),
          direction: pred.rf_price >= pred.latest_close ? 'Bullish' : 'Bearish',
          confidence: 81.2
        });

        // Set up the gauge doughnut datasets
        const conf = dir?.confidence || 76.5;
        this.gaugeData = {
          labels: ['Confidence', 'Remaining'],
          datasets: [
            {
              data: [conf, 100 - conf],
              backgroundColor: [BTC_ORANGE, '#F0F0F0'],
              borderWidth: 0,
              borderRadius: 4
            }
          ]
        };
      }

      if (hist && hist.length > 0) {
        // Format history rows with computed absolute error percentages
        const formatted = hist.map(h => {
          const err = h.actual_value 
            ? ((Math.abs(h.predicted_value - h.actual_value) / h.actual_value) * 100) 
            : null;
          return {
            ...h,
            error_pct: err
          };
        });
        this.predictionHistory.set(formatted);
      }

      this.lastUpdatedTime.set(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Error loading prediction details page:', err);
    }
  }
}
