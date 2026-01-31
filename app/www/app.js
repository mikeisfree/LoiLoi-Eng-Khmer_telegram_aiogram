/**
 * LoiLoi Translator - Main Application
 * Voice translator with multi-language support
 */

// ========================================
// Languages Configuration
// ========================================

const LANGUAGES = {
    en: { name: 'English', flag: '🇬🇧' },
    km: { name: 'ខ្មែរ (Khmer)', flag: '🇰🇭' },
    pl: { name: 'Polski', flag: '🇵🇱' }
};

// ========================================
// Translations (i18n)
// ========================================

const translations = {
    en: {
        ready: 'Ready',
        recording: 'Recording...',
        processing: 'Processing...',
        holdToRecord: 'Hold to record',
        original: 'Original',
        translation: 'Translation',
        settings: 'Settings',
        apiKeyLabel: 'Gemini API Key',
        apiKeyHint: 'Get your key from Google AI Studio',
        getApiKey: 'Get API Key →',
        save: 'Save',
        noApiKey: 'Please set your API key in Settings',
        noApiKeyWarning: 'Please set your API key in Settings ⚙️',
        select2Languages: 'Select 2 languages to translate',
        apiKeySaved: 'API key saved!',
        errorRecording: 'Could not access microphone',
        errorProcessing: 'Error processing audio',
        errorNetwork: 'Network error. Please try again.',
    },
    km: {
        ready: 'រួចរាល់',
        recording: 'កំពុងថត...',
        processing: 'កំពុងដំណើរការ...',
        holdToRecord: 'សង្កត់ដើម្បីថត',
        original: 'ដើម',
        translation: 'ការបកប្រែ',
        settings: 'ការកំណត់',
        apiKeyLabel: 'Gemini API Key',
        apiKeyHint: 'យក key ពី Google AI Studio',
        getApiKey: 'យក API Key →',
        save: 'រក្សាទុក',
        noApiKey: 'សូមកំណត់ API key របស់អ្នកក្នុង Settings',
        noApiKeyWarning: 'សូមកំណត់ API key នៅ Settings ⚙️',
        select2Languages: 'ជ្រើសរើសភាសា 2 ដើម្បីបកប្រែ',
        apiKeySaved: 'រក្សាទុក API key ហើយ!',
        errorRecording: 'មិនអាចប្រើមីក្រូហ្វូន',
        errorProcessing: 'កំហុសក្នុងការដំណើរការសំឡេង',
        errorNetwork: 'កំហុសបណ្តាញ។ សូមព្យាយាមម្តងទៀត។',
    },
    pl: {
        ready: 'Gotowy',
        recording: 'Nagrywanie...',
        processing: 'Przetwarzanie...',
        holdToRecord: 'Przytrzymaj aby nagrać',
        original: 'Oryginał',
        translation: 'Tłumaczenie',
        settings: 'Ustawienia',
        apiKeyLabel: 'Klucz API Gemini',
        apiKeyHint: 'Pobierz klucz z Google AI Studio',
        getApiKey: 'Pobierz klucz API →',
        save: 'Zapisz',
        noApiKey: 'Ustaw klucz API w Ustawieniach',
        noApiKeyWarning: 'Ustaw klucz API w Ustawieniach ⚙️',
        select2Languages: 'Wybierz 2 języki do tłumaczenia',
        apiKeySaved: 'Klucz API zapisany!',
        errorRecording: 'Brak dostępu do mikrofonu',
        errorProcessing: 'Błąd przetwarzania audio',
        errorNetwork: 'Błąd sieci. Spróbuj ponownie.',
    }
};

// ========================================
// State
// ========================================

const state = {
    lang: localStorage.getItem('ui_lang') || 'en',
    apiKey: localStorage.getItem('gemini_api_key') || '',
    selectedLangs: JSON.parse(localStorage.getItem('selected_langs')) || ['en', 'km'],
    isRecording: false,
    mediaRecorder: null,
    audioChunks: [],
};

