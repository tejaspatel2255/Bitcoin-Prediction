import { Component, OnInit, signal, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgChartsModule } from 'ng2-charts';
import { ChartConfiguration, ChartType } from 'chart.js';
import { TopbarComponent } from '../../shared/components/topbar/topbar.component';
import { PredictionCardComponent } from '../../shared/components/prediction-card/prediction-card.component';
import { BitcoinService } from '../../core/services/bitcoin.service';
import { PredictionService } from '../../core/services/prediction.service';
import { lastValueFrom } from 'rxjs';
import { DARK_CHART_DEFAULTS, BTC_ORANGE, BULL_GREEN } from '../../core/chart-config';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    NgChartsModule,
    TopbarComponent,
    PredictionCardComponent
  ],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent implements OnInit {
  selectedRange = signal<string>('90D');
  lastUpdatedTime = signal<string>('Just now');
  
  nextDayPred = signal<any>({
    predicted: 69210.0,
    low: 67800.0,
    high: 70600.0,
    direction: 'Bullish',
    confidence: 76.5
  });

  forecastStats = signal<any>({
    targetPrice: 70500,
    changePct: 3.12
  });

  isLoadingChart = signal<boolean>(true);

  // Chart configs
  mainChartData: ChartConfiguration['data'] = { datasets: [] };
  mainChartOptions: ChartConfiguration['options'] = {
    ...DARK_CHART_DEFAULTS,
    scales: {
      x: { grid: { color: '#F0F0F0' }, ticks: { color: '#888' } },
      y: { 
        position: 'left',
        grid: { color: '#F0F0F0' }, 
        ticks: { color: '#888' } 
      },
      yVolume: {
        position: 'right',
        grid: { display: false },
        ticks: { display: false },
        max: 100000000000 // scale down volume bars
      }
    }
  };

  miniChartData: ChartConfiguration['data'] = { datasets: [] };
  miniChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: { enabled: false } },
    scales: { x: { display: false }, y: { display: false } }
  };

  constructor(
    private bitcoinService: BitcoinService,
    private predictionService: PredictionService
  ) {
    // Re-fetch historical data when range signal changes
    effect(async () => {
      await this.loadChartDataForRange(this.selectedRange());
    });
  }

  async ngOnInit() {
    await this.loadPredictions();
  }

  setRange(range: string) {
    this.selectedRange.set(range);
  }

  private async loadPredictions() {
    try {
      const pred = await lastValueFrom(this.predictionService.getNextDayPrediction());
      const dir = await lastValueFrom(this.predictionService.getDirection());
      const f7d = await lastValueFrom(this.predictionService.get7DayForecast());

      if (pred) {
        this.nextDayPred.set({
          predicted: pred.ensemble_price,
          low: pred.ensemble_price * 0.98,
          high: pred.ensemble_price * 1.02,
          direction: dir?.direction === 'UP' ? 'Bullish' : 'Bearish',
          confidence: dir?.confidence || 76.5
        });
      }

      if (f7d && f7d.forecast && f7d.forecast.length > 0) {
        const lastDay = f7d.forecast[f7d.forecast.length - 1];
        const initialPrice = pred?.latest_close || 68450.0;
        const change = ((lastDay.yhat - initialPrice) / initialPrice) * 100;
        
        this.forecastStats.set({
          targetPrice: lastDay.yhat,
          changePct: change
        });

        // Set up the mini trend chart
        const labels = f7d.forecast.map(d => d.date);
        const yhats = f7d.forecast.map(d => d.yhat);
        const uppers = f7d.forecast.map(d => d.yhat_upper);
        const lowers = f7d.forecast.map(d => d.yhat_lower);

        this.miniChartData = {
          labels,
          datasets: [
            {
              data: yhats,
              borderColor: BULL_GREEN,
              borderWidth: 2,
              pointRadius: 0,
              fill: false,
              tension: 0.3
            },
            {
              data: uppers,
              borderColor: 'rgba(76, 175, 80, 0.05)',
              pointRadius: 0,
              fill: '+1', // fill down to lower dataset
              backgroundColor: 'rgba(76, 175, 80, 0.06)',
            },
            {
              data: lowers,
              borderColor: 'rgba(76, 175, 80, 0.05)',
              pointRadius: 0,
              fill: false
            }
          ]
        };
      }
      this.lastUpdatedTime.set(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Error loading dashboard predictions:', err);
    }
  }

  private async loadChartDataForRange(range: string) {
    this.isLoadingChart.set(true);
    let days = 90;
    if (range === '7D') days = 7;
    if (range === '30D') days = 30;
    if (range === '90D') days = 90;
    if (range === '1Y') days = 365;

    try {
      const data = await lastValueFrom(this.bitcoinService.getHistoricalData(days));
      if (data && data.length > 0) {
        const labels = data.map(d => new Date(d.date).toLocaleDateString());
        const closes = data.map(d => d.close);
        const volumes = data.map(d => d.volume);
        
        const sma7 = data.map(d => d.sma_7 || null);
        const sma21 = data.map(d => d.sma_21 || null);
        const bbUpper = data.map(d => d.bb_upper || null);
        const bbLower = data.map(d => d.bb_lower || null);

        // Adjust Y scale volume max to match actual volumes
        const maxVol = Math.max(...volumes);
        if (this.mainChartOptions && this.mainChartOptions.scales && this.mainChartOptions.scales['yVolume']) {
          this.mainChartOptions.scales['yVolume'].max = maxVol * 4; // volume stays in lower quarter
        }

        this.mainChartData = {
          labels,
          datasets: [
            {
              type: 'line',
              label: 'Close Price',
              data: closes,
              borderColor: '#1A1A1A',
              borderWidth: 2.5,
              pointRadius: 0,
              yAxisID: 'y'
            },
            {
              type: 'line',
              label: 'SMA 7',
              data: sma7,
              borderColor: '#888888',
              borderWidth: 1,
              borderDash: [2, 2],
              pointRadius: 0,
              yAxisID: 'y'
            },
            {
              type: 'line',
              label: 'SMA 21',
              data: sma21,
              borderColor: BTC_ORANGE,
              borderWidth: 1,
              pointRadius: 0,
              yAxisID: 'y'
            },
            {
              type: 'line',
              label: 'BB Upper',
              data: bbUpper,
              borderColor: '#9C27B0',
              borderWidth: 1,
              borderDash: [5, 5],
              pointRadius: 0,
              yAxisID: 'y'
            },
            {
              type: 'line',
              label: 'BB Lower',
              data: bbLower,
              borderColor: '#9C27B0',
              borderWidth: 1,
              borderDash: [5, 5],
              pointRadius: 0,
              yAxisID: 'y'
            },
            {
              type: 'bar',
              label: 'Volume',
              data: volumes,
              backgroundColor: 'rgba(247, 147, 26, 0.25)',
              yAxisID: 'yVolume'
            }
          ]
        };
      }
    } catch (err) {
      console.error('Error fetching historical chart data:', err);
    } finally {
      this.isLoadingChart.set(false);
    }
  }
}
