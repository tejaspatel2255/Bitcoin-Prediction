import { Component, Input, Output, EventEmitter, ChangeDetectionStrategy, ChangeDetectorRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SkeletonComponent } from '../skeleton/skeleton.component';

@Component({
  selector: 'app-insight-card',
  standalone: true,
  imports: [CommonModule, SkeletonComponent],
  templateUrl: './insight-card.component.html',
  styleUrl: './insight-card.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class InsightCardComponent {
  @Input() icon: string = '';
  @Input() title: string = '';
  @Input() text: string = '';
  @Input() borderColor: string = '#E8E8E8';
  @Input() timestamp: string = '';
  @Input() isLoading: boolean = false;
  @Input() showRefresh: boolean = true;

  @Output() refresh = new EventEmitter<void>();

  private cdr = inject(ChangeDetectorRef);

  markForCheck() {
    this.cdr.markForCheck();
  }

  onRefresh() {
    this.refresh.emit();
  }
}
