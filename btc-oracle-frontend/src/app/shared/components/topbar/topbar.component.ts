import { Component, Input, Output, EventEmitter, ChangeDetectionStrategy, ChangeDetectorRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ThemeService } from '../../../core/services/theme.service';

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
  @Output() exportPdf = new EventEmitter<void>();
  
  readonly themeService = inject(ThemeService);
  private cdr = inject(ChangeDetectorRef);

  toggleTheme() {
    this.themeService.toggleTheme();
    this.cdr.markForCheck();
  }

  onExportPdf() {
    this.exportPdf.emit();
  }
}
