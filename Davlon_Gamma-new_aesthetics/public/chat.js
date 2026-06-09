// Chat Interface Logic for Sessions Page

const chatContainer = document.getElementById('chat-container');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('chat-send-btn');
const sessionTitleEl = document.getElementById('session-title');

// Session Management
let currentSessionId = null;
let currentSession = null;

// Initialize session from URL
function initSession() {
    const params = new URLSearchParams(window.location.search);
    currentSessionId = params.get('session');
    const initialPrompt = params.get('initial');

    if (!currentSessionId) {
        // No session specified, redirect to sessions list
        window.location.href = 'sessions.html';
        return;
    }

    // Load session from localStorage
    const sessions = JSON.parse(localStorage.getItem('chatSessions') || '[]');
    currentSession = sessions.find(s => s.id === currentSessionId);

    if (!currentSession) {
        // Session not found, redirect
        window.location.href = 'sessions.html';
        return;
    }

    // Set title
    if (sessionTitleEl) {
        sessionTitleEl.textContent = currentSession.title;
    }

    // Load existing messages
    if (currentSession.messages && currentSession.messages.length > 0) {
        currentSession.messages.forEach(msg => {
            addMessageToDOM(msg.text, msg.sender, false, msg.legacyWarning);
        });
    } else {
        // Add welcome message for new sessions
        addMessageToDOM("Hello! I've read your documents. Ask me anything about them.", 'ai', false);
    }

    // Handle initial prompt from new session
    if (initialPrompt && chatInput) {
        // Remove the initial param from URL to prevent re-sending on refresh
        window.history.replaceState({}, '', `chat.html?session=${currentSessionId}`);

        // Send the initial message
        chatInput.value = initialPrompt;
        setTimeout(() => sendMessage(), 100);
    }
}

function saveMessageToSession(text, sender, legacyWarning = null) {
    if (!currentSession) return;

    if (!currentSession.messages) {
        currentSession.messages = [];
    }

    currentSession.messages.push({
        text: text,
        sender: sender,
        timestamp: new Date().toISOString(),
        legacyWarning: legacyWarning
    });

    currentSession.updatedAt = new Date().toISOString();

    // Save back to localStorage
    let sessions = JSON.parse(localStorage.getItem('chatSessions') || '[]');
    const idx = sessions.findIndex(s => s.id === currentSessionId);
    if (idx !== -1) {
        sessions[idx] = currentSession;
        localStorage.setItem('chatSessions', JSON.stringify(sessions));
    }
}

// Initialize on load
if (chatContainer) {
    initSession();
}

if (sendBtn && chatInput) {
    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-resize logic (exact match to widget generator)
    chatInput.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
}

async function sendMessage() {
    if (!chatInput) return;

    const text = chatInput.value.trim();
    if (!text) return;

    // Reset height
    chatInput.style.height = 'auto';

    // 1. Add User Message
    addMessage(text, 'user');
    saveMessageToSession(text, 'user');
    chatInput.value = '';

    // 2. Add "Thinking..." Placeholder
    const thinkingId = addMessage("Thinking...", 'ai', true);

    try {
        // 3. Call Backend RAG API (with timeout)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout

        const response = await fetch('/api/query/rag', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: text, UseAllDocs: true }),
            signal: controller.signal
        });
        clearTimeout(timeoutId);

        if (response.ok) {
            const result = await response.json();

            // 5. Update AI Message with Markdown & Truth Dots
            updateMessage(thinkingId, result.answer, result.legacy_warning);
            saveMessageToSession(result.answer, 'ai', result.legacy_warning);
        } else {
            const errorMsg = "Sorry, I encountered an error connecting to my brain.";
            updateMessage(thinkingId, errorMsg);
            saveMessageToSession(errorMsg, 'ai');
        }
    } catch (e) {
        console.error(e);
        let errorMsg;
        if (e.name === 'AbortError') {
            errorMsg = "The request timed out. The AI is taking too long to respond. Please try a simpler question or check if the backend is running.";
        } else {
            errorMsg = "Network Error: Could not reach the AI.";
        }
        updateMessage(thinkingId, errorMsg);
        saveMessageToSession(errorMsg, 'ai');
    }
}

