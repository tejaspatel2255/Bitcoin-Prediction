import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-badge',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './badge.component.html',
  styleUrl: './badge.component.scss'
})
export class BadgeComponent {
  @Input() type: 'bullish' | 'bearish' | 'neutral' | string = 'neutral';
  @Input() label: string = '';

  get badgeClass(): string {
    return `badge-${this.type.toLowerCase()}`;
  }
}
