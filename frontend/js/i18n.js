 
const translations = {
    en: { 
        nav: {
            matches: 'Matches',
            chat: 'Chat',
            profile: 'Profile',
            logout: 'Logout'
        },
        matches: {
            title: 'Your Matches',
            score: 'Match Score',
            connect: 'Connect',
            viewProfile: 'View Profile'
        },
        chatbot: {
            title: 'AI Assistant',
            placeholder: 'Ask me anything...',
            send: 'Send'
        }
    },
    ta: {
        nav: {
            matches: 'பொருத்தங்கள்',
            chat: 'அரட்டை',
            profile: 'சுயவிவரம்',
            logout: 'வெளியேறு'
        },
        matches: {
            title: 'உங்கள் பொருத்தங்கள்',
            score: 'பொருத்த மதிப்பெண்',
            connect: 'இணைக்க',
            viewProfile: 'சுயவிவரத்தைப் பார்க்க'
        },
        chatbot: {
            title: 'AI உதவியாளர்',
            placeholder: 'எதையும் கேளுங்கள்...',
            send: 'அனுப்பு'
        }
    }
};

function setupLanguageToggle() {
    const toggleBtn = document.getElementById('lang-toggle');
    
    toggleBtn.addEventListener('click', () => {
        currentLang = currentLang === 'en' ? 'ta' : 'en';
        localStorage.setItem('language', currentLang);
        updateLanguage();
        toggleBtn.textContent = currentLang === 'en' ? 'தமிழ்' : 'English';
    });
    
    updateLanguage();
}

function updateLanguage() {
    document.querySelectorAll('[data-i18n]').forEach(elem => {
        const key = elem.getAttribute('data-i18n');
        const text = getNestedTranslation(translations[currentLang], key);
        if (text) {
            elem.textContent = text;
        }
    });
}

function getNestedTranslation(obj, path) {
    return path.split('.').reduce((current, key) => current?.[key], obj);
}

function t(key) {
    return getNestedTranslation(translations[currentLang], key) || key;
}