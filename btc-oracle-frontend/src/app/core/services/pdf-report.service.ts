import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class PdfReportService {

  async generateExecutiveReport(data: {
    btcPrice: { price: number; change_24h: number; volume: number; market_cap: number };
    prediction: { predicted: number; low: number; high: number; direction: string; confidence: number };
    insights: { market_summary: string; risk_analysis: string; seven_day_outlook: string };
    accuracies: { prophet: number; random_forest: number; lstm: number };
  }): Promise<void> {
    try {
      const jsPDFModule = await import('jspdf');
      const jsPDF = jsPDFModule.jsPDF || jsPDFModule.default;
      const doc = new jsPDF('p', 'mm', 'a4');

      const dateStr = new Date().toLocaleDateString('en-US', {
        year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
      });

      // ── Header Band ──────────────────────────────────────────────────
      doc.setFillColor(15, 17, 23); // #0F1117 Dark Header
      doc.rect(0, 0, 210, 32, 'F');

      // Title & Subtitle
      doc.setTextColor(245, 158, 11); // BTC Orange #F59E0B
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(20);
      doc.text('BTC ORACLE', 14, 15);

      doc.setTextColor(255, 255, 255);
      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.text('Executive Market Intelligence Brief & AI Forecast', 14, 23);

      doc.setTextColor(156, 163, 175);
      doc.setFontSize(9);
      doc.text(`Generated: ${dateStr}`, 145, 23);

      let y = 42;

      // ── Key Market Telemetry Section ───────────────────────────────────
      doc.setTextColor(31, 41, 55);
      doc.setFontSize(12);
      doc.setFont('helvetica', 'bold');
      doc.text('1. MARKET TELEMETRY', 14, y);
      y += 6;

      doc.setDrawColor(229, 231, 235);
      doc.line(14, y, 196, y);
      y += 8;

      // Metric Box 1: BTC Price
      doc.setFillColor(249, 250, 251);
      doc.roundedRect(14, y, 42, 22, 3, 3, 'F');
      doc.setFontSize(8);
      doc.setTextColor(107, 114, 128);
      doc.text('BTC PRICE', 18, y + 6);
      doc.setFontSize(11);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(31, 41, 55);
      doc.text(`$${data.btcPrice.price.toLocaleString('en-US', { minimumFractionDigits: 2 })}`, 18, y + 14);

      // Metric Box 2: 24h Change
      doc.roundedRect(60, y, 42, 22, 3, 3, 'F');
      doc.setFontSize(8);
      doc.setTextColor(107, 114, 128);
      doc.text('24H CHANGE', 64, y + 6);
      doc.setFontSize(11);
      doc.setFont('helvetica', 'bold');
      const isPos = data.btcPrice.change_24h >= 0;
      doc.setTextColor(isPos ? 16 : 239, isPos ? 185 : 68, isPos ? 129 : 68);
      doc.text(`${isPos ? '+' : ''}${data.btcPrice.change_24h.toFixed(2)}%`, 64, y + 14);

      // Metric Box 3: 24h Volume
      doc.setFillColor(249, 250, 251);
      doc.roundedRect(106, y, 42, 22, 3, 3, 'F');
      doc.setFontSize(8);
      doc.setTextColor(107, 114, 128);
      doc.text('24H VOLUME', 110, y + 6);
      doc.setFontSize(11);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(31, 41, 55);
      doc.text(`$${(data.btcPrice.volume / 1e9).toFixed(2)}B`, 110, y + 14);

      // Metric Box 4: Market Cap
      doc.roundedRect(152, y, 44, 22, 3, 3, 'F');
      doc.setFontSize(8);
      doc.setTextColor(107, 114, 128);
      doc.text('MARKET CAP', 156, y + 6);
      doc.setFontSize(11);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(31, 41, 55);
      doc.text(`$${(data.btcPrice.market_cap / 1e9).toFixed(1)}B`, 156, y + 14);

      y += 30;

      // ── AI Ensemble Prediction Section ─────────────────────────────────
      doc.setTextColor(31, 41, 55);
      doc.setFontSize(12);
      doc.setFont('helvetica', 'bold');
      doc.text('2. ENSEMBLE MODEL PREDICTION (PROPHET + LSTM + RF)', 14, y);
      y += 6;
      doc.line(14, y, 196, y);
      y += 8;

      doc.setFillColor(245, 247, 250);
      doc.roundedRect(14, y, 182, 30, 4, 4, 'F');

      doc.setFontSize(9);
      doc.setTextColor(107, 114, 128);
      doc.text('TARGET FORECAST (24H)', 20, y + 8);
      doc.setFontSize(16);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(245, 158, 11);
      doc.text(`$${data.prediction.predicted.toLocaleString('en-US', { minimumFractionDigits: 2 })}`, 20, y + 18);

      doc.setFontSize(9);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(75, 85, 99);
      doc.text(`Estimated Range: $${data.prediction.low.toLocaleString()} — $${data.prediction.high.toLocaleString()}`, 20, y + 25);

      doc.setFontSize(11);
      doc.setFont('helvetica', 'bold');
      const isBull = data.prediction.direction === 'Bullish';
      doc.setTextColor(isBull ? 16 : 239, isBull ? 185 : 68, isBull ? 129 : 68);
      doc.text(`Direction: ${data.prediction.direction} (${data.prediction.confidence}% Confidence)`, 105, y + 18);

      y += 38;

      // ── OpenRouter / Gemini AI Insights ─────────────────────────────────
      doc.setTextColor(31, 41, 55);
      doc.setFontSize(12);
      doc.setFont('helvetica', 'bold');
      doc.text('3. AI MARKET INTELLIGENCE & INSIGHTS (GEMINI 1.5 FLASH)', 14, y);
      y += 6;
      doc.line(14, y, 196, y);
      y += 8;

      const drawSectionBox = (title: string, content: string, colorRGB: [number, number, number]) => {
        doc.setFillColor(252, 252, 253);
        doc.setDrawColor(colorRGB[0], colorRGB[1], colorRGB[2]);
        doc.setLineWidth(0.8);
        doc.roundedRect(14, y, 182, 30, 3, 3, 'FD');

        doc.setFontSize(10);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(colorRGB[0], colorRGB[1], colorRGB[2]);
        doc.text(title, 20, y + 7);

        doc.setFontSize(8.5);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(55, 65, 81);

        const lines = doc.splitTextToSize(content || 'No insights available.', 170);
        doc.text(lines.slice(0, 3), 20, y + 14);

        y += 34;
      };

      drawSectionBox('Executive Market Summary', data.insights.market_summary, [245, 158, 11]);
      drawSectionBox('Risk Analysis & Volatility Factors', data.insights.risk_analysis, [239, 68, 68]);
      drawSectionBox('7-Day Structural Outlook', data.insights.seven_day_outlook, [16, 185, 129]);

      // ── Footer ──────────────────────────────────────────────────────────
      doc.setFontSize(8);
      doc.setTextColor(156, 163, 175);
      doc.text('BTC Oracle System © — Financial Intelligence & Ensemble Prediction Platform.', 14, 285);
      doc.text('Page 1 of 1', 180, 285);

      // Save PDF
      doc.save(`BTC-Oracle-Executive-Brief-${new Date().toISOString().split('T')[0]}.pdf`);
    } catch (err) {
      console.error('Failed to generate PDF report:', err);
      alert('PDF generation failed. Please try again.');
    }
  }
}
