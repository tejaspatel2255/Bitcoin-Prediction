import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, catchError, map, of } from 'rxjs';
import { environment } from '../../../environments/environment';
import { BTCPrice, BTCHistoricalRow } from '../models/btc-data.model';

@Injectable({
  providedIn: 'root'
})
export class BitcoinService {
  private coinGeckoUrl = environment.coinGeckoUrl;
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getLivePrice(): Observable<BTCPrice> {
    const url = `${this.coinGeckoUrl}/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true&include_market_cap=true&include_24hr_vol=true`;
    return this.http.get<any>(url).pipe(
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
        // Return fallback simulation values
        return of({
          price: 68450.00,
          change_24h: 1.45,
          market_cap: 1345000000000.0,
          volume: 28400000000.0
        } as BTCPrice);
      })
    );
  }

  getHistoricalData(days: number): Observable<BTCHistoricalRow[]> {
    const url = `${this.apiUrl}/api/data/historical?days=${days}`;
    return this.http.get<BTCHistoricalRow[]>(url).pipe(
      catchError(err => {
        console.error('Error fetching historical data:', err);
        return of([] as BTCHistoricalRow[]);
      })
    );
  }
}
