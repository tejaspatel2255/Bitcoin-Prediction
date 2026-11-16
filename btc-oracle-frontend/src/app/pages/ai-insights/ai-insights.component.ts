import { Component, OnInit, signal, ChangeDetectionStrategy, ChangeDetectorRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TopbarComponent } from '../../shared/components/topbar/topbar.component';
import { InsightCardComponent } from '../../shared/components/insight-card/insight-card.component';
import { InsightService } from '../../core/services/insight.service';
import { lastValueFrom } from 'rxjs';

@Component({
  selector: 'app-ai-insights',
  standalone: true,
  imports: [
    CommonModule,
    TopbarComponent,
    InsightCardComponent
  ],
  templateUrl: './ai-insights.component.html',
  styleUrl: './ai-insights.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class AiInsightsComponent implements OnInit {
  lastUpdatedTime = signal<string>('Just now');
  
  marketSummary = signal<string>('');
  predictionExplanation = signal<string>('');
  riskAnalysis = signal<string>('');
  sevenDayOutlook = signal<string>('');

  summaryTimestamp = signal<string>('');
  explainTimestamp = signal<string>('');
  riskTimestamp = signal<string>('');
  outlookTimestamp = signal<string>('');

  loadingMap = signal<Record<string, boolean>>({
    summary: false,
    explain: false,
    risk: false,
    outlook: false,
    all: false
  });

  private cdr = inject(ChangeDetectorRef);

  constructor(private insightService: InsightService) {}

  async ngOnInit() {
    await this.loadAllInsights();
  }

  async loadAllInsights() {
    this.setAllLoading(true);
    try {
      const report = await lastValueFrom(this.insightService.getFullReport());
      if (report) {
        const now = new Date().toLocaleTimeString();
        this.marketSummary.set(report.market_summary);
        this.predictionExplanation.set(report.prediction_explanation);
        this.riskAnalysis.set(report.risk_analysis);
        this.sevenDayOutlook.set(report.seven_day_outlook);

        this.summaryTimestamp.set(now);
        this.explainTimestamp.set(now);
        this.riskTimestamp.set(now);
        this.outlookTimestamp.set(now);
      }
      this.lastUpdatedTime.set(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Error fetching full AI report:', err);
    } finally {
      this.setAllLoading(false);
      this.cdr.markForCheck();
    }
  }

  async refreshInsightSegment(segment: 'summary' | 'explain' | 'risk' | 'outlook') {
    const keyMap: Record<string, string> = {
      summary: 'summary',
      explain: 'explain',
      risk: 'risk',
      outlook: 'outlook'
    };

    const loaderKey = keyMap[segment];
    this.updateLoadingState(loaderKey, true);

    try {
      // Map front-end segment keys to back-end endpoints
      let apiSegment = 'summary';
      if (segment === 'explain') apiSegment = 'prediction-explanation';
      if (segment === 'risk') apiSegment = 'risk';
      if (segment === 'outlook') apiSegment = 'outlook';

      const res = await lastValueFrom(this.insightService.refreshInsightSegment(apiSegment));
      const now = new Date().toLocaleTimeString();

      if (res && res.response_text) {
        if (segment === 'summary') {
          this.marketSummary.set(res.response_text);
          this.summaryTimestamp.set(now);
        } else if (segment === 'explain') {
          this.predictionExplanation.set(res.response_text);
          this.explainTimestamp.set(now);
        } else if (segment === 'risk') {
          this.riskAnalysis.set(res.response_text);
          this.riskTimestamp.set(now);
        } else if (segment === 'outlook') {
          this.sevenDayOutlook.set(res.response_text);
          this.outlookTimestamp.set(now);
        }
      }
    } catch (err) {
      console.error(`Error refreshing segment ${segment}:`, err);
    } finally {
      this.updateLoadingState(loaderKey, false);
      this.cdr.markForCheck();
    }
  }

  private setAllLoading(val: boolean) {
    this.loadingMap.set({
      summary: val,
      explain: val,
      risk: val,
      outlook: val,
      all: val
    });
    this.cdr.markForCheck();
  }

  private updateLoadingState(key: string, val: boolean) {
    const next = { ...this.loadingMap() };
    next[key] = val;
    this.loadingMap.set(next);
    this.cdr.markForCheck();
  }
}
