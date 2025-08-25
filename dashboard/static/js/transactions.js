// Enhanced Trading Bot Dashboard - Page Transactions

let transactionsData = {
    transactions: [],
    summary: {}
}

let transactionsChart = null

function showSectionLoader(id, show = true) {
    const el = document.getElementById(id)
    if (el) el.style.display = show ? 'block' : 'none'
}

// Fonctions de chargement
async function loadTransactions(period = 'all') {
    try {
        showSectionLoader('transactions-list-loader', true)
        showSectionLoader('transactions-chart-loader', true)
        showSectionLoader('crypto-stats-loader', true)

        const response = await fetch(`/api/stats/transactions?period=${encodeURIComponent(period)}&limit=200`)
        const data = await response.json()

        transactionsData.transactions = data.transactions || []
        updateTransactionsTable(data.transactions || [])
        updateTransactionsSummary(data.transactions || [])
        updateCryptoStats(data.transactions || [])
        updateTransactionsChart(data.transactions || [])

        showSectionLoader('transactions-list-loader', false)
        showSectionLoader('transactions-chart-loader', false)
        showSectionLoader('crypto-stats-loader', false)

        return data.transactions || []
    } catch (error) {
        console.error('❌ Erreur chargement transactions:', error)
        showSectionLoader('transactions-list-loader', false)
        showSectionLoader('transactions-chart-loader', false)
        showSectionLoader('crypto-stats-loader', false)
        return []
    }
}

function updateTransactionsSummary(transactions) {
    const buys = transactions.filter(t => t.side === 'BUY')
    const sells = transactions.filter(t => t.side === 'SELL')
    const totalVolume = transactions.reduce((sum, t) => sum + (t.value || 0), 0)
    const avgTradeSize = transactions.length ? totalVolume / transactions.length : 0

    document.getElementById('total-buys').textContent = buys.length
    document.getElementById('total-sells').textContent = sells.length
    document.getElementById('total-volume').textContent = `${totalVolume.toFixed(2)} USDC`
    document.getElementById('avg-trade-size').textContent = `${avgTradeSize.toFixed(2)} USDC`
}

function updateTransactionsTable(transactions) {
    const tbody = document.getElementById('transactions-table')
    if (!tbody) return

    if (transactions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="loading">Aucune transaction trouvée</td></tr>'
        return
    }

    tbody.innerHTML = transactions.map(tx => {
        const date = new Date(tx.created_at)
        const sideClass = tx.side === 'BUY' ? 'buy' : 'sell'
        const sideIcon = tx.side === 'BUY' ? '📈' : '📉'

        return `
            <tr class="transaction-row">
                <td>
                    <div class="date-time">
                        <div class="date">${date.toLocaleDateString('fr-FR')}</div>
                        <div class="time">${date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}</div>
                    </div>
                </td>
                <td><code style="font-size: 0.8rem;">${tx.order_id || '--'}</code></td>
                <td><strong>${tx.symbol.replace('USDC', '')}</strong></td>
                <td><span class="transaction-side ${sideClass}">${sideIcon} ${tx.side}</span></td>
                <td>${parseFloat(tx.price).toFixed(6)} USDC</td>
                <td>${parseFloat(tx.quantity).toFixed(8)}</td>
                <td><strong>${parseFloat(tx.value || 0).toFixed(2)} USDC</strong></td>
                <td>-- USDC</td>
                <td><span class="status-badge status-active">✅ Confirmé</span></td>
            </tr>
        `
    }).join('')
}

function updateCryptoStats(transactions) {
    const tbody = document.getElementById('crypto-stats-table')
    if (!tbody) return

    const cryptoStats = {}
    transactions.forEach(tx => {
        const symbol = tx.symbol
        if (!cryptoStats[symbol]) {
            cryptoStats[symbol] = {
                buys: 0,
                sells: 0,
                volume: 0,
                lastTransaction: null
            }
        }

        if (tx.side === 'BUY') cryptoStats[symbol].buys++
        if (tx.side === 'SELL') cryptoStats[symbol].sells++
        cryptoStats[symbol].volume += tx.value || 0

        if (!cryptoStats[symbol].lastTransaction ||
            new Date(tx.created_at) > new Date(cryptoStats[symbol].lastTransaction)) {
            cryptoStats[symbol].lastTransaction = tx.created_at
        }
    })

    const rows = Object.entries(cryptoStats).map(([symbol, stats]) => {
        const lastDate = stats.lastTransaction ?
            new Date(stats.lastTransaction).toLocaleDateString('fr-FR') : '--'

        return `
            <tr>
                <td><strong>${symbol.replace('USDC', '')}</strong></td>
                <td>${stats.buys}</td>
                <td>${stats.sells}</td>
                <td>${stats.volume.toFixed(2)} USDC</td>
                <td>${lastDate}</td>
            </tr>
        `
    })

    tbody.innerHTML = rows.length ? rows.join('') :
        '<tr><td colspan="5" class="loading">Aucune donnée</td></tr>'

    updateMetrics(transactions)
}

function updateTransactionsChart(transactions) {
    const canvas = document.getElementById('transactions-volume-chart')
    if (!canvas) return

    // Grouper par date (YYYY-MM-DD)
    const byDay = {}
    transactions.forEach(tx => {
        const d = new Date(tx.created_at)
        const key = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0')
        byDay[key] = (byDay[key] || 0) + (tx.value || 0)
    })

    const labels = Object.keys(byDay).sort()
    const values = labels.map(k => parseFloat(byDay[k].toFixed(2)))

    if (transactionsChart) {
        transactionsChart.destroy()
    }

    const ctx = canvas.getContext('2d')
    transactionsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Volume (USDC)',
                data: values,
                backgroundColor: 'rgba(99, 102, 241, 0.5)',
                borderColor: '#6366f1',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: { ticks: { autoSkip: true, maxTicksLimit: 10 } },
                y: { beginAtZero: true }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function (ctx) { return `${ctx.parsed.y.toFixed(2)} USDC` }
                    }
                }
            }
        }
    })
}

function updateMetrics(transactions) {
    const biggestTrade = Math.max(0, ...transactions.map(t => t.value || 0))
    const buys = transactions.filter(t => t.side === 'BUY').length
    const sells = transactions.filter(t => t.side === 'SELL').length
    const total = buys + sells

    const buyPercentage = total ? ((buys / total) * 100).toFixed(0) : 0
    const sellPercentage = total ? ((sells / total) * 100).toFixed(0) : 0

    document.getElementById('trade-frequency').textContent = `${total} tx`
    document.getElementById('total-commission').textContent = '-- USDC'
    document.getElementById('biggest-trade').textContent = `${biggestTrade.toFixed(2)} USDC`
    document.getElementById('buy-sell-ratio').textContent = `${buyPercentage}% / ${sellPercentage}%`
}

function updateLastUpdateTime() {
    const element = document.getElementById('last-update-time')
    if (element) {
        element.textContent = new Date().toLocaleString('fr-FR')
    }
}

window.refreshTransactions = async function () {
    const activeBtn = document.querySelector('.period-btn.active')
    const period = activeBtn ? activeBtn.dataset.period : 'all'
    await loadTransactions(period)
    updateLastUpdateTime()
}

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'))
            btn.classList.add('active')
            await loadTransactions(btn.dataset.period)
        })
    })

    window.refreshTransactions()
    setInterval(window.refreshTransactions, 60000)
})