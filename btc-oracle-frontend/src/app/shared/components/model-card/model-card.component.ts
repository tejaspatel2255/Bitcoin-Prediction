import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-model-card',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './model-card.component.html',
  styleUrl: './model-card.component.scss'
})
export class ModelCardComponent {
  @Input() icon: string = '';
  @Input() name: string = '';
  @Input() subtitle: string = '';
  @Input() accuracy: number = 0;
  @Input() accColor: string = '#4CAF50';
}
