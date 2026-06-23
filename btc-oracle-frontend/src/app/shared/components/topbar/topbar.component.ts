import { Component, Input, ChangeDetectionStrategy, ChangeDetectorRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-topbar',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './topbar.component.html',
  styleUrl: './topbar.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class TopbarComponent {
  @Input() lastUpdated: string = '2 min ago';
  
  private cdr = inject(ChangeDetectorRef);
  
  // Expose manual change detection hook if needed by parent
  markForCheck() {
    this.cdr.markForCheck();
  }
}