// ========================================
// DOM Elements
// ========================================

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const elements = {
    recordBtn: $('#recordBtn'),
    status: $('#status'),
    statusText: $('#status .status-text'),
    originalText: $('#originalText'),
    translationText: $('#translationText'),
    originalCard: $('#originalCard'),
    translationCard: $('#translationCard'),
    settingsBtn: $('#settingsBtn'),
    settingsModal: $('#settingsModal'),
    closeSettings: $('#closeSettings'),
    apiKeyInput: $('#apiKey'),
    saveSettings: $('#saveSettings'),
    langSelector: $('#langSelector'),
    toast: $('#toast'),
    apiWarning: $('#apiWarning'),
    langWarning: $('#langWarning'),
};

// ========================================
// i18n
// ========================================

function t(key) {
    return translations[state.lang]?.[key] || translations.en[key] || key;
}

function updateUI() {
    // Update all data-i18n elements
    $$('[data-i18n]').forEach(el => {
        const key = el.dataset.i18n;
        if (key) el.textContent = t(key);
    });
    
    // Update language flag buttons
    $$('.lang-flag-btn').forEach(btn => {
        const lang = btn.dataset.lang;
        btn.classList.toggle('active', state.selectedLangs.includes(lang));
    });
    
    // Show/hide language warning
    updateLangWarning();
    
    // Update API warning visibility
    updateApiWarning();
}

function updateLangWarning() {
    if (elements.langWarning) {
        const hasTwo = state.selectedLangs.length === 2;
        elements.langWarning.style.display = hasTwo ? 'none' : 'flex';
    }
}

function updateApiWarning() {
    if (elements.apiWarning) {
        elements.apiWarning.style.display = state.apiKey ? 'none' : 'flex';
    }
}

// ========================================
// Toast Notifications
// ========================================

function showToast(message, type = 'info') {
    const toast = elements.toast;
    toast.textContent = message;
    toast.className = 'toast show ' + type;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// ========================================
// Settings Modal
// ========================================

function openSettings() {
    elements.apiKeyInput.value = state.apiKey;
    elements.settingsModal.classList.add('open');
}

function closeSettings() {
    elements.settingsModal.classList.remove('open');
}

function saveSettings() {
    state.apiKey = elements.apiKeyInput.value.trim();
    localStorage.setItem('gemini_api_key', state.apiKey);
    closeSettings();
    updateApiWarning();
    showToast(t('apiKeySaved'), 'success');
}

// ========================================
// Audio Recording
// ========================================

async function startRecording() {
    // Check if 2 languages are selected
    if (state.selectedLangs.length !== 2) {
        showToast(t('select2Languages'), 'error');
        return;
    }
    
    if (!state.apiKey) {
        showToast(t('noApiKey'), 'error');
        openSettings();
        return;
    }
    
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                sampleRate: 16000,
                channelCount: 1,
                echoCancellation: true,
                noiseSuppression: true,
            }
        });
        
        // Try to use webm/opus, fallback to whatever is available
        const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') 
            ? 'audio/webm;codecs=opus' 
            : 'audio/webm';
        
        state.mediaRecorder = new MediaRecorder(stream, { mimeType });
        state.audioChunks = [];
        
        state.mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) {
                state.audioChunks.push(e.data);
            }
        };
        
        state.mediaRecorder.onstop = async () => {
            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
            
            // Process audio
            const audioBlob = new Blob(state.audioChunks, { type: mimeType });
            await processAudio(audioBlob);
        };
        
        state.mediaRecorder.start();
        state.isRecording = true;
        
        // Update UI
        elements.recordBtn.classList.add('recording');
        elements.status.classList.add('recording');
        elements.status.classList.remove('processing');
        elements.statusText.textContent = t('recording');
        
    } catch (error) {
        console.error('Recording error:', error);
        showToast(t('errorRecording'), 'error');
    }
}

