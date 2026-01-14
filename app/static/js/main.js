// ============================================================
// ELEMENTS
// ============================================================

const elements = {
    // Tabs
    tabs: document.querySelectorAll('.tab'),
    tabContents: document.querySelectorAll('.tab-content'),
    
    // Form
    form: document.getElementById('emailForm'),
    emailText: document.getElementById('emailText'),
    emailFile: document.getElementById('emailFile'),
    fileLabel: document.getElementById('fileLabel'),
    filePreview: document.getElementById('filePreview'),
    charCount: document.getElementById('charCount'),
    submitBtn: document.getElementById('submitBtn'),
    
    // Cards
    uploadCard: document.getElementById('uploadCard'),
    resultCard: document.getElementById('resultCard'),
    
    // Result elements
    categoryValue: document.getElementById('categoryValue'),
    resultCategory: document.getElementById('resultCategory'),
    resultResponse: document.getElementById('resultResponse'),
    resultJustification: document.getElementById('resultJustification'),
    resultPreview: document.getElementById('resultPreview'),
    previewSection: document.getElementById('previewSection'),
    
    // Buttons
    closeResult: document.getElementById('closeResult'),
    newClassification: document.getElementById('newClassification'),
    copyResponse: document.getElementById('copyResponse'),
    
    // Toast
    toast: document.getElementById('toast')
};

// ============================================================
// TAB SWITCHING
// ============================================================

elements.tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        const targetTab = tab.dataset.tab;
        
        // Update active tab
        elements.tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        // Update active content
        elements.tabContents.forEach(content => {
            if (content.id === `${targetTab}Content`) {
                content.classList.add('active');
            } else {
                content.classList.remove('active');
            }
        });
        
        // Clear opposite input
        if (targetTab === 'text') {
            elements.emailFile.value = '';
            hideFilePreview();
        } else {
            elements.emailText.value = '';
            updateCharCount();
        }
    });
});

// ============================================================
// CHARACTER COUNTER
// ============================================================

function updateCharCount() {
    const count = elements.emailText.value.length;
    elements.charCount.textContent = count.toLocaleString('pt-BR');
}

elements.emailText.addEventListener('input', updateCharCount);

// ============================================================
// FILE UPLOAD
// ============================================================

let selectedFile = null;

elements.emailFile.addEventListener('change', handleFileSelect);

function handleFileSelect(e) {
    const file = e.target.files[0];
    
    if (!file) {
        hideFilePreview();
        return;
    }
    
    // Validate file type
    const validTypes = ['.txt', '.pdf'];
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!validTypes.includes(fileExt)) {
        showToast('Apenas arquivos .txt e .pdf são permitidos', 'error');
        elements.emailFile.value = '';
        hideFilePreview();
        return;
    }
    
    // Validate file size (10MB)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        showToast('Arquivo muito grande. Máximo: 10MB', 'error');
        elements.emailFile.value = '';
        hideFilePreview();
        return;
    }
    
    selectedFile = file;
    showFilePreview(file);
}

function showFilePreview(file) {
    const sizeInMB = (file.size / (1024 * 1024)).toFixed(2);
    const fileType = file.name.split('.').pop().toUpperCase();
    
    elements.filePreview.innerHTML = `
        <div class="file-preview-info">
            <svg class="file-preview-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" stroke-width="2"/>
                <path d="M13 2v7h7" stroke-width="2"/>
            </svg>
            <div class="file-preview-text">
                <div class="file-preview-name">${file.name}</div>
                <div class="file-preview-size">${fileType} • ${sizeInMB} MB</div>
            </div>
            <button type="button" class="file-preview-remove" onclick="removeFile()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="20" height="20">
                    <path d="M18 6L6 18M6 6l12 12" stroke-width="2" stroke-linecap="round"/>
                </svg>
            </button>
        </div>
    `;
    
    elements.filePreview.classList.add('active');
}

function hideFilePreview() {
    elements.filePreview.classList.remove('active');
    elements.filePreview.innerHTML = '';
    selectedFile = null;
}

function removeFile() {
    elements.emailFile.value = '';
    hideFilePreview();
}

// Drag & Drop
elements.fileLabel.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.fileLabel.classList.add('drag-over');
});

elements.fileLabel.addEventListener('dragleave', () => {
    elements.fileLabel.classList.remove('drag-over');
});

elements.fileLabel.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.fileLabel.classList.remove('drag-over');
    
    const file = e.dataTransfer.files[0];
    if (file) {
        elements.emailFile.files = e.dataTransfer.files;
        handleFileSelect({ target: elements.emailFile });
    }
});

