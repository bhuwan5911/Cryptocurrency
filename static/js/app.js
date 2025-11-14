/*
  Crypto Price Predictor AI - App Logic (Phase 2)
  Includes:
  - LSTM Model Prediction
  - AI Analyst (Bytez/OpenAI) Integration
  - Theme-Aware Charts
  - Portfolio Management
*/
class CryptoPredictorApp {
    constructor() {
        this.chart = null;
        this.currentCrypto = 'BTC';
        // 'localStorage' se user ki theme preference load karo
        this.isDarkMode = localStorage.getItem('darkMode') === 'true';
        
        // YEH NAYA VARIABLE HAI (Step 2.4)
        // Prediction data ko yahaan store karenge taaki 'Analyze' button use kar sake
        this.currentPredictionData = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.applyDarkMode(); // Theme ko chart load hone se *pehle* apply karo
        this.loadHistory();
        this.loadChart(30); // Default 30 din ka chart load karo
        this.loadPortfolio();
        this.updateStats();
        
        // Default crypto ko select karo
        document.getElementById('cryptoSelect').value = this.currentCrypto;
    }

    setupEventListeners() {
        const form = document.getElementById('predictionForm');
        form?.addEventListener('submit', (e) => this.handlePredict(e));

        const darkModeToggle = document.getElementById('darkModeToggle');
        darkModeToggle?.addEventListener('click', () => this.toggleDarkMode());

        // Chart period buttons
        document.querySelectorAll('.chart-period-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleChartPeriod(e));
        });

        // Crypto select change
        const cryptoSelect = document.getElementById('cryptoSelect');
        cryptoSelect?.addEventListener('change', (e) => {
            this.currentCrypto = e.target.value;
            if (this.currentCrypto) {
                this.loadChart(document.querySelector('.chart-period-btn.active')?.dataset.period || 30);
            }
        });
        
        // ------ STEP 2.4 (NAYA CODE) START ------
        // 'Get AI Insight' button ke liye naya listener
        const analyzeBtn = document.getElementById('analyzeBtn');
        analyzeBtn?.addEventListener('click', (e) => this.handleAnalyze(e));
        // ------ STEP 2.4 (NAYA CODE) END ------

        // (Portfolio listeners ko hum baad mein add kar sakte hain agar form HTML mein hai)
        // const portfolioForm = document.getElementById('addHoldingForm');
        // portfolioForm?.addEventListener('submit', (e) => this.handleAddHolding(e));
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
        
        // ------ STEP 2.4 (NAYA CODE) START ------
        // Nayi prediction se pehle purana analysis saaf karo
        document.getElementById('analyzeBtn').disabled = true;
        document.getElementById('analysisOutput').innerHTML = '<p class="text-gray-500 dark:text-gray-400">Pehle ek prediction generate karein...</p>';
        this.currentPredictionData = null; // Purana data clear karo
        // ------ STEP 2.4 (NAYA CODE) END ------

