// Enhanced Trading Bot Dashboard - JavaScript

// Configuration
const CONFIG = {
    refreshInterval: 30000, // 30 secondes
    apiBase: '/api'
};

// État global
let isLoading = false;

// Fonctions utilitaires
function formatNumber(num, decimals = 2) {
    if (num === null || num === undefined) return '--';
    return parseFloat(num).toFixed(decimals);
}

function formatCurrency(amount) {
    if (amount === null || amount === undefined) return '--';
    return `${formatNumber(amount, 2)} USDC`;
}

function formatDateTime(dateStr) {
    if (!dateStr) return '--';
    const date = new Date(dateStr);
    return date.toLocaleString('fr-FR');
}

function formatTime(dateStr) {
    if (!dateStr) return '--';
    const date = new Date(dateStr);
    return date.toLocaleTimeString('fr-FR');
}

// Fonction sécurisée pour mettre à jour le contenu
function safeSetContent(elementId, content) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = content;
        return true;
    } else {
        console.warn(`Élément non trouvé: ${elementId}`);
        return false;
    }
}

// Mise à jour du statut
function updateStatus(status) {
    const indicator = document.getElementById('status-indicator');
    const text = document.getElementById('status-text');
    
    if (!indicator || !text) {
        console.warn('Éléments status non trouvés dans le DOM');
        return;
    }
    
    // Nettoyer les classes
    indicator.className = '';
    
    switch(status) {
        case 'active':
            indicator.className = 'status-active';
            text.textContent = 'Actif';
            break;
        case 'idle':
            indicator.className = 'status-idle';
            text.textContent = 'En attente';
            break;
        default:
            indicator.className = 'status-unknown';
            text.textContent = 'Inconnu';
    }
}

// Charger les statistiques
async function loadStats() {
    try {
        const response = await fetch(`${CONFIG.apiBase}/stats`);
        const data = await response.json();
        
        if (data.error) {
            console.error('Erreur stats:', data.error);
            return;
        }
        
        // Mise à jour des cartes stats avec vérifications
        safeSetContent('daily-buys', `${data.daily_buys || 0}/100`);
        safeSetContent('active-oco', data.active_oco || 0);
        safeSetContent('total-transactions', data.total_transactions || 0);
        safeSetContent('bot-status', data.bot_status || 'unknown');
        
        // Mise à jour du statut navbar
        updateStatus(data.bot_status);
        
        // Dernière mise à jour
        safeSetContent('last-update', formatDateTime(data.timestamp));
        
        console.log('Stats chargées:', data);
        
    } catch (error) {
        console.error('Erreur chargement stats:', error);
    }
}

// Charger les transactions
async function loadTransactions() {
    try {
        const response = await fetch(`${CONFIG.apiBase}/stats/transactions`);
        const data = await response.json();
        
        const tbody = document.getElementById('transactions-table');
        if (!tbody) {
            console.warn('Table transactions non trouvée');
            return;
        }
        
        if (data.error || !data.transactions) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading">Erreur chargement</td></tr>';
            return;
        }
        
        if (data.transactions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading">Aucune transaction récente</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.transactions.map(tx => `
            <tr>
                <td>${formatTime(tx.created_at)}</td>
                <td>${tx.symbol}</td>
                <td><span class="${tx.side.toLowerCase()}">${tx.side}</span></td>
                <td>${formatNumber(tx.quantity, 8)}</td>
                <td>${formatCurrency(tx.price)}</td>
                <td>${formatCurrency(tx.value)}</td>
            </tr>
        `).join('');
        
        console.log(`Transactions chargées: ${data.transactions.length}`);
        
    } catch (error) {
        console.error('Erreur chargement transactions:', error);
        const tbody = document.getElementById('transactions-table');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading">Erreur réseau</td></tr>';
        }
    }
}

// Charger les ordres OCO
async function loadOrders() {
    try {
        const response = await fetch(`${CONFIG.apiBase}/orders`);
        const data = await response.json();
        
        const tbody = document.getElementById('orders-table');
        if (!tbody) {
            console.warn('Table ordres non trouvée');
            return;
        }
        
        if (data.error || !data.orders) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading">Erreur chargement</td></tr>';
            return;
        }
        
        if (data.orders.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading">Aucun ordre OCO actif</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.orders.map(order => `
            <tr>
                <td>${order.symbol}</td>
                <td>${formatNumber(order.quantity, 8)}</td>
                <td>${formatNumber(order.kept_quantity, 8)}</td>
                <td>+${formatNumber(order.profit_target, 1)}%</td>
                <td>${formatCurrency(order.stop_loss_price)}</td>
                <td>${formatTime(order.created_at)}</td>
            </tr>
        `).join('');
        
        console.log(`Ordres OCO chargés: ${data.orders.length}`);
        
    } catch (error) {
        console.error('Erreur chargement ordres:', error);
        const tbody = document.getElementById('orders-table');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading">Erreur réseau</td></tr>';
        }
    }
}

// Rafraîchir tout le dashboard
async function refreshDashboard() {
    if (isLoading) {
        console.log('Refresh déjà en cours, ignoré');
        return;
    }
    
    isLoading = true;
    console.log('🔄 Refresh dashboard...');
    
    try {
        await Promise.all([
            loadStats(),
            loadTransactions(),
            loadOrders()
        ]);
        console.log('✅ Dashboard refreshé avec succès');
    } catch (error) {
        console.error('❌ Erreur refresh dashboard:', error);
    } finally {
        isLoading = false;
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    console.log('🤖 Dashboard Enhanced Trading Bot initialisé');
    console.log('DOM éléments trouvés:');
    console.log('- daily-buys:', !!document.getElementById('daily-buys'));
    console.log('- active-oco:', !!document.getElementById('active-oco'));
    console.log('- total-transactions:', !!document.getElementById('total-transactions'));
    console.log('- bot-status:', !!document.getElementById('bot-status'));
    console.log('- transactions-table:', !!document.getElementById('transactions-table'));
    console.log('- orders-table:', !!document.getElementById('orders-table'));
    
    // Premier chargement
    refreshDashboard();
});

// Export pour usage global
window.refreshDashboard = refreshDashboard;
window.loadStats = loadStats;
window.loadTransactions = loadTransactions;
window.loadOrders = loadOrders;
