import { Component, Input, ChangeDetectionStrategy, ChangeDetectorRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SkeletonComponent } from '../skeleton/skeleton.component';

@Component({
  selector: 'app-metric-card',
  standalone: true,
  imports: [CommonModule, SkeletonComponent],
  templateUrl: './metric-card.component.html',
  styleUrl: './metric-card.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class MetricCardComponent {
  @Input() icon: string = '';
  @Input() label: string = '';
  @Input() value: string = '';
  @Input() delta: string = '';
  @Input() deltaColor: string = '#888888';
  @Input() topBorderColor: string = '';
  @Input() isLoading: boolean = false;

  private cdr = inject(ChangeDetectorRef);

  markForCheck() {
    this.cdr.markForCheck();
  }
}
