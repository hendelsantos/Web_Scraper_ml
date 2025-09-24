// Configuração da API
const API_BASE_URL = window.location.origin;

// Estado da aplicação
let currentJobId = null;
let statusCheckInterval = null;

// Elementos DOM
const elements = {
    form: document.getElementById('scraperForm'),
    siteSelect: document.getElementById('site'),
    searchInput: document.getElementById('search_term'),
    submitBtn: document.getElementById('submitBtn'),
    statusContainer: document.getElementById('statusContainer'),
    resultsContainer: document.getElementById('resultsContainer'),
    jobId: document.getElementById('jobId'),
    statusIcon: document.getElementById('statusIcon'),
    statusText: document.getElementById('statusText'),
    progressFill: document.getElementById('progressFill'),
    statusDetails: document.getElementById('statusDetails'),
    resultsSummary: document.getElementById('resultsSummary'),
    resultsBody: document.getElementById('resultsBody'),
    downloadBtn: document.getElementById('downloadBtn'),
    newSearchBtn: document.getElementById('newSearchBtn')
};

// Inicialização
document.addEventListener('DOMContentLoaded', async () => {
    await loadSites();
    setupEventListeners();
});

// Carregar sites disponíveis
async function loadSites() {
    try {
        const response = await fetch(`${API_BASE_URL}/sites`);
        const data = await response.json();
        
        elements.siteSelect.innerHTML = '<option value="">Selecione um site...</option>';
        
        if (data.sites_disponiveis) {
            Object.entries(data.sites_disponiveis).forEach(([key, name]) => {
                const option = document.createElement('option');
                option.value = key;
                option.textContent = name;
                elements.siteSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Erro ao carregar sites:', error);
        elements.siteSelect.innerHTML = '<option value="">Erro ao carregar sites</option>';
    }
}

// Configurar event listeners
function setupEventListeners() {
    elements.form.addEventListener('submit', handleFormSubmit);
    elements.downloadBtn.addEventListener('click', handleDownload);
    elements.newSearchBtn.addEventListener('click', handleNewSearch);
}

// Submissão do formulário
async function handleFormSubmit(event) {
    event.preventDefault();
    
    const site = elements.siteSelect.value;
    const searchTerm = elements.searchInput.value.trim();
    
    if (!site || !searchTerm) {
        alert('Por favor, preencha todos os campos!');
        return;
    }
    
    await startScraping(site, searchTerm);
}

// Iniciar scraping
async function startScraping(site, searchTerm) {
    try {
        // Atualizar UI
        elements.submitBtn.disabled = true;
        elements.submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Iniciando...';
        
        // Fazer requisição para API
        const response = await fetch(`${API_BASE_URL}/scraping`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                site: site,
                termo_busca: searchTerm
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.job_id) {
            currentJobId = data.job_id;
            showStatus(data.job_id);
            startStatusMonitoring();
        } else {
            const errorMessage = data.detail || data.message || 'Erro ao iniciar scraping';
            throw new Error(errorMessage);
        }
        
    } catch (error) {
        console.error('Erro completo:', error);
        
        let errorMessage = 'Erro desconhecido';
        if (error.message) {
            errorMessage = error.message;
        } else if (typeof error === 'string') {
            errorMessage = error;
        } else if (error.toString) {
            errorMessage = error.toString();
        }
        
        alert(`Erro: ${errorMessage}`);
        resetForm();
    }
}

// Mostrar área de status
function showStatus(jobId) {
    elements.jobId.textContent = jobId;
    elements.statusContainer.style.display = 'block';
    elements.resultsContainer.style.display = 'none';
    
    // Scroll para o status
    elements.statusContainer.scrollIntoView({ behavior: 'smooth' });
}

// Monitoramento de status
function startStatusMonitoring() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }
    
    statusCheckInterval = setInterval(checkJobStatus, 2000);
    checkJobStatus(); // Primeira verificação imediata
}

// Verificar status do job
async function checkJobStatus() {
    if (!currentJobId) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/job/${currentJobId}`);
        const data = await response.json();
        
        updateStatusDisplay(data);
        
        // Se completou ou erro, parar monitoramento
        if (data.status === 'completed' || data.status === 'error') {
            clearInterval(statusCheckInterval);
            statusCheckInterval = null;
            
            if (data.status === 'completed') {
                showResults(data);
            } else {
                showError(data);
            }
        }
        
    } catch (error) {
        console.error('Erro ao verificar status:', error);
        // Se há muitos erros consecutivos, parar o monitoramento
        if (statusCheckInterval) {
            clearInterval(statusCheckInterval);
            statusCheckInterval = null;
            showError({ message: 'Erro de conexão com a API' });
        }
    }
}

// Atualizar display de status
function updateStatusDisplay(data) {
    const { status, message, progress } = data;
    
    // Atualizar ícone
    elements.statusIcon.className = 'status-icon';
    elements.statusIcon.innerHTML = '';
    
    switch (status) {
        case 'running':
            elements.statusIcon.classList.add('running');
            elements.statusIcon.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            elements.statusText.textContent = 'Coletando dados...';
            break;
        case 'completed':
            elements.statusIcon.classList.add('completed');
            elements.statusIcon.innerHTML = '<i class="fas fa-check"></i>';
            elements.statusText.textContent = 'Concluído!';
            break;
        case 'error':
            elements.statusIcon.classList.add('error');
            elements.statusIcon.innerHTML = '<i class="fas fa-times"></i>';
            elements.statusText.textContent = 'Erro!';
            break;
        default:
            elements.statusIcon.innerHTML = '<i class="fas fa-clock"></i>';
            elements.statusText.textContent = 'Aguardando...';
    }
    
    // Atualizar progresso
    const progressPercent = progress || 0;
    elements.progressFill.style.width = `${progressPercent}%`;
    
    // Atualizar detalhes
    elements.statusDetails.textContent = message || 'Processando...';
}

// Mostrar resultados
function showResults(data) {
    const results = data; // A API retorna os dados diretamente, não em data.result
    
    if (!results || !results.produtos || results.produtos.length === 0) {
        showError({ message: 'Nenhum resultado encontrado' });
        return;
    }
    
    // Mostrar container de resultados
    elements.resultsContainer.style.display = 'block';
    elements.resultsContainer.scrollIntoView({ behavior: 'smooth' });
    
    // Resumo
    const count = results.produtos.length;
    const searchTerm = elements.searchInput.value; // Usar o valor do input
    const siteName = elements.siteSelect.options[elements.siteSelect.selectedIndex].text;
    
    elements.resultsSummary.innerHTML = `
        <strong>${count} produtos</strong> encontrados para 
        "<strong>${searchTerm}</strong>" em ${siteName}
    `;
    
    // Tabela de resultados
    elements.resultsBody.innerHTML = '';
    
    results.produtos.forEach(produto => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="product-name">${escapeHtml(produto.nome || 'N/A')}</td>
            <td class="product-price">${escapeHtml(produto.preco || 'N/A')}</td>
            <td>
                <a href="${produto.link || '#'}" 
                   target="_blank" 
                   class="product-link" 
                   rel="noopener noreferrer">
                    Ver Produto
                </a>
            </td>
            <td class="product-rating">
                ${produto.avaliacao ? `
                    <span class="rating-stars">⭐</span>
                    ${escapeHtml(produto.avaliacao)}
                ` : 'N/A'}
            </td>
            <td>${escapeHtml(produto.vendas || 'N/A')}</td>
        `;
        elements.resultsBody.appendChild(row);
    });
    
    resetForm();
}

