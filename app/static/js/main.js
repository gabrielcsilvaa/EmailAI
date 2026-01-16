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
    toast: $('toast'),
    historyArea: $('historyArea')
};

let selectedFiles = [];

elements.emailFiles.addEventListener('change', (e) => {
    lerArquivos(Array.from(e.target.files));
});

function lerArquivos(files) {
    files.forEach(file => {
        const ext = file.name.split('.').pop().toLowerCase();
        if (!['txt', 'pdf'].includes(ext)) {
            mostrarToast(`Arquivo ${file.name} não é .txt ou .pdf`, 'error');
            return;
        }
        
        if (file.size > 10 * 1024 * 1024) {
            mostrarToast(`Arquivo ${file.name} é muito grande (máx. 10MB)`, 'error');
            return;
        }
        
        if (selectedFiles.some(f => f.name === file.name && f.size === file.size)) {
            mostrarToast(`Arquivo ${file.name} já foi adicionado`, 'error');
            return;
        }
        
        selectedFiles.push(file);
    });
    
    renderizarListaArquivos();
    elements.emailFiles.value = ''; 
}

function renderizarListaArquivos() {
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
                <button type="button" class="file-remove" onclick="removerArquivo(${index})">
                    <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M18 6L6 18M6 6l12 12" stroke-width="2"/>
                    </svg>
                </button>
            </div>
        `;
    }).join('');
}

function removerArquivo(index) {
    selectedFiles.splice(index, 1);
    renderizarListaArquivos();
}

window.removerArquivo = removerArquivo;



elements.form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const text = elements.emailText.value.trim();
    const hasFiles = selectedFiles.length > 0;
    
    // Validation
    if (!text && !hasFiles) {
        mostrarToast('Adicione texto ou arquivos para processar', 'error');
        return;
    }
    
    // Process
    await processarEmails({ text, files: selectedFiles });
});

async function processarEmails({ text, files }) {
    definirCarregando(true);
    
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
                const result = await processarEmail(req);
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
        
        exibirResultados(results);
        mostrarToast(`${results.length} email(s) processado(s)`, 'success');
        
        elements.emailText.value = '';
        selectedFiles = [];
        renderizarListaArquivos();
        
    } catch (error) {
        mostrarToast('Erro ao processar emails', 'error');
        console.error(error);
    } finally {
        definirCarregando(false);
    }
}

async function processarEmail(request) {
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

function exibirResultados(results) {
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
            return criarCardErro(result, index);
        }
        return criarCardResultado(result, index);
    }).join('');
    
    setTimeout(() => {
        elements.resultsArea.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);

    elements.historyArea.innerHTML += results.map((result) => {
        if (result.error) {
             return itensHistoricoErro(result);
        }

        return itensHistorico(result);
    }).join('');

    setTimeout(() => {
        elements.historyArea.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
}

function criarCardResultado(result, index) {
    const categoryClass = result.categoria?.toLowerCase() || 'produtivo';
    const categoryIcon = categoryClass === 'produtivo' 
        ? '<circle cx="12" cy="12" r="10" stroke-width="2"/><path d="M9 12l2 2 4-4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        : '<circle cx="12" cy="12" r="10" stroke-width="2"/><path d="M12 8v4M12 16h.01" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>';
    
    // Generate 3 response variations (informal, formal, professional)
    const responses = gerarVariacoesResposta(result.resposta || '');
    
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
                        ${verificarNoReply(result.justificativa_curta, responses, index)}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function criarOpcaoResposta(type, text, resultIndex) {
    const id = `response-${resultIndex}-${type}`;
    return `
        <div class="response-option">
            <div class="response-option-header">
                <div class="response-option-type">${type}</div>
                    <button class="btn-copy" data-target="${id}" onclick="copiarResposta(this.dataset.target)">
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

function criarCardErro(result, index) {
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

function gerarVariacoesResposta(baseResponse) {
    const informal = baseResponse
        .replace(/\bOlá\b/gi, 'Oi')
        .replace(/Como posso ajudar você\?/gi, 'Como posso te ajudar?')
        .replace(/\bvocê\b/gi, 'tu')
        .replace(/\bseu\b/gi, 'teu')
        .replace(/\bClaro!\b/gi, 'Claro!')
        + ' ';

    const formal = baseResponse
        .replace(/\bOi\b/gi, 'Olá')
        .replace(/\btu\b/gi, 'você')
        .replace(/\bteu\b/gi, 'seu')
        .replace(/😊|🎄|✨/g, '')
        + ' ';

    const professional = 'Prezado(a), ' + baseResponse
        .replace(/\bOi\b/gi, 'Bom dia')
        .replace(/\btu\b/gi, 'Vossa Senhoria')
        .replace(/\bteu\b/gi, 'seu')
        .replace(/😊|🎄|✨/g, '')
        .replace(/!/g, '.')
        + ' ';

    return { informal, formal, professional };
}


function verificarNoReply(justificationResponse, responses, index) {
    if (justificationResponse.indexOf("'no-reply'") === -1 || justificationResponse.indexOf('no-reply') === -1) {
        return ` 
        ${criarOpcaoResposta('informal', responses.informal, index)}
        ${criarOpcaoResposta('formal', responses.formal, index)}
        ${criarOpcaoResposta('profissional', responses.professional, index)}
        `
    } else {
         return `${criarOpcaoResposta('formal', responses.formal, index)}`
    }
}

async function copiarResposta(elementId) {
  const element = document.getElementById(elementId);

  if (!element) {
    mostrarToast("Elemento não encontrado", "error");
    return;
  }

  const text = element.innerText || element.textContent || "";

  if (!text.trim()) {
    mostrarToast("Nada para copiar", "error");
    return;
  }

  if (navigator.clipboard && navigator.clipboard.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      mostrarToast("Resposta copiada!", "success");
      return;
    } catch (err) {
      console.error("Clipboard API falhou:", err);
      // cai pro fallback
    }
  }

  try {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.top = "-9999px";
    document.body.appendChild(textarea);
    textarea.select();
    textarea.setSelectionRange(0, textarea.value.length);

    const ok = document.execCommand("copy");
    document.body.removeChild(textarea);

    if (ok) {
      mostrarToast("Resposta copiada!", "success");
    } else {
      mostrarToast("Não consegui copiar automaticamente", "error");
    }
  } catch (err) {
    console.error("Fallback copy falhou:", err);
    mostrarToast("Erro ao copiar", "error");
  }
}

window.copiarResposta = copiarResposta;

function definirCarregando(loading) {
    elements.submitBtn.disabled = loading;
    
    if (loading) {
        elements.btnText.style.display = 'none';
        elements.spinner.style.display = 'block';
    } else {
        elements.btnText.style.display = 'block';
        elements.spinner.style.display = 'none';
    }
}


function mostrarToast(message, type = 'success') {
    elements.toast.textContent = message;
    elements.toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        elements.toast.classList.remove('show');
    }, 3000);
}

