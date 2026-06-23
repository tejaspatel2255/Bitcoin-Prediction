import { Component, OnInit, OnDestroy, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TopbarComponent } from '../../shared/components/topbar/topbar.component';
import { MetricCardComponent } from '../../shared/components/metric-card/metric-card.component';
import { InsightCardComponent } from '../../shared/components/insight-card/insight-card.component';
import { ModelCardComponent } from '../../shared/components/model-card/model-card.component';
import { BitcoinService } from '../../core/services/bitcoin.service';
import { InsightService } from '../../core/services/insight.service';
import { ModelService } from '../../core/services/model.service';
import { CurrencyFormatPipe } from '../../shared/pipes/currency-format.pipe';
import { PercentFormatPipe } from '../../shared/pipes/percent-format.pipe';
import { lastValueFrom, Subscription, interval } from 'rxjs';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [
    CommonModule,
    TopbarComponent,
    MetricCardComponent,
    InsightCardComponent,
    ModelCardComponent,
    CurrencyFormatPipe,
    PercentFormatPipe
  ],
  templateUrl: './home.component.html',
  styleUrl: './home.component.scss'
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

  private refreshSub?: Subscription;

  constructor(
    private bitcoinService: BitcoinService,
    private insightService: InsightService,
    private modelService: ModelService
  ) {}

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

      this.lastUpdatedTime.set(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Error fetching home page data:', err);
    } finally {
      this.isLoadingMetrics.set(false);
      this.isLoadingInsights.set(false);
    }
  }

  async refreshMetrics() {
    try {
      const priceRes = await lastValueFrom(this.bitcoinService.getLivePrice());
      if (priceRes) this.btcPrice.set(priceRes);
      this.lastUpdatedTime.set(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Error refreshing metrics:', err);
    }
  }

  async refreshInsightSegment(segment: string) {
    this.isLoadingInsights.set(true);
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
    }
  }
}
