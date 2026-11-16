import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'percentFormat',
  standalone: true
})
export class PercentFormatPipe implements PipeTransform {
  transform(value: number | null | undefined, showSign: boolean = true, decimals: number = 2): string {
    if (value === null || value === undefined || isNaN(value)) {
      return '0.00%';
    }
    const sign = showSign && value > 0 ? '+' : '';
    return `${sign}${value.toFixed(decimals)}%`;
  }
}
