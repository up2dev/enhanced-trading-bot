// Enhanced Trading Bot Dashboard - Page Portfolio COMPLÈTE
// Charge TOUTES les données : stats, balances, table, chart, performances

console.log('📄 Chargement du fichier portfolio.js complet')

// Variables globales
let portfolioData = null
let allocationChart = null
let refreshInterval = null

// === UTILITAIRES DE FORMATAGE ===
function formatNumber(num, decimals = 2) {
    if (num === null || num === undefined || isNaN(num)) return '--'
    return parseFloat(num).toFixed(decimals)
}

function formatCurrency(amount) {
    if (amount === null || amount === undefined || isNaN(amount)) return '--'
    return `${formatNumber(amount, 2)} USDC`
}

function formatPercent(value) {
    if (value === null || value === undefined || isNaN(value)) return '--'
    return `${(value).toFixed(2)}%`
}

function setElementContent(elementId, content) {
    const element = document.getElementById(elementId)
    if (element) {
        element.textContent = content
        return true
    } else {
        console.warn(`⚠️ Élément ${elementId} non trouvé`)
        return false
    }
}

function showSectionLoader(id, show = true) {
    const el = document.getElementById(id)
    if (el) el.style.display = show ? 'block' : 'none'
}

// === CHARGEMENT DES DONNÉES PORTFOLIO ===
async function loadPortfolioData() {
    try {
        showSectionLoader('portfolio-summary-loader', true)
        showSectionLoader('holdings-loader', true)
        showSectionLoader('allocation-loader', true)

        const response = await fetch('/api/portfolio')

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        const data = await response.json()

        if (data.error) {
            console.error('❌ Erreur API portfolio:', data.error)
            showError('portfolio', data.error)
            showSectionLoader('portfolio-summary-loader', false)
            showSectionLoader('holdings-loader', false)
            showSectionLoader('allocation-loader', false)
            return null
        }

        portfolioData = data

        // Mettre à jour toutes les sections
        updatePortfolioSummary(data)
        updateHoldingsTable(data)
        updateAllocationChart(data)

        showSectionLoader('portfolio-summary-loader', false)
        showSectionLoader('holdings-loader', false)
        showSectionLoader('allocation-loader', false)

        return data

    } catch (error) {
        console.error('❌ Erreur chargement portfolio:', error)
        showError('portfolio', error.message)
        showSectionLoader('portfolio-summary-loader', false)
        showSectionLoader('holdings-loader', false)
        showSectionLoader('allocation-loader', false)
        return null
    }
}

// === CHARGEMENT DES PERFORMANCES ===
async function loadPerformanceData() {
    try {
        showSectionLoader('performance-loader', true)

        const response = await fetch('/api/portfolio/performance')

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        const data = await response.json()

        if (data.error) {
            console.warn('⚠️ Erreur API performances:', data.error)
            setDefaultPerformances()
            showSectionLoader('performance-loader', false)
            return null
        }

        updatePerformanceElements(data)
        showSectionLoader('performance-loader', false)

        return data

    } catch (error) {
        console.error('❌ Erreur chargement performances:', error)
        setDefaultPerformances()
        showSectionLoader('performance-loader', false)
        return null
    }
}

// === CHARGEMENT COMPLET DE LA PAGE ===
async function loadAllData() {
    await Promise.allSettled([
        loadPortfolioData(),
        loadPerformanceData()
    ])
}

// === MISE À JOUR DU RÉSUMÉ PORTFOLIO ===
function updatePortfolioSummary(data) {
    try {
        const activeCount = data.active_cryptos || 0
        setElementContent('active-cryptos-count', activeCount)

        const totalValue = data.total_value || 0
        setElementContent('total-value', formatCurrency(totalValue))

        const freeUsdc = data.free_usdc || 0
        setElementContent('free-usdc', formatCurrency(freeUsdc))

    } catch (error) {
        console.error('❌ Erreur mise à jour résumé:', error)
    }
}

// === MISE À JOUR DES PERFORMANCES ===
function updatePerformanceElements(data) {
    try {
        const perfElements = {
            'perf-today': data.today || 0,
            'perf-7d': data['7d'] || data.week || 0,
            'perf-30d': data['30d'] || data.month || 0,
            'perf-total': data.total || 0
        }

        Object.entries(perfElements).forEach(([elementId, value]) => {
            const element = document.getElementById(elementId)
            if (element) {
                const formattedValue = `${value >= 0 ? '+' : ''}${formatNumber(value, 2)}%`
                element.textContent = formattedValue

                element.classList.remove('positive', 'negative', 'neutral')
                if (value > 0.1) element.classList.add('positive')
                else if (value < -0.1) element.classList.add('negative')
                else element.classList.add('neutral')
            }
        })

    } catch (error) {
        console.error('❌ Erreur mise à jour performances:', error)
        setDefaultPerformances()
    }
}

