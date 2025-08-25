// Enhanced Trading Bot Dashboard - JavaScript commun avec header

const CONFIG = {
    refreshInterval: 30000,
    apiBase: '/api'
}

// Fonctions utilitaires
window.formatNumber = function (num, decimals = 2) {
    if (num === null || num === undefined) return '--'
    return parseFloat(num).toFixed(decimals)
}

window.formatCurrency = function (amount) {
    if (amount === null || amount === undefined) return '--'
    return `${formatNumber(amount, 2)} USDC`
}

window.formatDateTime = function (dateStr) {
    if (!dateStr) return '--'
    const date = new Date(dateStr)
    return date.toLocaleString('fr-FR')
}

// Chargement du statut bot pour le header
window.loadBotStatus = async function () {
    try {
        console.log('🤖 Chargement du statut du bot...')

        const response = await fetch('/api/stats')

        if (!response.ok) {
            updateHeaderStatus('error', 'Erreur API')
            return null
        }

        const data = await response.json()
        console.log('✅ Statut bot récupéré:', data)

        // Mettre à jour le header
        updateHeaderStatus(data.bot_status, getStatusText(data.bot_status, data.last_update))

        return data

    } catch (error) {
        console.error('❌ Erreur loadBotStatus:', error)
        updateHeaderStatus('error', 'Connexion échouée')
        return null
    }
}

function getStatusText(status, lastUpdate) {
    switch (status) {
        case 'active':
            return 'Actif'
        case 'idle':
            if (lastUpdate) {
                const lastDate = new Date(lastUpdate)
                const now = new Date()
                const diffHours = Math.floor((now - lastDate) / (1000 * 60 * 60))

                if (diffHours < 1) return 'En attente (<1h)'
                if (diffHours < 24) return `En attente (${diffHours}h)`
                const diffDays = Math.floor(diffHours / 24)
                return `En attente (${diffDays}j)`
            }
            return 'En attente'
        case 'error':
            return 'Erreur'
        default:
            return 'Inconnu'
    }
}

function updateHeaderStatus(status, text) {
    const dot = document.getElementById('header-status-indicator')
    const textElement = document.getElementById('header-status-text')

    if (dot) {
        dot.className = `status-dot ${status}`
    }

    if (textElement) {
        textElement.textContent = text
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    console.log('🤖 Dashboard Enhanced Trading Bot - JS commun initialisé')

    // Chargement initial du statut
    window.loadBotStatus()

    // Refresh automatique du statut header
    setInterval(window.loadBotStatus, 60000)
})

window.CONFIG = CONFIG