function stopRecording() {
    if (state.mediaRecorder && state.isRecording) {
        state.mediaRecorder.stop();
        state.isRecording = false;
        
        // Update UI
        elements.recordBtn.classList.remove('recording');
        elements.status.classList.remove('recording');
        elements.status.classList.add('processing');
        elements.statusText.textContent = t('processing');
    }
}

// ========================================
// Gemini API
// ========================================

async function processAudio(audioBlob) {
    try {
        // Convert blob to base64
        const base64Audio = await blobToBase64(audioBlob);
        
        // Call Gemini API
        const result = await callGeminiAPI(base64Audio);
        
        // Update results
        elements.originalText.textContent = result.text || '—';
        elements.translationText.textContent = result.translation || '—';
        
        // Update scroll arrows visibility
        updateScrollArrows();
        
        // Highlight cards
        elements.originalCard.classList.add('highlight');
        elements.translationCard.classList.add('highlight');
        setTimeout(() => {
            elements.originalCard.classList.remove('highlight');
            elements.translationCard.classList.remove('highlight');
        }, 2000);
        
        // Reset status
        elements.status.classList.remove('processing');
        elements.statusText.textContent = t('ready');
        
    } catch (error) {
        console.error('Processing error:', error);
        showToast(t('errorProcessing'), 'error');
        elements.status.classList.remove('processing');
        elements.statusText.textContent = t('ready');
    }
}

function blobToBase64(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => {
            // Remove data URL prefix
            const base64 = reader.result.split(',')[1];
            resolve(base64);
        };
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
}

async function callGeminiAPI(base64Audio) {
    // Build dynamic prompt based on selected languages
    const [lang1, lang2] = state.selectedLangs;
    const name1 = LANGUAGES[lang1]?.name || lang1;
    const name2 = LANGUAGES[lang2]?.name || lang2;
    
    const prompt = `You are a translator for ${name1} and ${name2}.
Task:
1. Listen to the audio and transcribe what is spoken.
2. Detect if the language is ${name1} ('${lang1}') or ${name2} ('${lang2}').
3. Translate it to the other language (${lang1.toUpperCase()}→${lang2.toUpperCase()} or ${lang2.toUpperCase()}→${lang1.toUpperCase()}).

Return ONLY a JSON object with no markdown:
{"lang":"${lang1}","text":"transcribed text","translation":"translated text"}`;

    const response = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${state.apiKey}`,
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                contents: [{
                    parts: [
                        { text: prompt },
                        { 
                            inline_data: { 
                                mime_type: 'audio/webm', 
                                data: base64Audio 
                            } 
                        }
                    ]
                }],
                generationConfig: {
                    temperature: 0.1,
                    maxOutputTokens: 1024,
                }
            })
        }
    );
    
    if (!response.ok) {
        const error = await response.json();
        console.error('API Error:', error);
        throw new Error(error.error?.message || 'API request failed');
    }
    
    const data = await response.json();
    const text = data.candidates?.[0]?.content?.parts?.[0]?.text || '';
    
    // Parse JSON from response
    return parseJSONResponse(text);
}

function parseJSONResponse(text) {
    // Remove markdown code blocks if present
    let cleaned = text.trim();
    if (cleaned.startsWith('```')) {
        const lines = cleaned.split('\n');
        cleaned = lines.slice(1, -1).join('\n');
    }
    
    // Find JSON object
    const start = cleaned.indexOf('{');
    const end = cleaned.lastIndexOf('}');
    
    if (start !== -1 && end !== -1) {
        cleaned = cleaned.slice(start, end + 1);
    }
    
    try {
        return JSON.parse(cleaned);
    } catch (e) {
        console.error('JSON parse error:', e, cleaned);
        return { text: cleaned, translation: '' };
    }
}

// ========================================
// Event Listeners
// ========================================