function setDefaultPerformances() {
    const defaultPerfs = {
        'perf-today': 0,
        'perf-7d': 0,
        'perf-30d': 0,
        'perf-total': 0
    }

    Object.entries(defaultPerfs).forEach(([elementId, value]) => {
        const element = document.getElementById(elementId)
        if (element) {
            element.textContent = `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
            element.classList.add('neutral')
        }
    })
}

// === MISE À JOUR DU TABLEAU HOLDINGS ===
function updateHoldingsTable(data) {
    const tbody = document.getElementById('holdings-table')
    if (!tbody) return

    if (!data.cryptos || data.cryptos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="loading">Aucune crypto configurée</td></tr>'
        return
    }

    try {
        const rows = data.cryptos.map((crypto) => {
            const name = crypto.name || 'N/A'
            const symbol = crypto.symbol || 'N/A'

            const balance = crypto.balance || 0
            const currentPrice = crypto.current_price || 0
            const valueUsdc = crypto.value_usdc || 0

            const targetAllocation = crypto.max_allocation || 0
            const currentAllocation = crypto.current_allocation || 0
            const allocationDiff = currentAllocation - targetAllocation

            let statusClass = 'status-unknown'
            let statusText = 'En attente'

            if (balance > 0) {
                if (allocationDiff > 0.03) {
                    statusClass = 'status-high'
                    statusText = 'Sur-alloué'
                } else if (allocationDiff < -0.03) {
                    statusClass = 'status-low'
                    statusText = 'Sous-alloué'
                } else {
                    statusClass = 'status-ok'
                    statusText = 'Équilibré'
                }
            }

            return `
                <tr>
                    <td>
                        <strong>${name}</strong><br>
                        <small class="text-muted">${symbol}</small>
                    </td>
                    <td class="text-right">
                        ${balance > 0 ? formatNumber(balance, 8) : '--'}<br>
                        <small class="text-muted">${name}</small>
                    </td>
                    <td class="text-right">${currentPrice > 0 ? formatCurrency(currentPrice) : '--'}</td>
                    <td class="text-right">${valueUsdc > 0 ? formatCurrency(valueUsdc) : '--'}</td>
                    <td class="text-right">${formatPercent(currentAllocation * 100)}</td>
                    <td class="text-right">${formatPercent(targetAllocation * 100)}</td>
                    <td class="text-center">
                        <span class="status-badge ${statusClass}">${statusText}</span>
                    </td>
                </tr>
            `
        })

        tbody.innerHTML = rows.join('')

    } catch (error) {
        console.error('❌ Erreur construction tableau:', error)
        tbody.innerHTML = '<tr><td colspan="7" class="error">Erreur lors de la construction du tableau</td></tr>'
    }
}

// === MISE À JOUR DU GRAPHIQUE D'ALLOCATION ===
function updateAllocationChart(data) {
    const chartCanvas = document.getElementById('allocation-chart')
    if (!chartCanvas) return

    if (!data.cryptos || data.cryptos.length === 0) return

    const cryptosWithBalance = data.cryptos.filter(c => (c.balance || 0) > 0 && (c.value_usdc || 0) > 0)

    if (cryptosWithBalance.length === 0) {
        const ctx = chartCanvas.getContext('2d')
        ctx.clearRect(0, 0, chartCanvas.width, chartCanvas.height)
        ctx.font = '16px Arial'
        ctx.fillStyle = '#666'
        ctx.textAlign = 'center'
        ctx.fillText('Aucune donnée à afficher', chartCanvas.width / 2, chartCanvas.height / 2)
        return
    }

    try {
        const labels = cryptosWithBalance.map(c => c.name)
        const values = cryptosWithBalance.map(c => c.value_usdc || 0)
        const colors = [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
            '#FF9F40', '#c9cbcf', '#7FD8BE', '#A7C5EB', '#FF5C8D', '#ffb347'
        ]

        if (allocationChart) allocationChart.destroy()

        allocationChart = new Chart(chartCanvas, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: colors.slice(0, values.length),
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { font: { size: 12 }, padding: 15 }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const value = context.raw
                                const total = context.dataset.data.reduce((a, b) => a + b, 0)
                                const percentage = ((value / total) * 100).toFixed(1)
                                return `${context.label}: ${formatCurrency(value)} (${percentage}%)`
                            }
                        }
                    }
                }
            }
        })

    } catch (error) {
        console.error('❌ Erreur création graphique:', error)
    }
}

// === GESTION DES ERREURS ===
function showError(section, message) {
    console.error(`❌ Erreur section ${section}:`, message)

    const errorElement = document.getElementById(`${section}-error`)
    if (errorElement) {
        errorElement.textContent = `Erreur: ${message}`
        errorElement.style.display = 'block'
    }
}

// === INITIALISATION DE LA PAGE ===
document.addEventListener('DOMContentLoaded', () => {
    const essentialElements = [
        'holdings-table',
        'allocation-chart',
        'active-cryptos-count',
        'total-value',
        'free-usdc'
    ]

    const missingElements = essentialElements.filter(id => !document.getElementById(id))
    if (missingElements.length > 0) return

    loadAllData()

    if (refreshInterval) clearInterval(refreshInterval)
    refreshInterval = setInterval(() => {
        loadAllData()
    }, 30000)
})

window.loadAllData = loadAllData

// === NETTOYAGE À LA FERMETURE ===
window.addEventListener('beforeunload', () => {
    if (refreshInterval) {
        clearInterval(refreshInterval)
    }

    if (allocationChart) {
        allocationChart.destroy()
    }
})

// === EXPORTS GLOBAUX POUR DEBUG ===
window.loadPortfolioData = loadPortfolioData
window.loadPerformanceData = loadPerformanceData
window.loadAllData = loadAllData
window.portfolioData = portfolioData
window.allocationChart = allocationChart

console.log('📄 Fin du chargement portfolio.js complet')