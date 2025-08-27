// Enhanced Trading Bot Dashboard - Page Orders

let ordersData = {
    orders: [],
    history: []
}

function showSectionLoader(id, show = true) {
    const el = document.getElementById(id)
    if (el) el.style.display = show ? 'block' : 'none'
}

// Fonctions de chargement
async function loadOrders() {
    try {
        showSectionLoader('orders-list-loader', true)
        const response = await fetch('/api/orders')
        const data = await response.json()
        ordersData.orders = data.orders || []
        showSectionLoader('orders-list-loader', false)
        return data.orders || []
    } catch (error) {
        showSectionLoader('orders-list-loader', false)
        console.error('❌ Erreur chargement ordres:', error)
        return []
    }
}

async function loadOrdersHistory() {
    try {
        showSectionLoader('orders-history-loader', true)
        const response = await fetch('/api/orders/history')
        const data = await response.json()
        ordersData.history = data.orders || []
        showSectionLoader('orders-history-loader', false)
        return data.orders || []
    } catch (error) {
        showSectionLoader('orders-history-loader', false)
        console.error('❌ Erreur historique ordres:', error)
        return []
    }
}

function computeProfitFromHistory(history) {
    // Profit approximatif: pour chaque exécution, value_sell - unknown buy (we fallback to 0)
    // Since we do not join buy price per history row here, we accumulate executed value only
    return history.reduce((sum, h) => {
        const execValue = (h.execution_price || 0) * (h.execution_qty || 0)
        return sum + execValue
    }, 0)
}

function mapFilledOrdersFromHistory(history) {
    // Map history rows to a uniform order row for the filled filter
    return (history || []).map(h => {
        const date = h.executed_at || h.created_at
        return {
            id: h.oco_order_id,
            symbol: h.symbol,
            quantity: h.execution_qty || h.quantity || 0,
            buy_price: null,
            profit_target: h.profit_target || '',
            stop_loss_price: h.stop_loss_price || 0,
            kept_quantity: h.kept_quantity || 0,
            created_at: date,
            status: h.status || 'FILLED'
        }
    })
}

function updateOrdersStats(_orders) {
    const activeOrders = ordersData.orders.filter(o => o.status === 'ACTIVE')
    const filledHistory = ordersData.history.filter(h => (h.status || '').includes('FILLED'))
    const stopLossOrders = filledHistory.filter(h => (h.status || '') === 'STOP_FILLED')

    document.getElementById('active-orders-count').textContent = activeOrders.length
    document.getElementById('filled-orders-count').textContent = filledHistory.length
    document.getElementById('stop-loss-count').textContent = stopLossOrders.length

    // Profit affiché: somme des valeurs exécutées (approx)
    const profitValue = computeProfitFromHistory(filledHistory)
    document.getElementById('total-profit').textContent = `${profitValue.toFixed(2)} USDC`
}

function filterOrdersByStatus(status) {
    if (!status || status === 'all') return ordersData.orders
    if (status === 'active') return ordersData.orders.filter(o => o.status === 'ACTIVE')
    if (status === 'filled') {
        // Show executed items from history
        return mapFilledOrdersFromHistory(ordersData.history)
    }
    if (status === 'cancelled') return ordersData.orders.filter(o => (o.status || '').toUpperCase().includes('CANCEL'))
    return ordersData.orders
}

