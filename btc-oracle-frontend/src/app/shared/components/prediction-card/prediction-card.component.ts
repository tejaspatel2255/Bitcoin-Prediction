import { Component, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { animate, state, style, transition, trigger } from '@angular/animations';

@Component({
  selector: 'app-prediction-card',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './prediction-card.component.html',
  styleUrl: './prediction-card.component.scss',
  animations: [
    trigger('growWidth', [
      state('start', style({ width: '0%' })),
      state('end', style({ width: '{{width}}%' }), { params: { width: 0 } }),
      transition('start => end', [animate('1s ease-out')])
    ])
  ]
})
export class PredictionCardComponent implements OnInit {
  @Input() predicted: number = 0;
  @Input() low: number = 0;
  @Input() high: number = 0;
  @Input() direction: 'Bullish' | 'Bearish' | string = 'Bullish';
  @Input() confidence: number = 0;

  animationState = 'start';

  ngOnInit() {
    // Delay slightly to allow element to render before animation starts
    setTimeout(() => {
      this.animationState = 'end';
    }, 200);
  }

  get dirColor(): string {
    return this.direction === 'Bullish' || this.direction === 'UP' ? '#4CAF50' : '#F44336';
  }

  get dirBg(): string {
    return this.direction === 'Bullish' || this.direction === 'UP' ? 'rgba(76,175,80,0.12)' : 'rgba(244,67,54,0.12)';
  }

  get arrow(): string {
    return this.direction === 'Bullish' || this.direction === 'UP' ? '↗' : '↘';
  }
}
