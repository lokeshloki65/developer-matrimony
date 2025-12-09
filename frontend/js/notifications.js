const messaging = firebase.messaging();

async function requestNotificationPermission() {
    try { 
        const permission = await Notification.requestPermission();
        
        if (permission === 'granted') {
            console.log('Notification permission granted');
            
            // Get FCM token
            const token = await messaging.getToken({
                vapidKey: 'YOUR_VAPID_KEY'
            });
            
            console.log('FCM Token:', token);
            
            // Save token to user profile
            const userId = localStorage.getItem('userId');
            if (userId) {
                await db.collection('users').doc(userId).update({
                    fcmToken: token,
                    fcmTokenUpdatedAt: firebase.firestore.FieldValue.serverTimestamp()
                });
            }
            
            return token;
        } else {
            console.log('Notification permission denied');
            return null;
        }
    } catch (error) {
        console.error('Error requesting notification permission:', error);
        return null;
    }
}

// Handle foreground messages
messaging.onMessage((payload) => {
    console.log('Received foreground message:', payload);
    
    // Show custom notification
    showNotification(payload.notification.title, payload.notification.body);
    
    // Update notification badge
    updateNotificationBadge();
});

function showNotification(title, body) {
    const notificationEl = document.createElement('div');
    notificationEl.className = 'notification-toast';
    notificationEl.innerHTML = `
        <div class="notification-content">
            <h4>${title}</h4>
            <p>${body}</p>
        </div>
        <button onclick="this.parentElement.remove()">×</button>
    `;
    
    document.body.appendChild(notificationEl);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notificationEl.remove();
    }, 5000);
}

async function updateNotificationBadge() {
    try {
        const userId = localStorage.getItem('userId');
        const unreadQuery = await db.collection('notifications')
            .where('userId', '==', userId)
            .where('read', '==', false)
            .get();
        
        const unreadCount = unreadQuery.size;
        
        const badge = document.getElementById('notification-badge');
        if (badge) {
            badge.textContent = unreadCount;
            badge.style.display = unreadCount > 0 ? 'block' : 'none';
        }
    } catch (error) {
        console.error('Error updating notification badge:', error);
    }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    requestNotificationPermission();
    updateNotificationBadge();
    
    // Update badge every minute
    setInterval(updateNotificationBadge, 60000);
});