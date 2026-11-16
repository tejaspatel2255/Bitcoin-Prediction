export const DARK_CHART_DEFAULTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { 
      labels: { 
        color: '#333333', 
        font: { 
          family: 'Inter, sans-serif',
          weight: 500
        } 
      } 
    },
    tooltip: { 
      backgroundColor: '#1A1D27', 
      titleColor: '#FFF', 
      bodyColor: '#CCC',
      borderColor: '#2A2D3A',
      borderWidth: 1
    }
  },
  scales: {
    x: { 
      grid: { color: '#F0F0F0' }, 
      ticks: { color: '#888' } 
    },
    y: { 
      grid: { color: '#F0F0F0' }, 
      ticks: { color: '#888' } 
    }
  }
};

export const BTC_ORANGE = '#F7931A';
export const BULL_GREEN = '#4CAF50';
export const BEAR_RED = '#F44336';
