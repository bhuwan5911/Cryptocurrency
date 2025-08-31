class CryptoPredictorApp {
    constructor() {
        this.chart = null;
        this.currentCrypto = 'BTC';
        this.isDarkMode = true;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadHistory();
        this.loadChart();
        this.updateStats();
    }

    setupEventListeners() {
        // Prediction form
        const form = document.getElementById('predictionForm');
        form.addEventListener('submit', (e) => this.handlePredict(e));

        // Dark mode toggle
        const darkModeToggle = document.getElementById('darkModeToggle');
        darkModeToggle.addEventListener('click', () => this.toggleDarkMode());

        // Chart period buttons
        document.querySelectorAll('.chart-period-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleChartPeriod(e));
        });

        // Crypto select change
        const cryptoSelect = document.getElementById('cryptoSelect');
        cryptoSelect.addEventListener('change', (e) => {
            this.currentCrypto = e.target.value;
            if (this.currentCrypto) {
                this.loadChart();
            }
        });
    }

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
                body: JSON.stringify({ crypto })
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

        currentPriceEl.textContent = `$${data.current_price.toFixed(2)}`;
        predictedPriceEl.textContent = `$${data.predicted_price.toFixed(2)}`;
        
        const changePercent = data.change_percent;
        const changeClass = changePercent >= 0 ? 'text-green-400' : 'text-red-400';
        const changeSymbol = changePercent >= 0 ? '+' : '';
        changePercentEl.textContent = `${changeSymbol}${changePercent.toFixed(2)}%`;
        changePercentEl.className = `font-semibold ${changeClass}`;

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
            predictBtn.classList.add('loading');
        } else {
            overlay.classList.add('hidden');
            predictBtn.disabled = false;
            predictBtn.classList.remove('loading');
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
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center py-8 text-gray-400">
                        <div class="flex flex-col items-center space-y-2">
                            <i data-feather="database" class="w-8 h-8 text-gray-500"></i>
                            <span>No predictions yet. Make your first prediction!</span>
                        </div>
                    </td>
                </tr>
            `;
            feather.replace();
            return;
        }

        tbody.innerHTML = predictions.map(pred => {
            const cryptoClass = pred.crypto === 'BTC' ? 'text-crypto-btc' : 'text-crypto-eth';
            const statusBadge = pred.actual_price ? 
                '<span class="status-completed">Completed</span>' : 
                '<span class="status-pending">Pending</span>';
            
            return `
                <tr class="hover:bg-white/5 transition-colors">
                    <td class="py-3 px-2">
                        <span class="font-semibold ${cryptoClass}">${pred.crypto}</span>
                    </td>
                    <td class="py-3 px-2 text-gray-300">${new Date(pred.date).toLocaleDateString()}</td>
                    <td class="py-3 px-2 text-right font-medium text-white">$${pred.predicted_price}</td>
                    <td class="py-3 px-2 text-right text-gray-300">${pred.actual_price ? `$${pred.actual_price}` : '-'}</td>
                    <td class="py-3 px-2 text-right">${statusBadge}</td>
                </tr>
            `;
        }).join('');
    }

    renderHistoryError(message) {
        const tbody = document.getElementById('historyTableBody');
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-8 text-red-400">
                    <div class="flex flex-col items-center space-y-2">
                        <i data-feather="alert-circle" class="w-8 h-8 text-red-500"></i>
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

        const labels = data.map(item => new Date(item.date).toLocaleDateString());
        const prices = data.map(item => item.price);

        // Determine crypto colors
        const cryptoColors = {
            BTC: { border: '#f7931a', background: '#f7931a20' },
            ETH: { border: '#627eea', background: '#627eea20' }
        };

        const colors = cryptoColors[crypto] || cryptoColors.BTC;

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
                    pointBorderColor: '#ffffff',
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
                            color: '#ffffff',
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
                            color: '#9ca3af',
                            font: {
                                size: 12
                            }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)',
                            drawBorder: false
                        }
                    },
                    y: {
                        ticks: {
                            color: '#9ca3af',
                            font: {
                                size: 12
                            },
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)',
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

        // Clear canvas and show error message
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#ef4444';
        ctx.font = '16px system-ui';
        ctx.textAlign = 'center';
        ctx.fillText(message, canvas.width / 2, canvas.height / 2);
    }

    handleChartPeriod(e) {
        const period = parseInt(e.target.dataset.period);
        
        // Update active button
        document.querySelectorAll('.chart-period-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        e.target.classList.add('active');
        
        // Load chart with new period
        this.loadChart(period);
    }

    toggleDarkMode() {
        this.isDarkMode = !this.isDarkMode;
        const html = document.documentElement;
        const icon = document.querySelector('#darkModeToggle i');
        
        if (this.isDarkMode) {
            html.classList.add('dark');
            icon.setAttribute('data-feather', 'moon');
        } else {
            html.classList.remove('dark');
            icon.setAttribute('data-feather', 'sun');
        }
        
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
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new CryptoPredictorApp();
});

// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatPercentage(value) {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
}

// Add smooth scrolling for better UX
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Add keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + Enter to submit prediction form
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        const form = document.getElementById('predictionForm');
        if (form) {
            form.dispatchEvent(new Event('submit'));
        }
    }
    
    // Escape to close loading overlay
    if (e.key === 'Escape') {
        const overlay = document.getElementById('loadingOverlay');
        if (!overlay.classList.contains('hidden')) {
            overlay.classList.add('hidden');
        }
    }
});

// Handle connection errors gracefully
window.addEventListener('online', function() {
    console.log('Connection restored');
});

window.addEventListener('offline', function() {
    console.log('Connection lost');
});