function updateOrdersTable(orders) {
    const tbody = document.getElementById('orders-table')
    if (!tbody) return

    if (!orders || orders.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="loading">Aucun ordre trouvé</td></tr>'
        return
    }

    tbody.innerHTML = orders.map(order => {
        const date = new Date(order.created_at)
        const statusClass = (order.status || '').toLowerCase()
        const buyPrice = (order.buy_price != null) ? `${parseFloat(order.buy_price).toFixed(6)} USDC` : '--'

        return `
            <tr>
                <td>
                    <div class="date-time">
                        <div class="date">${date.toLocaleDateString('fr-FR')}</div>
                        <div class="time">${date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}</div>
                    </div>
                </td>
                <td><strong>${order.symbol.replace('USDC', '')}</strong></td>
                <td>${parseFloat(order.quantity || 0).toFixed(6)}</td>
                <td>${buyPrice}</td>
                <td><span class="profit-target">📈 ${order.profit_target ? '+' + order.profit_target + '%' : '--'}</span></td>
                <td>${order.stop_loss_price != null ? parseFloat(order.stop_loss_price).toFixed(6) + ' USDC' : '--'}</td>
                <td>${parseFloat(order.kept_quantity || 0).toFixed(6)}</td>
                <td><span class="order-status ${statusClass}">✅ ${order.status || 'FILLED'}</span></td>
                <td>
                    <button class="action-btn-small" onclick="viewOrderDetails('${order.id || order.oco_order_id || ''}')">Détails</button>
                </td>
            </tr>
        `
    }).join('')
}

function updateHistoryTable(history) {
    const tbody = document.getElementById('orders-history-table')
    if (!tbody) return

    if (history.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="loading">Aucun historique disponible</td></tr>'
        return
    }

    tbody.innerHTML = history.map(item => {
        const date = new Date(item.executed_at || item.created_at)
        const type = item.execution_type === 'PROFIT' ? 'Profit' : (item.execution_type === 'STOP_LOSS' ? 'Stop-loss' : (item.status || 'N/A'))
        const execPrice = (item.execution_price != null) ? `${parseFloat(item.execution_price).toFixed(6)} USDC` : '--'
        const execQty = (item.execution_qty != null) ? parseFloat(item.execution_qty).toFixed(8) : '--'
        const keptQty = (item.kept_quantity != null) ? parseFloat(item.kept_quantity).toFixed(8) : '--'
        return `
            <tr>
                <td>
                    <div class="date-time">
                        <div class="date">${date.toLocaleDateString('fr-FR')}</div>
                        <div class="time">${date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}</div>
                    </div>
                </td>
                <td><strong>${item.symbol.replace('USDC', '')}</strong></td>
                <td>${type}</td>
                <td>${execPrice}</td>
                <td>${execQty}</td>
                <td>${item.status || 'N/A'}</td>
                <td>${keptQty}</td>
            </tr>
        `
    }).join('')
}

function updateLastUpdateTime() {
    const element = document.getElementById('last-update-time')
    if (element) {
        element.textContent = new Date().toLocaleString('fr-FR')
    }
}

window.refreshOrders = async function () {
    const activeBtn = document.querySelector('.filter-btn.active')
    const status = activeBtn ? activeBtn.dataset.filter : 'all'
    await Promise.all([
        loadOrders(),
        loadOrdersHistory()
    ])
    // Respect active filter after refresh
    const filtered = filterOrdersByStatus(status)
    updateOrdersTable(filtered)
    updateOrdersStats(ordersData.orders)
    updateHistoryTable(ordersData.history)
    updateLastUpdateTime()
}

window.viewOrderDetails = function (orderId) {
    // Basic details modal using alert as placeholder
    const hist = ordersData.history.find(h => String(h.oco_order_id) === String(orderId))
    if (hist) {
        alert(`Ordre ${orderId}\nSymbole: ${hist.symbol}\nStatut: ${hist.status}\nPrix exec: ${hist.execution_price || 'N/A'}\nQty exec: ${hist.execution_qty || 'N/A'}`)
        return
    }
    const act = ordersData.orders.find(o => String(o.id) === String(orderId))
    if (act) {
        alert(`Ordre ${orderId}\nSymbole: ${act.symbol}\nStatut: ${act.status}\nPrix achat: ${act.buy_price || 'N/A'}\nQty: ${act.quantity}`)
        return
    }
    alert(`Détails non trouvés pour l'ordre ${orderId}`)
}

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'))
            btn.classList.add('active')
            const status = btn.dataset.filter
            const filtered = filterOrdersByStatus(status)
            updateOrdersTable(filtered)
        })
    })

    window.refreshOrders()
    setInterval(window.refreshOrders, 60000)
})