// Mostrar erro
function showError(data) {
    elements.statusDetails.innerHTML = `
        <div style="color: #e53e3e; font-weight: 600;">
            ❌ ${data.message || 'Erro desconhecido'}
        </div>
    `;
    resetForm();
}

// Download dos resultados
async function handleDownload() {
    if (!currentJobId) return;
    
    try {
        elements.downloadBtn.disabled = true;
        elements.downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Baixando...';
        
        const response = await fetch(`${API_BASE_URL}/job/${currentJobId}/download`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `scraping_results_${currentJobId}.xlsx`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        } else {
            throw new Error('Erro ao baixar arquivo');
        }
        
    } catch (error) {
        console.error('Erro no download:', error);
        alert('Erro ao baixar arquivo');
    } finally {
        elements.downloadBtn.disabled = false;
        elements.downloadBtn.innerHTML = '<i class="fas fa-download"></i> Baixar Excel';
    }
}

// Nova busca
function handleNewSearch() {
    // Reset estado
    currentJobId = null;
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
        statusCheckInterval = null;
    }
    
    // Esconder containers
    elements.statusContainer.style.display = 'none';
    elements.resultsContainer.style.display = 'none';
    
    // Limpar campos
    elements.searchInput.value = '';
    elements.siteSelect.value = '';
    
    // Resetar botão
    resetForm();
    
    // Scroll para o topo
    elements.form.scrollIntoView({ behavior: 'smooth' });
}

// Reset do formulário
function resetForm() {
    elements.submitBtn.disabled = false;
    elements.submitBtn.innerHTML = '<i class="fas fa-rocket"></i> Iniciar Scraping';
}

// Escape HTML para segurança
function escapeHtml(text) {
    if (typeof text !== 'string') return text;
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Tratamento de erros globais
window.addEventListener('error', (event) => {
    console.error('Erro global:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('Promise rejeitada:', event.reason);
});

// Limpeza na saída
window.addEventListener('beforeunload', () => {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }
});
