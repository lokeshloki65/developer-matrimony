const API_URL = 'http://localhost:5000';

// Load dashboard on init
async function loadDashboard() {
    try {
        const token = localStorage.getItem('authToken');
        const response = await fetch(`${API_URL}/api/admin/dashboard`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error);
        }
        
        // Update stats
        document.getElementById('total-users').textContent = data.stats.totalUsers;
        document.getElementById('active-users').textContent = data.stats.activeUsers;
        document.getElementById('pending-verifications').textContent = data.stats.pendingVerifications;
        document.getElementById('total-matches').textContent = data.stats.totalMatches;
        document.getElementById('pending-reports').textContent = data.stats.pendingReports;
        document.getElementById('premium-users').textContent = data.stats.premiumUsers;
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        alert('Failed to load dashboard. Please check if you have admin access.');
    }
}

// Load users list
async function loadUsers(filter = 'all', page = 1) {
    try {
        const token = localStorage.getItem('authToken');
        const response = await fetch(
            `${API_URL}/api/admin/users?filter=${filter}&page=${page}&limit=20`,
            { headers: { 'Authorization': `Bearer ${token}` } }
        );
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error);
        }
        
        renderUsersTable(data.users);
        
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

function renderUsersTable(users) {
    const tbody = document.getElementById('users-tbody');
    tbody.innerHTML = users.map(user => `
        <tr>
            <td>
                <div class="user-cell">
                    <img src="${user.photos?.[0]?.url || 'assets/default-avatar.png'}" 
                         alt="${user.fullName}" class="user-avatar">
                    <span>${user.fullName}</span>
                </div>
            </td>
            <td>${user.email}</td>
            <td>${user.phone || 'N/A'}</td>
            <td>
                <span class="badge ${user.verification.profileVerified ? 'badge-success' : 'badge-warning'}">
                    ${user.verification.profileVerified ? 'Verified' : 'Pending'}
                </span>
            </td>
            <td>
                <span class="badge ${user.isPremium ? 'badge-premium' : 'badge-free'}">
                    ${user.isPremium ? 'Premium' : 'Free'}
                </span>
            </td>
            <td>
                <button onclick="viewUser('${user.id}')" class="btn-sm btn-primary">View</button>
                <button onclick="verifyUser('${user.id}')" class="btn-sm btn-success">Verify</button>
                <button onclick="suspendUser('${user.id}')" class="btn-sm btn-danger">Suspend</button>
            </td>
        </tr>
    `).join('');
}

// Verify user
async function verifyUser(userId) {
    if (!confirm('Verify this user profile?')) return;
    
    try {
        const token = localStorage.getItem('authToken');
        const response = await fetch(`${API_URL}/api/admin/verify-user/${userId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ type: 'profile' })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('User verified successfully');
            loadUsers();
        } else {
            alert(data.error);
        }
    } catch (error) {
        console.error('Error verifying user:', error);
        alert('Failed to verify user');
    }
}

// Load reports
async function loadReports(status = 'pending') {
    try {
        const token = localStorage.getItem('authToken');
        const response = await fetch(
            `${API_URL}/api/admin/reports?status=${status}`,
            { headers: { 'Authorization': `Bearer ${token}` } }
        );
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error);
        }
        
        renderReportsTable(data.reports);
        
    } catch (error) {
        console.error('Error loading reports:', error);
    }
}

function renderReportsTable(reports) {
    const tbody = document.getElementById('reports-tbody');
    tbody.innerHTML = reports.map(report => `
        <tr>
            <td>${report.reporter?.name || 'Unknown'}</td>
            <td>${report.reported?.name || 'Unknown'}</td>
            <td>${report.reason}</td>
            <td>${report.description || 'N/A'}</td>
            <td>${new Date(report.createdAt._seconds * 1000).toLocaleString()}</td>
            <td>
                <button onclick="resolveReport('${report.id}', 'dismiss')" class="btn-sm btn-secondary">Dismiss</button>
                <button onclick="resolveReport('${report.id}', 'warn')" class="btn-sm btn-warning">Warn</button>
                <button onclick="resolveReport('${report.id}', 'suspend')" class="btn-sm btn-danger">Suspend</button>
            </td>
        </tr>
    `).join('');
}

async function resolveReport(reportId, action) {
    if (!confirm(`${action.toUpperCase()} this reported user?`)) return;
    
    try {
        const token = localStorage.getItem('authToken');
        const response = await fetch(`${API_URL}/api/admin/reports/${reportId}/resolve`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ action })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Report resolved successfully');
            loadReports();
        } else {
            alert(data.error);
        }
    } catch (error) {
        console.error('Error resolving report:', error);
        alert('Failed to resolve report');
    }
}

// Broadcast notification
async function sendBroadcast() {
    const title = document.getElementById('broadcast-title').value;
    const message = document.getElementById('broadcast-message').value;
    const filter = document.getElementById('broadcast-filter').value;
    
    if (!title || !message) {
        alert('Please fill all fields');
        return;
    }
    
    if (!confirm(`Send notification to ${filter} users?`)) return;
    
    try {
        const token = localStorage.getItem('authToken');
        const response = await fetch(`${API_URL}/api/admin/broadcast`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title, message, filter })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(data.message);
            document.getElementById('broadcast-title').value = '';
            document.getElementById('broadcast-message').value = '';
        } else {
            alert(data.error);
        }
    } catch (error) {
        console.error('Error sending broadcast:', error);
        alert('Failed to send broadcast');
    }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
});