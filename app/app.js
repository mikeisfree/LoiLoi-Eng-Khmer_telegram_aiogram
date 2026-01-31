/**
 * LoiLoi Translator - Main Application
 * Voice translator EN ↔️ KM using Gemini API
 */

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
        apiKeySaved: 'រក្សាទុក API key ហើយ!',
        errorRecording: 'មិនអាចប្រើមីក្រូហ្វូន',
        errorProcessing: 'កំហុសក្នុងការដំណើរការសំឡេង',
        errorNetwork: 'កំហុសបណ្តាញ។ សូមព្យាយាមម្តងទៀត។',
    }
};

// ========================================
// State
// ========================================

const state = {
    lang: localStorage.getItem('ui_lang') || 'en',
    apiKey: localStorage.getItem('gemini_api_key') || '',
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
    langToggle: $('#langToggle'),
    toast: $('#toast'),
    apiWarning: $('#apiWarning'),
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
        el.textContent = t(key);
    });
    
    // Update language toggle
    $$('.lang-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.lang === state.lang);
    });
    
    // Update API warning visibility
    updateApiWarning();
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
    const prompt = `You are a translator for English and Khmer (Cambodian).
Task:
1. Listen to the audio and transcribe what is spoken.
2. Detect if the language is English ('en') or Khmer ('km').
3. Translate it to the other language (EN→KM or KM→EN).

Return ONLY a JSON object with no markdown:
{"lang":"en","text":"transcribed text","translation":"translated text"}`;

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
    
    // Language toggle
    elements.langToggle.addEventListener('click', (e) => {
        if (e.target.classList.contains('lang-btn')) {
            state.lang = e.target.dataset.lang;
            localStorage.setItem('ui_lang', state.lang);
            updateUI();
        }
    });
    
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

function init() {
    updateUI();
    initEventListeners();
    initScrollArrows();
}

// Start app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
