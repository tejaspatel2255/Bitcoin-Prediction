import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-skeleton',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="skeleton" [style.width]="width" [style.height]="height" [style.border-radius]="radius"></div>
  `,
  styles: [`
    .skeleton {
      background: linear-gradient(90deg, #E8E8E8 25%, #F5F5F5 50%, #E8E8E8 75%);
      background-size: 200% 100%;
      animation: shimmer 1.5s infinite;
      display: block;
    }
    @keyframes shimmer {
      0% { background-position: -200% 0; }
      100% { background-position: 200% 0; }
    }
  `]
})
export class SkeletonComponent {
  @Input() width = '100%';
  @Input() height = '20px';
  @Input() radius = '4px';
}
