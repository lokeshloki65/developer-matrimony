// Firebase Configuration
const firebaseConfig = {
    apiKey: "YOUR_API_KEY",
    authDomain: "YOUR_AUTH_DOMAIN",
    projectId: "YOUR_PROJECT_ID",
    storageBucket: "YOUR_STORAGE_BUCKET",
    messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
    appId: "YOUR_APP_ID"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
const db = firebase.firestore();

// Auth State Observer
auth.onAuthStateChanged(async (user) => {
    if (user) {
        console.log('User signed in:', user.uid);
        localStorage.setItem('userId', user.uid);
        
        // Get ID token for API calls
        const token = await user.getIdToken();
        localStorage.setItem('authToken', token);
        
        // Load main app
        loadMainApp();
    } else {
        console.log('User signed out');
        showLoginPage();
    }
});

// Login Function
async function login(email, password) {
    try {
        const userCredential = await auth.signInWithEmailAndPassword(email, password);
        return { success: true, user: userCredential.user };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

// Register Function
async function register(email, password, profileData) {
    try {
        // Create user account
        const userCredential = await auth.createUserWithEmailAndPassword(email, password);
        const user = userCredential.user;
        
        // Create profile via backend
        const token = await user.getIdToken();
        const response = await fetch(`${API_URL}/api/profiles/create`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(profileData)
        });
        
        if (!response.ok) {
            throw new Error('Failed to create profile');
        }
        
        return { success: true, user };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

// Logout Function
async function logout() {
    try {
        await auth.signOut();
        localStorage.clear();
        window.location.reload();
    } catch (error) {
        console.error('Logout error:', error);
    }
} 
