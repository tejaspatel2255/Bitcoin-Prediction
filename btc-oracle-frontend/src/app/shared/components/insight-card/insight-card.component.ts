import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-insight-card',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './insight-card.component.html',
  styleUrl: './insight-card.component.scss'
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

  onRefresh() {
    this.refresh.emit();
  }
}
