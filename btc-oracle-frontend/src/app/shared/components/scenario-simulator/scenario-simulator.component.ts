import { Component, Input, OnChanges, SimpleChanges, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CurrencyFormatPipe } from '../../pipes/currency-format.pipe';
import { PercentFormatPipe } from '../../pipes/percent-format.pipe';

@Component({
  selector: 'app-scenario-simulator',
  standalone: true,
  imports: [CommonModule, FormsModule, CurrencyFormatPipe, PercentFormatPipe],
  templateUrl: './scenario-simulator.component.html',
  styleUrl: './scenario-simulator.component.scss'
})
export class ScenarioSimulatorComponent implements OnChanges {
  @Input() currentPrice: number = 88000;
  @Input() baselinePrediction: number = 89200;
  @Input() baselineConfidence: number = 74;

  // Simulator Input Signals
  volumeChange = signal<number>(0);       // -50% to +50%
  sentimentRsi = signal<number>(50);       // 20 (Oversold) to 80 (Overbought)
  volatilityFactor = signal<number>(1.0);  // 0.5x to 2.0x

  ngOnChanges(changes: SimpleChanges): void {
    // If inputs change, recalculations happen automatically via computed signals
  }

  // Computed Recalculated Prediction
  simulatedResult = computed(() => {
    const basePred = this.baselinePrediction > 0 ? this.baselinePrediction : this.currentPrice;
    const volShift = this.volumeChange() / 100;
    const rsiShift = (this.sentimentRsi() - 50) / 100;
    const volMult = this.volatilityFactor();

    // Model weight impact calculation
    const priceShiftRatio = (volShift * 0.08) + (rsiShift * 0.14 * volMult);
    const simulatedPrice = basePred * (1 + priceShiftRatio);
    const deltaFromCurrent = simulatedPrice - this.currentPrice;
    const deltaPct = (deltaFromCurrent / this.currentPrice) * 100;
    const direction = simulatedPrice >= this.currentPrice ? 'Bullish' : 'Bearish';

    // Confidence adjustments based on parameters
    let simConfidence = this.baselineConfidence + (Math.abs(rsiShift) * 15) - (volMult > 1.5 ? 8 : 0);
    simConfidence = Math.min(98, Math.max(45, simConfidence));

    const rangeLow = simulatedPrice * (1 - (0.025 * volMult));
    const rangeHigh = simulatedPrice * (1 + (0.032 * volMult));

    return {
      simulatedPrice,
      deltaFromCurrent,
      deltaPct,
      direction,
      confidence: simConfidence,
      rangeLow,
      rangeHigh,
      priceShiftRatio
    };
  });

  // Preset Buttons
  applyPreset(preset: 'bull' | 'bear' | 'volatility' | 'reset') {
    switch (preset) {
      case 'bull':
        this.volumeChange.set(30);
        this.sentimentRsi.set(72);
        this.volatilityFactor.set(1.2);
        break;
      case 'bear':
        this.volumeChange.set(-25);
        this.sentimentRsi.set(30);
        this.volatilityFactor.set(1.4);
        break;
      case 'volatility':
        this.volumeChange.set(40);
        this.sentimentRsi.set(65);
        this.volatilityFactor.set(1.8);
        break;
      case 'reset':
        this.volumeChange.set(0);
        this.sentimentRsi.set(50);
        this.volatilityFactor.set(1.0);
        break;
    }
  }
}