// ============================================================
// FORM SUBMISSION
// ============================================================

elements.form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Determine which tab is active
    const activeTab = document.querySelector('.tab.active').dataset.tab;
    
    // Validate input
    if (activeTab === 'text') {
        const text = elements.emailText.value.trim();
        if (!text) {
            showToast('Por favor, insira o conteúdo do email', 'error');
            return;
        }
        await classifyEmail({ text });
    } else {
        if (!selectedFile) {
            showToast('Por favor, selecione um arquivo', 'error');
            return;
        }
        await classifyEmail({ file: selectedFile });
    }
});

async function classifyEmail(data) {
    // Show loading state
    setLoadingState(true);
    
    try {
        const formData = new FormData();
        
        if (data.text) {
            formData.append('text', data.text);
        } else if (data.file) {
            formData.append('file', data.file);
        }
        
        const response = await fetch('/api/process', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Erro ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // Show result
        displayResult(result);
        showToast('Classificação realizada com sucesso!', 'success');
        
    } catch (error) {
        console.error('Error:', error);
        showToast('Erro ao processar o email. Tente novamente.', 'error');
    } finally {
        setLoadingState(false);
    }
}

function setLoadingState(loading) {
    if (loading) {
        elements.submitBtn.disabled = true;
        elements.submitBtn.classList.add('loading');
    } else {
        elements.submitBtn.disabled = false;
        elements.submitBtn.classList.remove('loading');
    }
}

// ============================================================
// DISPLAY RESULT
// ============================================================

function displayResult(data) {
    const { categoria, resposta, justificativa_curta, preview } = data;
    
    // Update category
    elements.categoryValue.textContent = categoria;
    
    // Update category badge style
    const categoryBadge = elements.resultCategory.querySelector('.category-badge');
    categoryBadge.className = `category-badge ${categoria.toLowerCase()}`;
    
    // Update response
    elements.resultResponse.textContent = resposta;
    
    // Update justification
    elements.resultJustification.textContent = justificativa_curta;
    
    // Update preview (if available)
    if (preview) {
        elements.resultPreview.textContent = preview;
        elements.previewSection.style.display = 'block';
    } else {
        elements.previewSection.style.display = 'none';
    }
    
    // Show result card with animation
    elements.resultCard.style.display = 'block';
    
    // Scroll to result
    setTimeout(() => {
        elements.resultCard.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'nearest' 
        });
    }, 100);
}

// ============================================================
// RESULT ACTIONS
// ============================================================

elements.closeResult.addEventListener('click', () => {
    elements.resultCard.style.display = 'none';
});

elements.newClassification.addEventListener('click', () => {
    // Hide result
    elements.resultCard.style.display = 'none';
    
    // Reset form
    elements.form.reset();
    elements.emailFile.value = '';
    hideFilePreview();
    updateCharCount();
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

elements.copyResponse.addEventListener('click', async () => {
    const response = elements.resultResponse.textContent;
    
    try {
        await navigator.clipboard.writeText(response);
        showToast('Resposta copiada!', 'success');
        
        // Visual feedback
        elements.copyResponse.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M20 6L9 17l-5-5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Copiado!
        `;
        
        setTimeout(() => {
            elements.copyResponse.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2" stroke-width="2"/>
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" stroke-width="2"/>
                </svg>
                Copiar
            `;
        }, 2000);
        
    } catch (error) {
        showToast('Erro ao copiar', 'error');
    }
});

// ============================================================
// TOAST NOTIFICATION
// ============================================================

function showToast(message, type = 'success') {
    elements.toast.textContent = message;
    elements.toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        elements.toast.classList.remove('show');
    }, 3000);
}

// ============================================================
// KEYBOARD SHORTCUTS
// ============================================================

document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + Enter to submit
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        if (document.activeElement === elements.emailText) {
            elements.form.dispatchEvent(new Event('submit'));
        }
    }
    
    // Escape to close result
    if (e.key === 'Escape') {
        if (elements.resultCard.style.display === 'block') {
            elements.resultCard.style.display = 'none';
        }
    }
});

// ============================================================
// INITIALIZE
// ============================================================

console.log('✨ EmailAI Classifier iniciado com sucesso!');
console.log('💡 Atalhos:');
console.log('   - Ctrl/Cmd + Enter: Enviar formulário');
console.log('   - Escape: Fechar resultado');
