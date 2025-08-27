// Enhanced Trading Bot Dashboard - Page principale AMÉLIORÉE

let dashboardData = {
    stats: null,
    orders: null,
    transactions: null
};

async function loadStats() {
    try {
        console.log('📊 Chargement stats...');
        const response = await fetch('/api/stats');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log('📊 Stats reçues:', data);
        
        dashboardData.stats = data;
        
        // Mettre à jour l'interface
        updateStatsUI(data);
        
        // Mettre à jour la date de dernière mise à jour
        updateLastUpdateTime();
        
        return data;
        
    } catch (error) {
        console.error('❌ Erreur chargement stats:', error);
        
        updateStatsUI({
            daily_buys: 'ERR',
            active_oco: 'ERR',
            total_transactions: 'ERR',
            bot_status: 'error'
        });
        
        return null;
    }
}

function updateLastUpdateTime() {
    const element = document.getElementById('last-update-time');
    if (element) {
        const now = new Date();
        element.textContent = now.toLocaleString('fr-FR');
        console.log('✅ Heure mise à jour');
    }
}

function updateStatsUI(stats) {
    console.log('🔄 Mise à jour stats UI...');
    
    // Stats numériques
    const elements = {
        'daily-buys-count': stats.daily_buys || 0,
        'active-oco-count': stats.active_oco || 0,
        'total-transactions-count': stats.total_transactions || 0
    };
    
    Object.entries(elements).forEach(([elementId, value]) => {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
            console.log(`✅ ${elementId}: ${value}`);
        }
    });
    
    // Statut du bot avec plus de détails
    const statusElement = document.getElementById('bot-status-text');
    const statusIndicator = document.getElementById('bot-status-indicator');
    
    if (statusElement) {
        const status = stats.bot_status || 'unknown';
        const lastUpdate = stats.last_update;
        let statusText = 'Inconnu';
        let statusClass = 'status-unknown';
        
        switch(status) {
            case 'active':
                statusText = `🟢 Actif`;
                statusClass = 'status-active';
                break;
            case 'idle':
                // Calculer depuis quand il est inactif
                if (lastUpdate) {
                    const lastDate = new Date(lastUpdate);
                    const now = new Date();
                    const diffHours = Math.floor((now - lastDate) / (1000 * 60 * 60));
                    
                    if (diffHours < 1) {
                        statusText = `🟡 Inactif (<1h)`;
                    } else if (diffHours < 24) {
                        statusText = `🟡 Inactif (${diffHours}h)`;
                    } else {
                        const diffDays = Math.floor(diffHours / 24);
                        statusText = `🟡 Inactif (${diffDays}j)`;
                    }
                } else {
                    statusText = '🟡 En attente';
                }
                statusClass = 'status-idle';
                break;
            case 'error':
                statusText = '🔴 Erreur';
                statusClass = 'status-error';
                break;
            default:
                statusText = '⚫ Inconnu';
                statusClass = 'status-unknown';
        }
        
        statusElement.textContent = statusText;
        
        // Ajouter classe CSS si élément indicateur existe
        if (statusIndicator) {
            statusIndicator.className = `status-indicator ${statusClass}`;
        }
        
        console.log(`✅ Statut bot: ${statusText}`);
    }
    
    console.log('✅ Stats UI mises à jour');
}

async function loadTransactions() {
    try {
        console.log('📈 Chargement transactions...');
        const response = await fetch('/api/stats/transactions');
        
        if (!response.ok) {
            console.warn(`⚠️ Erreur transactions: ${response.status}`);
            return [];
        }
        
        const data = await response.json();
        console.log('📈 Transactions reçues:', data);
        
        dashboardData.transactions = data.transactions || [];
        updateTransactionsTable(data.transactions || []);
        
        return data.transactions || [];
        
    } catch (error) {
        console.error('❌ Erreur chargement transactions:', error);
        return [];
    }
}