function initEventListeners() {
    // Record button - hold to record
    elements.recordBtn.addEventListener('mousedown', startRecording);
    elements.recordBtn.addEventListener('mouseup', stopRecording);
    elements.recordBtn.addEventListener('mouseleave', stopRecording);
    
    // Touch events for mobile
    elements.recordBtn.addEventListener('touchstart', (e) => {
        e.preventDefault();
        startRecording();
    });
    elements.recordBtn.addEventListener('touchend', (e) => {
        e.preventDefault();
        stopRecording();
    });
    
    // Settings
    elements.settingsBtn.addEventListener('click', openSettings);
    elements.closeSettings.addEventListener('click', closeSettings);
    elements.saveSettings.addEventListener('click', saveSettings);
    
    // Close modal on backdrop click
    $('.modal-backdrop').addEventListener('click', closeSettings);
    
    // Language selector (max 2 languages)
    if (elements.langSelector) {
        elements.langSelector.addEventListener('click', (e) => {
            const btn = e.target.closest('.lang-flag-btn');
            if (!btn) return;
            
            const lang = btn.dataset.lang;
            const isActive = state.selectedLangs.includes(lang);
            
            if (isActive) {
                // Deselect language
                state.selectedLangs = state.selectedLangs.filter(l => l !== lang);
            } else {
                // Select language (only if less than 2 selected)
                if (state.selectedLangs.length < 2) {
                    state.selectedLangs.push(lang);
                }
                // If already 2 selected, do nothing (user must deselect first)
            }
            
            // Save and update UI
            localStorage.setItem('selected_langs', JSON.stringify(state.selectedLangs));
            updateUI();
        });
    }
    
    // Close settings with Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && elements.settingsModal.classList.contains('open')) {
            closeSettings();
        }
    });
}

// ========================================
// Scroll Arrows
// ========================================

function updateScrollArrows() {
    $$('.result-scroll-wrapper').forEach(wrapper => {
        const content = wrapper.querySelector('.result-content');
        const upArrow = wrapper.querySelector('.scroll-up');
        const downArrow = wrapper.querySelector('.scroll-down');
        
        if (!content || !upArrow || !downArrow) return;
        
        const hasOverflow = content.scrollHeight > content.clientHeight;
        
        if (hasOverflow) {
            // Show/hide arrows based on scroll position
            upArrow.classList.toggle('visible', content.scrollTop > 0);
            downArrow.classList.toggle('visible', 
                content.scrollTop < content.scrollHeight - content.clientHeight - 1);
        } else {
            // No overflow - hide both arrows
            upArrow.classList.remove('visible');
            downArrow.classList.remove('visible');
        }
    });
}

function scrollContent(wrapper, direction) {
    const content = wrapper.querySelector('.result-content');
    if (!content) return;
    
    const scrollAmount = 50;
    content.scrollBy({
        top: direction === 'up' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
    });
    
    // Update arrows after scroll
    setTimeout(updateScrollArrows, 100);
}

function initScrollArrows() {
    // Click handlers for arrows
    $$('.scroll-arrow').forEach(arrow => {
        arrow.addEventListener('click', (e) => {
            const wrapper = e.target.closest('.result-scroll-wrapper');
            const direction = e.target.dataset.direction;
            scrollContent(wrapper, direction);
        });
    });
    
    // Update arrows on scroll
    $$('.result-content').forEach(content => {
        content.addEventListener('scroll', updateScrollArrows);
    });
}

// ========================================
// Initialize
// ========================================

async function requestMicrophonePermission() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        // Stop the stream immediately - we just needed permission
        stream.getTracks().forEach(track => track.stop());
        console.log('Microphone permission granted');
    } catch (error) {
        console.warn('Microphone permission denied:', error);
    }
}

function init() {
    updateUI();
    initEventListeners();
    initScrollArrows();
    
    // Request microphone permission on app load
    requestMicrophonePermission();
}

// Start app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
