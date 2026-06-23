import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-metric-card',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './metric-card.component.html',
  styleUrl: './metric-card.component.scss'
})
export class MetricCardComponent {
  @Input() icon: string = '';
  @Input() label: string = '';
  @Input() value: string = '';
  @Input() delta: string = '';
  @Input() deltaColor: string = '#888888';
  @Input() topBorderColor: string = '';
}
