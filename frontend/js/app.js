const API_URL = 'http://localhost:5000'; // Change in production

let currentUser = null;
let currentLang = localStorage.getItem('language') || 'en';

// Initialize app
function initApp() {
    setupEventListeners();
    setupLanguageToggle();
    setupChatbot();
}

function setupEventListeners() {
    document.getElementById('logout-btn')?.addEventListener('click', logout);
    
    // Navigation
    document.querySelectorAll('a[href^="#"]').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = e.target.getAttribute('href').slice(1);
            loadPage(page);
        });
    });
}

async function loadPage(page) {
    const content = document.getElementById('main-content');
    
    switch(page) {
        case 'matches':
            content.innerHTML = await renderMatchesPage();
            break;
        case 'chat':
            content.innerHTML = await renderChatPage();
            break;
        case 'profile':
            content.innerHTML = await renderProfilePage();
            break;
        default:
            content.innerHTML = await renderMatchesPage();
    }
}

async function renderMatchesPage() {
    try {
        const token = localStorage.getItem('authToken');
        const response = await fetch(`${API_URL}/api/matches/discover?limit=20`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error);
        }
        
        const matches = data.matches;
        
        return `
            <div class="matches-container">
                <h2 data-i18n="matches.title">Your Matches</h2>
                <div class="matches-grid">
                    ${matches.map(match => `
                        <div class="match-card" data-user-id="${match.userId}">
                            <div class="match-photo">
                                <img src="${match.profile.photos?.[0]?.url || 'assets/default-avatar.png'}" 
                                     alt="${match.profile.fullName}">
                            </div>
                            <div class="match-info">
                                <h3>${match.profile.fullName}</h3>
                                <p class="match-score">Match Score: ${match.matchScore}%</p>
                                <p>${match.profile.developerInfo.role}</p>
                                <p>${match.profile.city}, ${match.profile.state}</p>
                                <div class="tech-tags">
                                    ${match.profile.developerInfo.techStack.slice(0, 3).map(tech => 
                                        `<span class="tech-tag">${tech}</span>`
                                    ).join('')}
                                </div>
                                <div class="match-actions">
                                    <button class="btn-primary" onclick="sendMatchRequest('${match.userId}')">
                                        Connect
                                    </button>
                                    <button class="btn-secondary" onclick="viewProfile('${match.userId}')">
                                        View Profile
                                    </button>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error loading matches:', error);
        return `<div class="error">Failed to load matches</div>`;
    }
}

async function sendMatchRequest(userId) {
    try {
        const token = localStorage.getItem('authToken');
        const response = await fetch(`${API_URL}/api/matches/send-request`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ receiverId: userId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Match request sent successfully!');
        } else {
            alert(data.error);
        }
    } catch (error) {
        console.error('Error sending request:', error);
        alert('Failed to send request');
    }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', initApp); 