        try {
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ crypto }) // 'days' parameter hata diya
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Prediction failed');
            }

            this.showResult(data);
            this.loadHistory(); // History refresh karo
            this.updateStats(); // Stats (e.g., total predictions) update karo
            
            // ------ STEP 2.4 (NAYA CODE) START ------
            // Prediction successful! Data ko store karo aur 'Analyze' button enable karo
            this.currentPredictionData = data;
            document.getElementById('analyzeBtn').disabled = false;
            document.getElementById('analysisOutput').innerHTML = '<p class="text-green-600 dark:text-green-400">Prediction safal! Ab "Get AI Insight" par click karein.</p>';
            // ------ STEP 2.4 (NAYA CODE) END ------
            
        } catch (error) {
            console.error('Prediction error:', error);
            this.showError(error.message || 'Failed to generate prediction');
        } finally {
            this.showLoading(false);
        }
    }
    
    // ------ STEP 2.4 (POORA NAYA FUNCTION) START ------
    async handleAnalyze(e) {
        e.preventDefault();
        
        if (!this.currentPredictionData) {
            document.getElementById('analysisOutput').innerHTML = '<p class="text-red-500">Kripaya pehle ek prediction generate karein.</p>';
            return;
        }

        const analyzeBtn = document.getElementById('analyzeBtn');
        const analysisOutput = document.getElementById('analysisOutput');
        
        // Loading state dikhao
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = `
            <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Analyzing...
        `;
        analysisOutput.innerHTML = '<p class="text-gray-500 dark:text-gray-400">AI Analyst (GPT) se baat kar rahe hain...</p>';

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    crypto: this.currentPredictionData.crypto,
                    current_price: this.currentPredictionData.current_price,
                    predicted_price: this.currentPredictionData.predicted_price
                })
            });

            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || 'Analysis failed');
            }
            
            // Success! AI ka jawaab dikhao
            analysisOutput.innerHTML = `<p class="text-gray-800 dark:text-gray-200">${result.analysis.replace(/\n/g, '<br>')}</p>`;

        } catch (error) {
            console.error('Analysis error:', error);
            analysisOutput.innerHTML = `<p class="text-red-500">AI Analyst se Error: ${error.message}</p>`;
        } finally {
            // Loading state hatao
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = 'Get AI Insight';
        }
    }
    // ------ STEP 2.4 (POORA NAYA FUNCTION) END ------

    showResult(data) {
        const resultDiv = document.getElementById('predictionResult');
        document.getElementById('currentPrice').textContent = `$${data.current_price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        document.getElementById('predictedPrice').textContent = `$${data.predicted_price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        
        const changePercent = data.change_percent;
        const changeClass = changePercent >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400';
        const changeSymbol = changePercent >= 0 ? '+' : '';
        const changePercentEl = document.getElementById('changePercent');
        
        changePercentEl.textContent = `${changeSymbol}${changePercent.toFixed(2)}%`;
        // Purani classes hatao aur nayi daalo
        changePercentEl.className = `font-bold text-lg ${changeClass}`;

        document.getElementById('predictionDate').textContent = data.prediction_date;

        resultDiv.classList.remove('hidden');
        resultDiv.classList.add('animate-slide-up');
    }

    showError(message) {
        const errorDiv = document.getElementById('errorMessage');
        document.getElementById('errorText').textContent = message;
        errorDiv.classList.remove('hidden');
        errorDiv.classList.add('animate-fade-in');
    }

    hideError() {
        document.getElementById('errorMessage').classList.add('hidden');
    }

    hideResult() {
        document.getElementById('predictionResult').classList.add('hidden');
    }

    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        const predictBtn = document.getElementById('predictBtn');
        
        if (show) {
            overlay.classList.remove('hidden');
            predictBtn.disabled = true;
            predictBtn.innerHTML = `
                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing...
            `;
        } else {
            overlay.classList.add('hidden');
            predictBtn.disabled = false;
            predictBtn.innerHTML = `
                <i data-feather="brain" class="w-5 h-5"></i>
                <span class="font-bold">Generate AI Prediction</span>
                <i data-feather="sparkles" class="w-4 h-4"></i>
            `;
            feather.replace(); // 'feather.replace()' ko call karna zaroori hai
        }
    }

    async loadHistory() {
        try {
            const response = await fetch('/api/history');
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Failed to load history');
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
                    <td colspan="5" class="text-center py-12 text-gray-500 dark:text-gray-400">
                        <div class="flex flex-col items-center space-y-4">
                            <div class="w-16 h-16 bg-gray-200/50 dark:bg-gradient-to-br dark:from-cyan-500/20 dark:to-purple-500/20 rounded-2xl flex items-center justify-center">
                                <i data-feather="database" class="w-8 h-8 text-cyan-600 dark:text-cyan-400"></i>
                            </div>
                            <div>
                                <h3 class="text-lg font-bold text-gray-700 dark:text-gray-300 mb-1">No Predictions Yet</h3>
                                <p class="text-sm text-gray-500 dark:text-gray-500">Generate your first AI prediction to see it here!</p>
                            </div>
                        </div>
                    </td>
                </tr>
            `;
            feather.replace();
            return;
        }

        tbody.innerHTML = predictions.map(pred => {
            const date = new Date(pred.date + 'T00:00:00'); // Date ko local timezone assume karo
            const formattedDate = date.toLocaleDateString('en-US', { day: '2-digit', month: 'short', year: 'numeric' });
            return `
                <tr class="hover:bg-gray-100/50 dark:hover:bg-white/5 transition-colors">
                    <td class="py-3 px-4 text-gray-800 dark:text-gray-100 font-semibold">${pred.crypto}</td>
                    <td class="py-3 px-4 text-gray-600 dark:text-gray-400">${formattedDate}</td>
                    <td class="py-3 px-4 text-right text-gray-800 dark:text-gray-100 font-medium">$${pred.predicted_price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    <td class="py-3 px-4 text-right text-gray-600 dark:text-gray-400">${pred.actual_price ? '$' + pred.actual_price.toLocaleString('en-US') : '-'}</td>
                    <td class="py-3 px-4 text-right">
                        <span class="py-1 px-3 rounded-full text-xs font-bold ${pred.actual_price ? 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400' : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-400'}">
                            ${pred.actual_price ? 'Completed' : 'Pending'}
                        </span>
                    </td>
                </tr>
            `;
        }).join('');
    }

    renderHistoryError(message) {
        // (Yeh function change nahi hua hai)
        const tbody = document.getElementById('historyTableBody');
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-12 text-red-500 dark:text-red-400">
                    <i data-feather="alert-circle" class="w-8 h-8 mx-auto mb-2"></i>
                    <p>${message}</p>
                </td>
            </tr>
        `;
        feather.replace();
    }

    async loadChart(days) {
        if (!this.currentCrypto) return;

        try {
            const response = await fetch(`/api/chart-data?crypto=${this.currentCrypto}&days=${days}`);
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Failed to load chart data');
            this.renderChart(data.data, data.crypto);
        } catch (error) {
            console.error('Chart loading error:', error);
        }
    }

    renderChart(data, crypto) {
        const ctx = document.getElementById('priceChart').getContext('2d');
        
        if (this.chart) {
            this.chart.destroy();
        }

        const labels = data.map(item => item.date);
        const prices = data.map(item => item.price);

        // --- YEH CHART THEME FIX HAI ---
        const isDark = this.isDarkMode;
        const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.05)';
        const textColor = isDark ? '#9ca3af' : '#6b7280'; // gray-400 / gray-500
        const legendColor = isDark ? '#e5e7eb' : '#374151'; // gray-200 / gray-700

        const cryptoColors = {
            BTC: { border: '#f7931a', background: 'rgba(247, 147, 26, 0.1)' },
            ETH: { border: '#627eea', background: 'rgba(98, 126, 234, 0.1)' },
            ADA: { border: '#0033ad', background: 'rgba(0, 51, 173, 0.1)' },
            SOL: { border: '#9945ff', background: 'rgba(153, 69, 255, 0.1)' },
            DOT: { border: '#e6007a', background: 'rgba(230, 0, 122, 0.1)' },
            AVAX: { border: '#e84142', background: 'rgba(232, 65, 66, 0.1)' },
            LINK: { border: '#375bd2', background: 'rgba(55, 91, 210, 0.1)' },
            LTC: { border: '#bfbbbb', background: 'rgba(191, 187, 187, 0.1)' }
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
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: colors.border,
                    pointBorderColor: isDark ? '#111827' : '#ffffff', // Theme-aware point border
                    pointBorderWidth: 2,
                    pointRadius: 0,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: legendColor, // THEME FIX
                            font: { size: 14, weight: '600' }
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: isDark ? '#1f2937' : '#ffffff', // Theme-aware tooltip
                        titleColor: isDark ? '#e5e7eb' : '#374151',
                        bodyColor: isDark ? '#e5e7eb' : '#374151',
                        borderColor: gridColor,
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                return `Price: $${context.parsed.y.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: textColor, // THEME FIX
                            font: { size: 12 },
                            maxRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 7 // Mobile par achha dikhega
                        },
                        grid: {
                            color: gridColor, // THEME FIX
                            drawBorder: false
                        }
                    },
                    y: {
                        ticks: {
                            color: textColor, // THEME FIX
                            font: { size: 12 },
                            callback: function(value) {
                                return '$' + value.toLocaleString('en-US');
                            }
                        },
                        grid: {
                            color: gridColor, // THEME FIX
                            drawBorder: false
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    handleChartPeriod(e) {
        // 'currentTarget' use karein taaki icon click bhi button ko target kare
        const btn = e.currentTarget;
        const period = parseInt(btn.dataset.period);
        
        document.querySelectorAll('.chart-period-btn').forEach(b => {
            b.classList.remove('bg-cyan-600', 'text-white', 'dark:bg-cyan-500', 'shadow-lg');
            b.classList.add('bg-gray-100/50', 'hover:bg-gray-200/70', 'dark:bg-white/5', 'dark:hover:bg-white/10', 'text-gray-700', 'dark:text-gray-300');
        });
        
        btn.classList.add('bg-cyan-600', 'text-white', 'dark:bg-cyan-500', 'shadow-lg');
        btn.classList.remove('bg-gray-100/50', 'hover:bg-gray-200/70', 'dark:bg-white/5', 'dark:hover:bg-white/10', 'text-gray-700', 'dark:text-gray-300');
        
        this.loadChart(period);
    }

    toggleDarkMode() {
        this.isDarkMode = !this.isDarkMode;
        localStorage.setItem('darkMode', this.isDarkMode);
        this.applyDarkMode();
    }

    applyDarkMode() {
        const html = document.documentElement;
        const icon = document.querySelector('#darkModeToggle i');
        
        if (this.isDarkMode) {
            html.classList.add('dark');
            icon?.setAttribute('data-feather', 'sun');
        } else {
            html.classList.remove('dark');
            icon?.setAttribute('data-feather', 'moon');
        }
        
        feather.replace(); // Icons ko refresh karo
        
        // Chart ko nayi theme ke saath reload karo
        if (this.chart) {
            this.loadChart(document.querySelector('.chart-period-btn.active')?.dataset.period || 30);
        }
    }

    async updateStats() {
        try {
            const response = await fetch('/api/history');
            const data = await response.json();
            
            if (response.ok && data.predictions) {
                document.getElementById('totalPredictions').textContent = data.predictions.length;
            }
        } catch (error) {
            console.error('Error updating stats:', error);
        }
    }

    // --- PORTFOLIO FUNCTIONS ---
    // (Yeh code change nahi hua hai)
    
    async loadPortfolio() {
        // (Yahaan portfolio load karne ka code aayega)
        // console.log("Portfolio loaded (placeholder)");
    }
    
    // (Baaki portfolio functions... handleAddHolding, deleteHolding, etc.)

}

// App ko start karo jab poora page load ho jaaye
document.addEventListener('DOMContentLoaded', () => {
    // Pehle Feather Icons ko chalao
    feather.replace();
    // Phir App ko initialize karo
    const app = new CryptoPredictorApp();
    // app ko global banao taaki inline 'onclick' (agar koi ho) kaam kar sake
    window.app = app;
});