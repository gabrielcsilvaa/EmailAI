const $ = (id) => document.getElementById(id);
const $$ = (selector) => document.querySelectorAll(selector);

const elements = {
    form: $('emailForm'),
    emailText: $('emailText'),
    emailFiles: $('emailFiles'),
    filesList: $('filesList'),
    submitBtn: $('submitBtn'),
    btnText: $('btnText'),
    spinner: $('spinner'),
    resultsArea: $('resultsArea'),
    toast: $('toast')
};

let selectedFiles = [];

elements.emailFiles.addEventListener('change', (e) => {
    handleFiles(Array.from(e.target.files));
});

function handleFiles(files) {
    files.forEach(file => {
        const ext = file.name.split('.').pop().toLowerCase();
        if (!['txt', 'pdf'].includes(ext)) {
            showToast(`Arquivo ${file.name} não é .txt ou .pdf`, 'error');
            return;
        }
        
        if (file.size > 10 * 1024 * 1024) {
            showToast(`Arquivo ${file.name} é muito grande (máx. 10MB)`, 'error');
            return;
        }
        
        if (selectedFiles.some(f => f.name === file.name && f.size === file.size)) {
            showToast(`Arquivo ${file.name} já foi adicionado`, 'error');
            return;
        }
        
        selectedFiles.push(file);
    });
    
    renderFilesList();
    elements.emailFiles.value = ''; 
}

function renderFilesList() {
    if (selectedFiles.length === 0) {
        elements.filesList.innerHTML = '';
        return;
    }
    
    elements.filesList.innerHTML = selectedFiles.map((file, index) => {
        const sizeKB = (file.size / 1024).toFixed(1);
        const ext = file.name.split('.').pop().toUpperCase();
        
        return `
            <div class="file-item">
                <div class="file-info">
                    <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" stroke-width="2"/>
                        <path d="M13 2v7h7" stroke-width="2"/>
                    </svg>
                    <div>
                        <div class="file-name">${file.name}</div>
                        <div class="file-size">${ext} • ${sizeKB} KB</div>
                    </div>
                </div>
                <button type="button" class="file-remove" onclick="removeFile(${index})">
                    <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M18 6L6 18M6 6l12 12" stroke-width="2"/>
                    </svg>
                </button>
            </div>
        `;
    }).join('');
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    renderFilesList();
}

window.removeFile = removeFile;



elements.form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const text = elements.emailText.value.trim();
    const hasFiles = selectedFiles.length > 0;
    
    // Validation
    if (!text && !hasFiles) {
        showToast('Adicione texto ou arquivos para processar', 'error');
        return;
    }
    
    // Process
    await processEmails({ text, files: selectedFiles });
});

async function processEmails({ text, files }) {
    setLoading(true);
    
    try {
        const requests = [];
        
        // Add text request if provided
        if (text) {
            requests.push({ type: 'text', data: text });
        }
        
        // Add file requests
        files.forEach(file => {
            requests.push({ type: 'file', data: file });
        });
        
        // Process all requests
        const results = [];
        for (const req of requests) {
            try {
                const result = await processEmail(req);
                results.push(result);
            } catch (error) {
                console.error('Error processing:', error);
                results.push({
                    error: true,
                    message: error.message,
                    source: req.type === 'file' ? req.data.name : 'Texto direto'
                });
            }
        }
        
        displayResults(results);
        showToast(`${results.length} email(s) processado(s)`, 'success');
        
        elements.emailText.value = '';
        selectedFiles = [];
        renderFilesList();
        
    } catch (error) {
        showToast('Erro ao processar emails', 'error');
        console.error(error);
    } finally {
        setLoading(false);
    }
}

async function processEmail(request) {
    const formData = new FormData();
    
    if (request.type === 'text') {
        formData.append('text', request.data);
    } else {
        formData.append('file', request.data);
    }
    
    const response = await fetch('/api/process', {
        method: 'POST',
        body: formData
    });
    
    if (!response.ok) {
        throw new Error(`Erro ${response.status}`);
    }
    
    const data = await response.json();
    
    return {
        ...data,
        source: request.type === 'file' ? request.data.name : 'Texto direto'
    };
}