// Add message to DOM (for new messages)
function addMessage(text, sender, isThinking = false) {
    return addMessageToDOM(text, sender, isThinking);
}

// Add message to DOM (also used for loading history)
function addMessageToDOM(text, sender, isThinking = false, legacyWarning = null) {
    const msgId = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 5);
    const div = document.createElement('div');
    div.className = `message ${sender} ${isThinking ? 'thinking' : ''}`;
    div.id = msgId;

    // Avatar
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerText = sender === 'user' ? 'Me' : 'AI';

    // Bubble
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';

    // For AI messages from history, render with markdown
    if (sender === 'ai' && !isThinking) {
        let html = parseResponse(text);
        if (legacyWarning) {
            html += renderLegacyWarning(legacyWarning);
        }
        bubble.innerHTML = html;
    } else {
        bubble.innerText = text;
    }

    div.appendChild(avatar);
    div.appendChild(bubble);
    chatContainer.appendChild(div);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    return msgId;
}



function updateMessage(msgId, newText, legacyWarning = null) {
    const msg = document.getElementById(msgId);
    if (msg) {
        msg.classList.remove('thinking');
        const bubble = msg.querySelector('.message-bubble');

        // Render main content
        let html = parseResponse(newText);

        // Add legacy warning footer if present
        if (legacyWarning) {
            html += renderLegacyWarning(legacyWarning);
        }

        bubble.innerHTML = html;

        // Auto-scroll
        const chatBox = document.getElementById('chat-history');
        if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;
    }
}

// Render legacy source warning footer (expandable)
function renderLegacyWarning(warning) {
    if (!warning || !warning.count || !warning.details) return '';  // Added: details check

    const warningId = 'legacy-warn-' + Date.now();

    // Build details HTML
    let detailsHtml = '<div class="legacy-details">';
    for (const source of warning.details) {
        let reasonText = '';
        switch (source.reason) {
            case 'superseded':
                reasonText = source.superseded_by
                    ? `Replaced by newer version`
                    : 'Superseded by newer document';
                break;
            case 'age_decay':
                reasonText = 'Low recent activity';
                break;
            case 'low_permanence':
                reasonText = 'Temporary/draft document';
                break;
            default:
                reasonText = 'Deprioritized';
        }
        detailsHtml += `
            <div class="legacy-source-item">
                <span class="legacy-source-name">📄 ${source.source}</span>
                <span class="legacy-source-reason">${reasonText}</span>
            </div>
        `;
    }
    detailsHtml += '</div>';

    return `
        <div class="legacy-warning-footer" id="${warningId}">
            <div class="legacy-warning-collapsed" onclick="toggleLegacyWarning('${warningId}')">
                <span class="legacy-warning-icon">⚠️</span>
                <span class="legacy-warning-text">${warning.count} source${warning.count > 1 ? 's' : ''} from legacy documents</span>
                <span class="legacy-warning-expand">▼ Details</span>
            </div>
            <div class="legacy-warning-expanded" style="display: none;">
                <div class="legacy-warning-header">
                    <strong>Legacy Sources</strong>
                    <span class="legacy-close" onclick="toggleLegacyWarning('${warningId}')">✕</span>
                </div>
                <p class="legacy-warning-info">These documents have reduced priority. Information may be outdated.</p>
                ${detailsHtml}
            </div>
        </div>
    `;
}

function toggleLegacyWarning(warningId) {
    const container = document.getElementById(warningId);
    if (!container) return;

    const collapsed = container.querySelector('.legacy-warning-collapsed');
    const expanded = container.querySelector('.legacy-warning-expanded');

    if (expanded.style.display === 'none') {
        collapsed.style.display = 'none';
        expanded.style.display = 'block';
    } else {
        collapsed.style.display = 'flex';
        expanded.style.display = 'none';
    }
}

