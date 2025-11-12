class CryptoPredictorApp {
    constructor() {
        this.chart = null;
        this.currentCrypto = 'BTC';
        this.predictionDays = 1;
        this.isDarkMode = localStorage.getItem('darkMode') !== 'false';
        this.portfolio = [];

        // --- NEW: Store last chart data to re-render on theme change ---
        this.lastChartData = null;

        // --- NEW: Define styles for active/inactive buttons ---
        // We will add/remove these full class strings for a professional effect
        this.activeBtnClasses = ['bg-cyan-600', 'text-white', 'shadow-lg', 'dark:bg-cyan-500'];
        this.inactiveBtnClasses = ['bg-gray-100/50', 'hover:bg-gray-200/70', 'dark:bg-white/5', 'dark:hover:bg-white/10', 'text-gray-700', 'dark:text-gray-300'];

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadHistory();
        this.loadChart();
        this.updateStats();
        // this.loadPortfolio(); // Assuming portfolio UI is not in this view
        this.applyDarkMode();
    }

    setupEventListeners() {
        const form = document.getElementById('predictionForm');
        form?.addEventListener('submit', (e) => this.handlePredict(e));

        const darkModeToggle = document.getElementById('darkModeToggle');
        darkModeToggle?.addEventListener('click', () => this.toggleDarkMode());

        document.querySelectorAll('.chart-period-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleChartPeriod(e));
        });

        document.querySelectorAll('.prediction-period-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handlePredictionPeriod(e));
        });

        const cryptoSelect = document.getElementById('cryptoSelect');
        cryptoSelect?.addEventListener('change', (e) => {
            this.currentCrypto = e.target.value;
            if (this.currentCrypto) {
                this.loadChart();
            }
        });
    }

    // ... (handlePredict, showResult, showError, hideError, showLoading methods are unchanged) ...
    // ... (Paste your existing handlePredict, showResult, showError, etc. methods here) ...

    async handlePredict(e) {
      e.preventDefault();
      
      const crypto = document.getElementById('cryptoSelect').value;
      if (!crypto) {
          this.showError('Please select a cryptocurrency');
          return;
      }

      this.showLoading(true);
      this.hideError();
      this.hideResult();

      try {
          const response = await fetch('/api/predict', {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
              },
              body: JSON.stringify({ crypto, days: this.predictionDays })
          });

          const data = await response.json();

          if (!response.ok) {
              throw new Error(data.error || 'Prediction failed');
          }

          this.showResult(data);
          this.loadHistory(); // Refresh history
          this.updateStats(); // Update stats
          
      } catch (error) {
          console.error('Prediction error:', error);
          this.showError(error.message || 'Failed to generate prediction');
      } finally {
          this.showLoading(false);
      }
    }

    showResult(data) {
        const resultDiv = document.getElementById('predictionResult');
        const currentPriceEl = document.getElementById('currentPrice');
        const predictedPriceEl = document.getElementById('predictedPrice');
        const changePercentEl = document.getElementById('changePercent');
        const predictionDateEl = document.getElementById('predictionDate');

        // --- UPDATED: Fix for light/dark mode text color ---
        const changePercent = data.change_percent;
        const changeClass = changePercent >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400';
        const changeSymbol = changePercent >= 0 ? '+' : '';
        
        currentPriceEl.textContent = `$${data.current_price.toFixed(2)}`;
        predictedPriceEl.textContent = `$${data.predicted_price.toFixed(2)}`;
        
        changePercentEl.textContent = `${changeSymbol}${changePercent.toFixed(2)}%`;
        // Ensure class is reset correctly
        changePercentEl.className = `font-bold text-lg ${changeClass}`;

        predictionDateEl.textContent = data.prediction_date;

        resultDiv.classList.remove('hidden');
        resultDiv.classList.add('animate-slide-up');
    }

    showError(message) {
      const errorDiv = document.getElementById('errorMessage');
      const errorText = document.getElementById('errorText');
      
      errorText.textContent = message;
      errorDiv.classList.remove('hidden');
      errorDiv.classList.add('animate-fade-in');
    }

    hideError() {
      const errorDiv = document.getElementById('errorMessage');
      errorDiv.classList.add('hidden');
    }

    hideResult() {
      const resultDiv = document.getElementById('predictionResult');
      resultDiv.classList.add('hidden');
    }

    showLoading(show) {
      const overlay = document.getElementById('loadingOverlay');
      const predictBtn = document.getElementById('predictBtn');
      
      if (show) {
          overlay.classList.remove('hidden');
          predictBtn.disabled = true;
          // Use opacity instead of 'loading' class for simplicity
          predictBtn.classList.add('opacity-50', 'cursor-not-allowed');
      } else {
          overlay.classList.add('hidden');
          predictBtn.disabled = false;
          predictBtn.classList.remove('opacity-50', 'cursor-not-allowed');
      }
    }

    async loadHistory() {
        try {
            const response = await fetch('/api/history');
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to load history');
            }
            this.renderHistory(data.predictions);
        } catch (error) {
            console.error('History loading error:', error);
            this.renderHistoryError('Failed to load prediction history');
        }
    }

    renderHistory(predictions) {
        const tbody = document.getElementById('historyTableBody');
        
        if (!predictions || predictions.length === 0) {
            // This is the "No Predictions Yet" block from index.html,
            // so we just return and let the HTML default show.
            tbody.innerHTML = ''; // Clear any old rows
            return;
        }

        tbody.innerHTML = predictions.map(pred => {
            const cryptoClass = pred.crypto === 'BTC' ? 'text-crypto-bitcoin' : (pred.crypto === 'ETH' ? 'text-crypto-ethereum' : 'text-cyan-600 dark:text-cyan-400');
            
            // --- UPDATED: Theme-aware text colors ---
            const statusBadge = pred.actual_price ? 
                '<span class="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300 text-xs font-medium px-2.5 py-0.5 rounded-full">Completed</span>' : 
                '<span class="bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300 text-xs font-medium px-2.5 py-0.5 rounded-full">Pending</span>';
            
            return `
                <tr class="hover:bg-gray-100 dark:hover:bg-white/5 transition-colors">
                    <td class="py-3 px-4">
                        <span class="font-semibold ${cryptoClass}">${pred.crypto}</span>
                    </td>
                    <td class="py-3 px-4 text-gray-600 dark:text-gray-300">${new Date(pred.date).toLocaleDateString()}</td>
                    <td class="py-3 px-4 text-right font-medium text-gray-800 dark:text-white">$${pred.predicted_price}</td>
                    <td class="py-3 px-4 text-right text-gray-600 dark:text-gray-300">${pred.actual_price ? `$${pred.actual_price}` : '-'}</td>
                    <td class="py-3 px-4 text-right">${statusBadge}</td>
                </tr>
            `;
        }).join('');
    }


    renderHistoryError(message) {
        const tbody = document.getElementById('historyTableBody');
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-8 text-red-500 dark:text-red-400">
                    <div class="flex flex-col items-center space-y-2">
                        <i data-feather="alert-circle" class="w-8 h-8"></i>
                        <span>${message}</span>
                    </div>
                </td>
            </tr>
        `;
        feather.replace();
    }

    async loadChart(days = 30) {
        if (!this.currentCrypto) return;

        try {
            const response = await fetch(`/api/chart-data?crypto=${this.currentCrypto}&days=${days}`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to load chart data');
            }
            this.renderChart(data.data, data.crypto);
        } catch (error) {
            console.error('Chart loading error:', error);
            this.renderChartError('Failed to load price data');
        }
    }

    renderChart(data, crypto) {
        const ctx = document.getElementById('priceChart').getContext('2d');
        
        if (this.chart) {
            this.chart.destroy();
        }

        // --- NEW: Store data for theme refresh ---
        this.lastChartData = { data, crypto };

        const labels = data.map(item => new Date(item.date).toLocaleDateString());
        const prices = data.map(item => item.price);

        const cryptoColors = {
            BTC: { border: '#f7931a', background: 'rgba(247, 147, 26, 0.1)' },
            ETH: { border: '#627eea', background: 'rgba(98, 126, 234, 0.1)' },
            ADA: { border: '#0033ad', background: 'rgba(0, 51, 173, 0.1)' },
            SOL: { border: '#9945ff', background: 'rgba(153, 69, 255, 0.1)' },
            MATIC: { border: '#8247e5', background: 'rgba(130, 71, 229, 0.1)' },
            DOT: { border: '#e6007a', background: 'rgba(230, 0, 122, 0.1)' },
            AVAX: { border: '#e84142', background: 'rgba(232, 65, 66, 0.1)' },
            LINK: { border: '#375bd2', background: 'rgba(55, 91, 210, 0.1)' },
            UNI: { border: '#ff007a', background: 'rgba(255, 0, 122, 0.1)' },
            LTC: { border: '#bfbbbb', background: 'rgba(191, 187, 187, 0.1)' }
        };
        const colors = cryptoColors[crypto] || cryptoColors.BTC;

        // --- THEME FIX: Determine colors based on dark mode ---
        const isDark = this.isDarkMode;
        const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
        const textColor = isDark ? '#9ca3af' : '#4b5563'; // gray-400 / gray-600
        const legendColor = isDark ? '#ffffff' : '#1f2937'; // white / gray-800

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: `${crypto} Price (USD)`,
                    data: prices,
                    borderColor: colors.border,
                    backgroundColor: colors.background,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: colors.border,
                    pointBorderColor: isDark ? '#111827' : '#ffffff', // Dark/Light background
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: legendColor, // <-- FIXED
                            font: {
                                size: 14,
                                weight: '600'
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: textColor, // <-- FIXED
                            font: { size: 12 }
                        },
                        grid: {
                            color: gridColor, // <-- FIXED
                            drawBorder: false
                        }
                    },
                    y: {
                        ticks: {
                            color: textColor, // <-- FIXED
                            font: { size: 12 },
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        },
                        grid: {
                            color: gridColor, // <-- FIXED
                            drawBorder: false
                        }
                    }
                },
                elements: {
                    point: {
                        hoverBackgroundColor: '#ffffff'
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    renderChartError(message) {
      const canvas = document.getElementById('priceChart');
      const ctx = canvas.getContext('2d');
      
      if (this.chart) {
          this.chart.destroy();
      }
      
      // --- THEME FIX: Use theme-aware color ---
      const textColor = this.isDarkMode ? '#ef4444' : '#dc2626'; // red-500 / red-600

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = textColor;
      ctx.font = '16px system-ui';
      ctx.textAlign = 'center';
      ctx.fillText(message, canvas.width / 2, canvas.height / 2);
    }

    // --- UPDATED: Swaps full Tailwind classes for active state ---
    handleChartPeriod(e) {
        const clickedBtn = e.currentTarget;
        const period = parseInt(clickedBtn.dataset.period);
        
        document.querySelectorAll('.chart-period-btn').forEach(btn => {
            btn.classList.remove(...this.activeBtnClasses);
            btn.classList.add(...this.inactiveBtnClasses);
        });
        clickedBtn.classList.remove(...this.inactiveBtnClasses);
        clickedBtn.classList.add(...this.activeBtnClasses);
        
        this.loadChart(period);
    }

    // --- UPDATED: Swaps full Tailwind classes for active state ---
    handlePredictionPeriod(e) {
        const clickedBtn = e.currentTarget;
        this.predictionDays = parseInt(clickedBtn.dataset.days);
        
        document.querySelectorAll('.prediction-period-btn').forEach(btn => {
            btn.classList.remove(...this.activeBtnClasses);
            btn.classList.add(...this.inactiveBtnClasses);
        });
        clickedBtn.classList.remove(...this.inactiveBtnClasses);
        clickedBtn.classList.add(...this.activeBtnClasses);
    }

    toggleDarkMode() {
        this.isDarkMode = !this.isDarkMode;
        localStorage.setItem('darkMode', this.isDarkMode);
        this.applyDarkMode();
    }

    applyDarkMode() {
        const html = document.documentElement;
        
        // --- SIMPLIFIED: Just toggle the 'dark' class on <html> ---
        // Your index.html and Tailwind will handle the rest.
        if (this.isDarkMode) {
            html.classList.add('dark');
        } else {
            html.classList.remove('dark');
        }
        
        // --- NEW: Refresh chart to apply new theme colors ---
        if (this.chart && this.lastChartData) {
            this.renderChart(this.lastChartData.data, this.lastChartData.crypto);
        }

        // Feather icons needs to be refreshed IF you are swapping them (which we do)
        feather.replace();
    }

    async updateStats() {
        try {
            const response = await fetch('/api/history');
            const data = await response.json();
            
            if (response.ok && data.predictions) {
                const totalPredictions = data.predictions.length;
                document.getElementById('totalPredictions').textContent = totalPredictions;
            }
        } catch (error) {
            console.error('Error updating stats:', error);
        }
    }

    // ... (Your portfolio methods) ...
    // Paste your existing loadPortfolio, handleAddHolding, deleteHolding, etc. here
}

// Initialize app when DOM is loaded
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new CryptoPredictorApp();
});