function displayResults(results) {
    if (results.length === 0) {
        elements.resultsArea.innerHTML = `
            <div class="empty-state">
                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <circle cx="12" cy="12" r="10" stroke-width="2"/>
                    <path d="M12 6v6l4 2" stroke-width="2" stroke-linecap="round"/>
                </svg>
                <p>Nenhum resultado ainda. Adicione emails acima.</p>
            </div>
        `;
        return;
    }
    
    elements.resultsArea.innerHTML = results.map((result, index) => {
        if (result.error) {
            return createErrorCard(result, index);
        }
        return createResultCard(result, index);
    }).join('');
    
    setTimeout(() => {
        elements.resultsArea.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
}

function createResultCard(result, index) {
    const categoryClass = result.categoria?.toLowerCase() || 'produtivo';
    const categoryIcon = categoryClass === 'produtivo' 
        ? '<circle cx="12" cy="12" r="10" stroke-width="2"/><path d="M9 12l2 2 4-4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        : '<circle cx="12" cy="12" r="10" stroke-width="2"/><path d="M12 8v4M12 16h.01" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>';
    
    const responseText = result.resposta || '';
    
    return `
        <div class="result-card" id="result-${index}">
            <div class="result-header">
                <div class="result-category ${categoryClass}">
                    <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        ${categoryIcon}
                    </svg>
                    ${result.categoria || 'Produtivo'}
                </div>
            </div>
            
            <div class="result-body">
                <!-- Remetente -->
                <div class="result-section">
                    <div class="result-label">
                        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            <circle cx="12" cy="7" r="4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        Remetente
                    </div>
                    <div class="result-content">${result.source || 'Texto direto'}</div>
                </div>
                
                <!-- Resumo -->
                <div class="result-section">
                    <div class="result-label">
                        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke-width="2"/>
                            <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" stroke-width="2"/>
                        </svg>
                        Resumo do E-mail
                    </div>
                    <div class="result-content secondary">${result.justificativa_curta || 'Classificação realizada.'}</div>
                </div>
                
                <!-- Sugestões de Resposta -->
                <div class="result-section">
                    <div class="result-label">
                        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" stroke-width="2"/>
                        </svg>
                        Sugestões de Resposta
                    </div>
                    <div class="response-options">
                        ${verificationNoReply(result.justificativa_curta, responseText, index)}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function createResponseOption(type, text, resultIndex) {
    const id = `response-${resultIndex}-${type}`;
    return `
        <div class="response-option">
            <div class="response-option-header">
                <div class="response-option-type">${type}</div>
                <button class="btn-copy" onclick="copyResponse('${id}')">
                    <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2" stroke-width="2"/>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" stroke-width="2"/>
                    </svg>
                    Copiar
                </button>
            </div>
            <div class="response-option-text" id="${id}">${text}</div>
        </div>
    `;
}

function createErrorCard(result, index) {
    return `
        <div class="result-card" id="result-${index}">
            <div class="result-header">
                <div class="result-category improdutivo">
                    <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <circle cx="12" cy="12" r="10" stroke-width="2"/>
                        <path d="M12 8v4M12 16h.01" stroke-width="2"/>
                    </svg>
                    Erro
                </div>
            </div>
            <div class="result-body">
                <div class="result-section">
                    <div class="result-label">Mensagem de Erro</div>
                    <div class="result-content secondary">${result.message}</div>
                </div>
                <div class="result-section">
                    <div class="result-label">Origem</div>
                    <div class="result-content">${result.source}</div>
                </div>
            </div>
        </div>
    `;
}

function verificationNoReply(justificationResponse, responseText, index) {
    if (justificationResponse.indexOf("'no-reply'") === -1) {
        return createResponseOption('formal', responseText, index);
    }
    return '';
}

async function copyResponse(elementId) {
    const element = $(elementId);
    const text = element.textContent;
    
    try {
        await navigator.clipboard.writeText(text);
        showToast('Resposta copiada!', 'success');
    } catch (error) {
        showToast('Erro ao copiar', 'error');
    }
}

window.copyResponse = copyResponse;


function setLoading(loading) {
    elements.submitBtn.disabled = loading;
    
    if (loading) {
        elements.btnText.style.display = 'none';
        elements.spinner.style.display = 'block';
    } else {
        elements.btnText.style.display = 'block';
        elements.spinner.style.display = 'none';
    }
}


function showToast(message, type = 'success') {
    elements.toast.textContent = message;
    elements.toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        elements.toast.classList.remove('show');
    }, 3000);
}

