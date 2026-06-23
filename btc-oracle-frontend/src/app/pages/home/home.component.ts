import { Component, OnInit, OnDestroy, signal, effect, ChangeDetectionStrategy, ChangeDetectorRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TopbarComponent } from '../../shared/components/topbar/topbar.component';
import { MetricCardComponent } from '../../shared/components/metric-card/metric-card.component';
import { InsightCardComponent } from '../../shared/components/insight-card/insight-card.component';
import { ModelCardComponent } from '../../shared/components/model-card/model-card.component';
import { NgChartsModule } from 'ng2-charts';
import { ChartConfiguration } from 'chart.js';
import { BitcoinService } from '../../core/services/bitcoin.service';
import { InsightService } from '../../core/services/insight.service';
import { ModelService } from '../../core/services/model.service';
import { PredictionService } from '../../core/services/prediction.service';
import { CurrencyFormatPipe } from '../../shared/pipes/currency-format.pipe';
import { PercentFormatPipe } from '../../shared/pipes/percent-format.pipe';
import { lastValueFrom, Subscription, interval } from 'rxjs';
import { DARK_CHART_DEFAULTS, BULL_GREEN } from '../../core/chart-config';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [
    CommonModule,
    TopbarComponent,
    MetricCardComponent,
    InsightCardComponent,
    ModelCardComponent,
    NgChartsModule,
    CurrencyFormatPipe,
    PercentFormatPipe
  ],
  templateUrl: './home.component.html',
  styleUrl: './home.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class HomeComponent implements OnInit, OnDestroy {
  // Signals for state
  btcPrice = signal<any>({ price: 0, change_24h: 0, market_cap: 0, volume: 0 });
  rsiVal = signal<number>(54.3);
  insights = signal<any>({ market_summary: '', risk_analysis: '', seven_day_outlook: '' });
  modelAccuracies = signal<any>({ prophet: 91.2, random_forest: 93.8, lstm: 94.5 });
  lastUpdatedTime = signal<string>('Just now');
  
  isLoadingMetrics = signal<boolean>(true);
  isLoadingInsights = signal<boolean>(true);

  // Range and Chart Signals
  selectedRange = signal<string>('90D');
  isLoadingChart = signal<boolean>(true);

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

  // Chart configurations
  mainChartData: ChartConfiguration['data'] = { datasets: [] };
  mainChartOptions: ChartConfiguration['options'] = {
    ...DARK_CHART_DEFAULTS,
    scales: {
      x: { grid: { color: '#E5E7EB' }, ticks: { color: '#6B7280' } },
      y: { 
        position: 'left',
        grid: { color: '#E5E7EB' }, 
        ticks: { color: '#6B7280' } 
      },
      yVolume: {
        position: 'right',
        grid: { display: false },
        ticks: { display: false },
        max: 100000000000
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

  private refreshSub?: Subscription;
  private cdr = inject(ChangeDetectorRef);

  constructor(
    private bitcoinService: BitcoinService,
    private insightService: InsightService,
    private modelService: ModelService,
    private predictionService: PredictionService
  ) {
    // Re-fetch historical chart data on range change
    effect(async () => {
      await this.loadChartDataForRange(this.selectedRange());
    }, { allowSignalWrites: true });
  }

  async ngOnInit() {
    await this.fetchInitialData();

    // Auto-refresh metrics every 60s
    this.refreshSub = interval(60000).subscribe(() => {
      this.refreshMetrics();
    });
  }

  ngOnDestroy() {
    if (this.refreshSub) {
      this.refreshSub.unsubscribe();
    }
  }

  private async fetchInitialData() {
    this.isLoadingMetrics.set(true);
    this.isLoadingInsights.set(true);
    this.cdr.markForCheck();

    try {
      // 1. Fetch live metrics
      const priceRes = await lastValueFrom(this.bitcoinService.getLivePrice());
      if (priceRes) this.btcPrice.set(priceRes);

      // 2. Fetch latest RSI from historical data
      const histData = await lastValueFrom(this.bitcoinService.getHistoricalData(2));
      if (histData && histData.length > 0) {
        const latestRow = histData[histData.length - 1];
        if (latestRow.rsi_14 !== undefined) {
          this.rsiVal.set(latestRow.rsi_14);
        }
      }

      // 3. Fetch latest AI insights
      const report = await lastValueFrom(this.insightService.getFullReport());
      if (report) this.insights.set(report);

      // 4. Fetch Model metrics
      const metrics = await lastValueFrom(this.modelService.getModelMetrics());
      if (metrics && metrics.length > 0) {
        const accMap: any = { prophet: 91.2, random_forest: 93.8, lstm: 94.5 };
        metrics.forEach(m => {
          accMap[m.model_name] = Number((100 - m.mape).toFixed(1));
        });
        this.modelAccuracies.set(accMap);
      }

      // 5. Fetch Predictions and Forecast
      await this.loadPredictions();

      this.lastUpdatedTime.set(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Error fetching home page data:', err);
    } finally {
      this.isLoadingMetrics.set(false);
      this.isLoadingInsights.set(false);
      this.cdr.markForCheck();
    }
  }

  async loadPredictions() {
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
          confidence: dir?.confidence || 73.0
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
              borderWidth: 2.1,
              pointRadius: 0,
              fill: false,
              tension: 0.3
            },
            {
              data: uppers,
              borderColor: 'rgba(16, 185, 129, 0.04)',
              pointRadius: 0,
              fill: '+1',
              backgroundColor: 'rgba(16, 185, 129, 0.05)',
            },
            {
              data: lowers,
              borderColor: 'rgba(16, 185, 129, 0.04)',
              pointRadius: 0,
              fill: false
            }
          ]
        };
      }
      this.cdr.markForCheck();
    } catch (err) {
      console.error('Error loading home predictions:', err);
    }
  }

  async loadChartDataForRange(range: string) {
    this.isLoadingChart.set(true);
    this.cdr.markForCheck();
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
        
        const sma21 = data.map(d => d.sma_21 || null);
        const bbUpper = data.map(d => d.bb_upper || null);
        const bbLower = data.map(d => d.bb_lower || null);

        const maxVol = Math.max(...volumes);
        if (this.mainChartOptions && this.mainChartOptions.scales && this.mainChartOptions.scales['yVolume']) {
          this.mainChartOptions.scales['yVolume'].max = maxVol * 4;
        }

        // Setup chart style with elegant gradient under price
        this.mainChartData = {
          labels,
          datasets: [
            {
              type: 'line',
              label: 'Price',
              data: closes,
              borderColor: '#F59E0B',
              backgroundColor: 'rgba(245, 158, 11, 0.05)',
              borderWidth: 2.5,
              pointRadius: 0,
              fill: true,
              tension: 0.15,
              yAxisID: 'y'
            },
            {
              type: 'line',
              label: 'SMA',
              data: sma21,
              borderColor: '#6B7280',
              borderWidth: 1.2,
              pointRadius: 0,
              fill: false,
              tension: 0.1,
              yAxisID: 'y'
            },
            {
              type: 'line',
              label: 'BB Upper',
              data: bbUpper,
              borderColor: 'rgba(139, 92, 246, 0.4)',
              borderWidth: 1,
              borderDash: [4, 4],
              pointRadius: 0,
              fill: false,
              yAxisID: 'y'
            },
            {
              type: 'line',
              label: 'BB Lower',
              data: bbLower,
              borderColor: 'rgba(139, 92, 246, 0.4)',
              borderWidth: 1,
              borderDash: [4, 4],
              pointRadius: 0,
              fill: false,
              yAxisID: 'y'
            },
            {
              type: 'bar',
              label: 'Volume',
              data: volumes,
              backgroundColor: 'rgba(16, 185, 129, 0.12)',
              yAxisID: 'yVolume'
            }
          ]
        };
      }
    } catch (err) {
      console.error('Error loading home chart:', err);
    } finally {
      this.isLoadingChart.set(false);
      this.cdr.markForCheck();
    }
  }

  setRange(range: string) {
    this.selectedRange.set(range);
  }

  async refreshMetrics() {
    try {
      const priceRes = await lastValueFrom(this.bitcoinService.getLivePrice());
      if (priceRes) this.btcPrice.set(priceRes);
      this.lastUpdatedTime.set(new Date().toLocaleTimeString());
      this.cdr.markForCheck();
    } catch (err) {
      console.error('Error refreshing metrics:', err);
    }
  }

  async refreshInsightSegment(segment: string) {
    this.isLoadingInsights.set(true);
    this.cdr.markForCheck();
    try {
      const res = await lastValueFrom(this.insightService.refreshInsightSegment(segment));
      if (res && res.response_text) {
        const currentInsights = { ...this.insights() };
        if (segment === 'summary') currentInsights.market_summary = res.response_text;
        if (segment === 'risk') currentInsights.risk_analysis = res.response_text;
        if (segment === 'outlook' || segment === 'full-report') currentInsights.seven_day_outlook = res.response_text;
        this.insights.set(currentInsights);
      }
    } catch (err) {
      console.error(`Error refreshing insight segment ${segment}:`, err);
    } finally {
      this.isLoadingInsights.set(false);
      this.cdr.markForCheck();
    }
  }
}