function itensHistorico(result) {
    const categoryClass = result.categoria?.toLowerCase() || 'produtivo';
    const categoryIcon = categoryClass === 'produtivo' 
    ? '<circle cx="12" cy="12" r="10" stroke-width="2"/><path d="M9 12l2 2 4-4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
    : '<circle cx="12" cy="12" r="10" stroke-width="2"/><path d="M12 8v4M12 16h.01" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>';

    return `  
        <div class="response-options-history">
            <div class="response-option-history">
                <div class="response-option-header-history">
                    <span class="response-option-type-history">Resumo do e-mail</span>
                </div>

                <p class="response-option-text-history">
                    ${result.justificativa_curta}
                </p>

                <div class="result-category-history">
                    <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        ${categoryIcon}
                    </svg>
                    ${ result.categoria || "Produtivo"}
                </div>
            </div>
        </div>
    `;
}

function itensHistoricoErro(result) {
    return `  
        <div class="response-options-history">
            <div class="response-option-history">
                <div class="response-option-header-history">
                    <span class="response-option-type-history">Resumo do e-mail</span>
                </div>

                <p class="response-option-text-history">
                    Ocorreu um erro no envio
                </p>

                <div class="result-category-history">
                    ERRO
                </div>
            </div>
        </div>
    `;
}

// Modal do Histórico
const buttonHistory = document.getElementById("button-history");
const sideModal = document.getElementById("sideModal");
const backdrop = document.getElementById("backdrop");
const closeBtn = document.getElementById("closeModal");

function abrirModal() {
sideModal.classList.add("active");
backdrop.classList.add("active");
}

function fecharModal() {
sideModal.classList.remove("active");
backdrop.classList.remove("active");
}

buttonHistory.addEventListener("click", abrirModal);
closeBtn.addEventListener("click", fecharModal);
backdrop.addEventListener("click", fecharModal);

function itensHistoricoModal() {

}