// Custom Markdown Engine (Forgiving & Robust)
// Replaces marked.js dependency to handle "AI-flavored" formatting
function parseResponse(text) {
    if (!text) return "";

    const lines = text.split('\n');
    let html = '<div class="chat-md">'; // Scoped wrapper
    let inList = false;
    let listType = null; // 'ul' or 'ol'

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i].trimEnd(); // Keep leading spaces for potential nesting (future), but trim end

        // 1. Detect Standard Headers (# Title)
        const headerMatch = line.match(/^(#{1,6})\s+(.*)/);
        if (headerMatch) {
            if (inList) { html += isUl(listType) ? '</ul>' : '</ol>'; inList = false; }
            const level = headerMatch[1].length;
            // Map h1-h6 -> h1-h3 for chat sizing
            const tag = level <= 2 ? 'h1' : (level === 3 ? 'h2' : 'h3');
            html += `<${tag}>${formatInline(headerMatch[2])}</${tag}>`;
            continue;
        }

        // 2. Detect "Bold Headers" (**Title** or **# Title**)
        const boldHeaderMatch = line.match(/^(\*\*#?)\s*([^*]+)\*\*$/);
        if (boldHeaderMatch) {
            if (inList) { html += isUl(listType) ? '</ul>' : '</ol>'; inList = false; }
            html += `<h3>${formatInline(boldHeaderMatch[2])}</h3>`;
            continue;
        }

        // 3. Detect Lists
        // Unordered (*, -)
        const ulMatch = line.match(/^[\*\-]\s+(.*)/);
        if (ulMatch) {
            if (!inList || listType !== 'ul') {
                if (inList) { html += isUl(listType) ? '</ul>' : '</ol>'; }
                html += '<ul>';
                inList = true;
                listType = 'ul';
            }
            html += `<li>${formatInline(ulMatch[1])}</li>`;
            continue;
        }

        // Ordered (1.)
        const olMatch = line.match(/^\d+\.\s+(.*)/);
        if (olMatch) {
            if (!inList || listType !== 'ol') {
                if (inList) { html += isUl(listType) ? '</ul>' : '</ol>'; }
                html += '<ol>';
                inList = true;
                listType = 'ol';
            }
            html += `<li>${formatInline(olMatch[1])}</li>`;
            continue;
        }

        // 4. Regular Paragraphs / Text
        // If we are in a list and see a non-list line:
        // "Generic" parser behavior: Close list for any non-indented text.
        // Robust behavior: If it's empty, ignore. If text, close list.

        if (line.trim() === '') {
            // Optional: Treats double newline as block break, but keeping list open for single newline spacing is risky
            // Strategy: Close list on empty line? No, AI often puts newlines between items.
            // Strategy: Keep open.
            continue;
        }

        // If we got here, it's text.
        if (inList) {
            html += isUl(listType) ? '</ul>' : '</ol>';
            inList = false;
        }

        // Render as paragraph or plain text with breaks
        html += `<p>${formatInline(line)}</p>`;
    }

    if (inList) { html += isUl(listType) ? '</ul>' : '</ol>'; }
    html += '</div>';

    return html;
}

function isUl(type) { return type === 'ul'; }

// Handles Bold, Italic, Code, and Citations
function formatInline(text) {
    let output = text;

    // 1. Code (`...`)
    output = output.replace(/`([^`]+)`/g, '<code>$1</code>');

    // 2. Bold (**...**)
    output = output.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // 3. Italic (*...*)
    output = output.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // 4. Truth Dots: [[Source: ...]]
    // Regex matches [[Source: filename (Page X)]] or just [[Source: filename]]
    output = output.replace(/\[\[Source:\s*(.*?)\]\]/g, (match, sourceInfo) => {
        return `<span class="citation-dot" title="Verified Source: ${sourceInfo}" onclick="event.stopPropagation(); openDocPreview('${sourceInfo}')"></span>`;
    });

    return output;
}

// Document Preview Logic
function openDocPreview(sourceInfo) {
    const modal = document.getElementById('doc-preview-modal');
    const title = document.getElementById('doc-preview-title');
    const content = document.getElementById('doc-preview-content');

    if (modal && title && content) {
        title.innerText = "Source: " + sourceInfo;
        content.innerText = `Preparing preview for ${sourceInfo}...\n\n(Simulated Preview)\nThis would display the actual content chunks from the document relevant to the citation.\n\n[End of Preview]`;
        modal.classList.add('active');
    }
}

function closeDocPreview() {
    const modal = document.getElementById('doc-preview-modal');
    if (modal) modal.classList.remove('active');
}

// Keeping fallback just in case, but unused by default now
function addCitations(msgId, citations) {
    // Legacy
}
