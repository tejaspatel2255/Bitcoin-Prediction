import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./pages/home/home.component').then(m => m.HomeComponent)
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./pages/dashboard/dashboard.component').then(m => m.DashboardComponent)
  },
  {
    path: 'predictions',
    loadComponent: () => import('./pages/predictions/predictions.component').then(m => m.PredictionsComponent)
  },
  {
    path: 'insights',
    loadComponent: () => import('./pages/ai-insights/ai-insights.component').then(m => m.AiInsightsComponent)
  },
  {
    path: 'performance',
    loadComponent: () => import('./pages/model-performance/model-performance.component').then(m => m.ModelPerformanceComponent)
  },
  {
    path: '**',
    redirectTo: ''
  }
];
