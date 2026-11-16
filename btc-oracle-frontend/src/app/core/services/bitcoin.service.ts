import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, catchError, map, of, shareReplay } from 'rxjs';
import { environment } from '../../../environments/environment';
import { BTCPrice, BTCHistoricalRow } from '../models/btc-data.model';

@Injectable({
  providedIn: 'root'
})
export class BitcoinService {
  private coinGeckoUrl = environment.coinGeckoUrl;
  private apiUrl = environment.apiUrl;

  // Caching variables for Live Price
  private livePriceCache$: Observable<BTCPrice> | null = null;
  private livePriceCacheTime: number = 0;
  private LIVE_PRICE_CACHE_DURATION = 60 * 1000; // 60 seconds

  // Caching map for Historical Data (per days parameter)
  private histCache = new Map<number, { cache$: Observable<BTCHistoricalRow[]>; time: number }>();
  private HIST_CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

  constructor(private http: HttpClient) {}

  getLivePrice(): Observable<BTCPrice> {
    const now = Date.now();
    if (!this.livePriceCache$ || now - this.livePriceCacheTime > this.LIVE_PRICE_CACHE_DURATION) {
      const url = `${this.coinGeckoUrl}/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true&include_market_cap=true&include_24hr_vol=true`;
      this.livePriceCache$ = this.http.get<any>(url).pipe(
        map(res => {
          const data = res.bitcoin;
          return {
            price: data.usd,
            change_24h: data.usd_24h_change,
            market_cap: data.usd_market_cap,
            volume: data.usd_24h_vol
          } as BTCPrice;
        }),
        catchError(err => {
          console.error('Error fetching live price from CoinGecko:', err);
          return of({
            price: 68450.00,
            change_24h: 1.45,
            market_cap: 1345000000000.0,
            volume: 28400000000.0
          } as BTCPrice);
        }),
        shareReplay(1)
      );
      this.livePriceCacheTime = now;
    }
    return this.livePriceCache$;
  }

  getHistoricalData(days: number): Observable<BTCHistoricalRow[]> {
    const now = Date.now();
    const cached = this.histCache.get(days);
    if (!cached || now - cached.time > this.HIST_CACHE_DURATION) {
      const url = `${this.apiUrl}/api/data/historical?days=${days}`;
      const cache$ = this.http.get<BTCHistoricalRow[]>(url).pipe(
        catchError(err => {
          console.error('Error fetching historical data:', err);
          return of([] as BTCHistoricalRow[]);
        }),
        shareReplay(1)
      );
      this.histCache.set(days, { cache$, time: now });
    }
    return this.histCache.get(days)!.cache$;
  }
}