async function loadOrders() {
    try {
        console.log('🎯 Chargement ordres...');
        const response = await fetch('/api/orders');
        
        if (!response.ok) {
            console.warn(`⚠️ Erreur ordres: ${response.status}`);
            return [];
        }
        
        const data = await response.json();
        console.log('🎯 Ordres reçus:', data);
        
        dashboardData.orders = data.orders || [];
        updateOrdersTable(data.orders || []);
        
        return data.orders || [];
        
    } catch (error) {
        console.error('❌ Erreur chargement ordres:', error);
        return [];
    }
}

function updateTransactionsTable(transactions) {
    console.log('📈 Mise à jour tableau transactions...');
    
    const tbody = document.getElementById('recent-transactions-table');
    if (!tbody) {
        console.warn('⚠️ Tableau transactions non trouvé');
        return;
    }
    
    if (!transactions || transactions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading">Aucune transaction récente</td></tr>';
        return;
    }
    
    tbody.innerHTML = transactions.slice(0, 8).map(tx => {
        const sideClass = tx.side === 'BUY' ? 'buy' : 'sell';
        const sideIcon = tx.side === 'BUY' ? '📈' : '📉';
        const sideText = tx.side === 'BUY' ? 'Achat' : 'Vente';
        const date = new Date(tx.created_at);
        const dateStr = date.toLocaleDateString('fr-FR');
        const timeStr = date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
        
        return `
            <tr>
                <td>
                    <div class="date-time">
                        <div class="date">${dateStr}</div>
                        <div class="time">${timeStr}</div>
                    </div>
                </td>
                <td><strong>${tx.symbol.replace('USDC', '')}</strong></td>
                <td><span class="transaction-side ${sideClass}">${sideIcon} ${sideText}</span></td>
                <td>${parseFloat(tx.quantity).toFixed(6)}</td>
                <td><strong>${parseFloat(tx.value).toFixed(2)} USDC</strong></td>
            </tr>
        `;
    }).join('');
    
    console.log(`✅ ${transactions.length} transactions affichées`);
}

function updateOrdersTable(orders) {
    console.log('🎯 Mise à jour tableau ordres...');
    
    const tbody = document.getElementById('active-orders-table');
    if (!tbody) {
        console.warn('⚠️ Tableau ordres non trouvé');
        return;
    }
    
    if (!orders || orders.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading">Aucun ordre OCO actif</td></tr>';
        return;
    }
    
    tbody.innerHTML = orders.slice(0, 8).map(order => {
        const date = new Date(order.created_at);
        const dateStr = date.toLocaleDateString('fr-FR');
        const timeStr = date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
        const profitTarget = parseFloat(order.profit_target).toFixed(1);
        
        return `
            <tr>
                <td>
                    <div class="date-time">
                        <div class="date">${dateStr}</div>
                        <div class="time">${timeStr}</div>
                    </div>
                </td>
                <td><strong>${order.symbol.replace('USDC', '')}</strong></td>
                <td>${parseFloat(order.quantity).toFixed(6)}</td>
                <td><span class="profit-target">🎯 +${profitTarget}%</span></td>
                <td><span class="status-badge status-active">🟢 Actif</span></td>
            </tr>
        `;
    }).join('');
    
    console.log(`✅ ${orders.length} ordres affichés`);
}

async function refreshDashboard() {
    console.log('🔄 Refresh dashboard principal...');
    
    try {
        const [stats, transactions, orders] = await Promise.all([
            loadStats(),
            loadTransactions(),
            loadOrders()
        ]);
        
        console.log('✅ Dashboard principal refreshé avec succès');
        
    } catch (error) {
        console.error('❌ Erreur refresh dashboard:', error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('📊 Page Dashboard principale initialisée');
    
    const criticalElements = [
        'daily-buys-count',
        'active-oco-count', 
        'total-transactions-count',
        'bot-status-text'
    ];
    
    const missingElements = criticalElements.filter(id => !document.getElementById(id));
    if (missingElements.length > 0) {
        console.warn('⚠️ Éléments manquants:', missingElements);
    } else {
        console.log('✅ Éléments dashboard détectés');
        
        // Premier refresh immédiat
        refreshDashboard();
        
        // Refresh automatique toutes les 30 secondes
        setInterval(refreshDashboard, 30000);
    }
});

// Export pour debug
window.dashboardData = dashboardData;
window.refreshDashboard = refreshDashboard;
