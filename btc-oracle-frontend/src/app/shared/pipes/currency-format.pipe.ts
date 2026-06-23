import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'currencyFormat',
  standalone: true
})
export class CurrencyFormatPipe implements PipeTransform {
  transform(value: number | null | undefined, decimals: number = 2, showAbbr: boolean = false): string {
    if (value === null || value === undefined || isNaN(value)) {
      return 'N/A';
    }

    if (showAbbr) {
      if (value >= 1e12) {
        return `$${(value / 1e12).toFixed(decimals)}T`;
      }
      if (value >= 1e9) {
        return `$${(value / 1e9).toFixed(decimals)}B`;
      }
      if (value >= 1e6) {
        return `$${(value / 1e6).toFixed(decimals)}M`;
      }
    }

    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(value);
  }
}
