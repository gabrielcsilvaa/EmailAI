# 📧 EmailAI (Case AutoU.io)
> Solução de classificação automática de emails corporativos com IA para o case técnico AutoU

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-4285F4?style=flat&logo=google&logoColor=white)](https://ai.google.dev/)

---

## 🎯 Sobre o Projeto

Este projeto foi desenvolvido como solução para o **case técnico da AutoU**, simulando uma aplicação real para uma empresa do setor financeiro que recebe alto volume de emails diariamente.

### Objetivo

Automatizar a leitura, classificação e sugestão de respostas para emails corporativos, liberando tempo da equipe e aumentando a eficiência operacional.

### Categorias

- **Produtivo**: Emails que exigem ação/resposta (suporte, status, dúvidas, solicitações)
- **Improdutivo**: Emails sociais/cortesia sem necessidade de ação imediata (agradecimentos, felicitações)

---

## ✨ Funcionalidades

- 🤖 **Classificação inteligente** com Google Gemini 2.5 Flash
- 💬 **Sugestão automática de resposta** contextualizada
- 📄 **Suporte a múltiplos formatos**: texto direto, .txt e .pdf
- 🎨 **Interface moderna** com design futurístico e animações
- ⚡ **Processamento em tempo real** com feedback visual
- 🔒 **Seguro**: dados não são armazenados
- 📱 **Responsivo**: funciona em desktop e mobile

---

## 🛠️ Stack Tecnológica

### Backend
- **Python 3.12+**
- **Flask** - Framework web minimalista
- **google-generativeai** - Integração com Gemini AI
- **pypdf** - Leitura de arquivos PDF

### Frontend
- **HTML5 + CSS3** - Interface moderna com glassmorphism
- **JavaScript (Vanilla)** - Sem frameworks, puro e performático
- **Google Fonts (Inter)** - Tipografia clean

### IA & NLP
- **Google Gemini 2.5 Flash** - Classificação e geração de respostas
- **NLP básico** - Pré-processamento com remoção de stopwords

---

## 📁 Estrutura do Projeto

```
email-ai-classifier/
├── app/
│   ├── __init__.py              # Factory pattern (create_app)
│   ├── config.py                # Configurações da aplicação
│   ├── routes/
│   │   ├── __init__.py
│   │   └── api.py               # Endpoint /api/process
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_client.py         # Lógica de classificação + IA
│   │   └── file_readers.py      # Leitura de .txt e .pdf
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css       # Design moderno
│   │   └── js/
│   │       └── main.js          # Interações e API calls
│   ├── templates/
│   │   └── index.html           # Interface principal
│   └── utils/
│       ├── __init__.py
│       └── text_utils.py        # Utilitários de texto
├── samples/                      # Exemplos de teste
│   ├── produtivo_1.txt
│   ├── improdutivo_1.txt
│   └── exemplos.pdf
├── .env                          # Variáveis de ambiente (não versionado)
├── .env.example                  # Template das variáveis
├── requirements.txt              # Dependências Python
├── runtime.txt                   # Versão do Python (deploy)
├── run.py                        # Entry point local
└── README.md                     # Este arquivo
```

---

## 🚀 Como Rodar Localmente

### Pré-requisitos

- Python 3.12+
- Pip instalado
- Chave de API do Google Gemini ([obter aqui](https://ai.google.dev/))

### Passo a Passo

1. **Clone o repositório**
```bash
git clone https://github.com/seu-usuario/email-ai-classifier.git
cd email-ai-classifier
```

2. **Crie um ambiente virtual**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Instale as dependências**
```bash
pip install -r requirements.txt
```

4. **Configure as variáveis de ambiente**
```bash
# Copie o template
cp .env.example .env

# Edite o .env e adicione sua chave do Gemini
GEMINI_API_KEY=sua_chave_aqui
```

5. **Execute a aplicação**
```bash
python run.py
```

6. **Acesse no navegador**
```
http://localhost:5000
```

---

## 🔑 Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
FLASK_ENV=development
SECRET_KEY=sua_chave_secreta_aqui
GEMINI_API_KEY=sua_chave_gemini_aqui
GEMINI_MODEL=models/gemini-2.5-flash
LOG_LEVEL=INFO
```

---

## 📡 API Endpoint

### `POST /api/process`

Processa e classifica um email.

**Entrada (opção 1 - JSON):**
```json
{
  "text": "Preciso do status do caso 12345"
}
```

**Entrada (opção 2 - FormData):**
```javascript
const formData = new FormData();
formData.append('file', arquivo); // .txt ou .pdf
```

**Resposta:**
```json
{
  "categoria": "Produtivo",
  "resposta": "Claro! Vou verificar o status do caso 12345 e retorno em breve.",
  "justificativa_curta": "Solicitação de status de caso em aberto.",
  "preview": "Preciso do status do caso 12345" // opcional
}
```

**Códigos de Status:**
- `200` - Sucesso
- `400` - Requisição inválida (falta texto/arquivo)
- `500` - Erro interno do servidor

---

## 🧪 Exemplos de Teste

### Produtivo

**Exemplo 1: Solicitação de status**
```
Preciso do status do caso 12345
```
→ Resposta sugerida: "Claro! Vou verificar o status do caso 12345 e retorno em breve."

**Exemplo 2: Dúvida técnica**
```
Como faço para redefinir minha senha do sistema?
```
→ Resposta sugerida: "Para redefinir sua senha, acesse 'Esqueci minha senha' na tela de login..."

**Exemplo 3: Envio de documento**
```
Segue em anexo o relatório de vendas do Q4.
```
→ Resposta sugerida: "Recebi o relatório. Vou analisar e retorno com feedback."

### Improdutivo

**Exemplo 1: Felicitação**
```
Feliz Natal para toda a equipe!
```
→ Resposta sugerida: "Obrigado! Feliz Natal pra você também! 🎄✨"

**Exemplo 2: Agradecimento**
```
Muito obrigado pela ajuda de ontem!
```
→ Resposta sugerida: "Imagina! Se precisar de algo mais, estou à disposição 😊"

---

## 🎨 Design e UX

### Conceito Visual
- **Tema**: Futurístico + Minimalista + Interativo
- **Paleta**: Gradientes vibrantes (roxo/azul/rosa) sobre fundo escuro
- **Efeitos**: Glassmorphism, animações suaves, micro-interações
- **Tipografia**: Inter (Google Fonts) - clean e moderna

### Destaques
- Background animado com esferas gradientes flutuantes
- Cards com efeito vidro fosco (backdrop-blur)
- Animações de entrada suaves (fadeIn, slideIn)
- Feedback visual em todas as interações
- Toast notifications para mensagens do sistema

---

## 🧠 Como Funciona

### Fluxo de Classificação

1. **Entrada do Usuário**
   - Texto direto ou upload de arquivo (.txt/.pdf)

2. **Pré-processamento NLP**
   - Normalização (lowercase, remoção de espaços extras)
   - Remoção de pontuação excessiva
   - Remoção de stopwords em português

3. **Regras Determinísticas** (prioridade)
   - Mensagens sociais curtas detectadas por keywords
   - Reduz custo de API e aumenta previsibilidade

4. **Classificação por IA** (Gemini 2.5 Flash)
   - Prompt estruturado com exemplos (few-shot learning)
   - Temperatura baixa (0.3) para consistência
   - Sempre retorna JSON válido

5. **Resposta Sugerida**
   - Contextualizada à categoria
   - Tom profissional mas amigável
   - Curta e objetiva (1-2 frases)

6. **Fallbacks Robustos**
   - Quota excedida → mensagem amigável
   - JSON inválido → tentativa de correção automática
   - Erro de API → fallback operacional

---

## 🔒 Segurança e Privacidade

- ✅ Dados **não são armazenados** em banco de dados
- ✅ Processamento **em memória** apenas durante a requisição
- ✅ API key do Gemini protegida em variável de ambiente
- ✅ Validação de tipos de arquivo (.txt e .pdf apenas)
- ✅ Limite de tamanho de arquivo (10MB)

---

## 🌐 Deploy

### Opções de Hospedagem

O projeto está configurado para deploy em:

1. **Vercel** (recomendado)
   - Suporte nativo a Python + Flask
   - Deploy automático via Git

2. **Render**
   - Tier gratuito generoso
   - Fácil configuração

3. **Heroku**
   - Clássico e confiável
   - Requer `Procfile`

4. **AWS/GCP/Azure**
   - Para produção em larga escala

### Arquivos Necessários

- `runtime.txt` - Especifica versão do Python
- `requirements.txt` - Dependências
- `.env` - Variáveis de ambiente (configurar no painel)

---

## 🎥 Vídeo Demonstrativo

[Link do vídeo no YouTube](https://youtube.com/seu-video)

**Conteúdo (3-5 minutos):**
- ✅ Introdução e contexto do case
- ✅ Demonstração da interface web
- ✅ Upload de arquivo + classificação
- ✅ Exemplos produtivo e improdutivo
- ✅ Explicação técnica (IA, prompt engineering, fallbacks)
- ✅ Resumo e aprendizados

---

## 📊 Decisões Técnicas

### Por que Gemini 2.5 Flash?
- ✅ Rápido (latência baixa)
- ✅ Gratuito até 15 RPM
- ✅ Suporte nativo a JSON
- ✅ Multilíngue (pt-BR)

### Por que Flask?
- ✅ Minimalista e leve
- ✅ Fácil de fazer deploy
- ✅ Ótimo para APIs RESTful

### Por que Vanilla JS?
- ✅ Zero dependências no frontend
- ✅ Mais leve e rápido
- ✅ Fácil de manter

### Por que NLP básico?
- ✅ Demonstra conhecimento de pré-processamento
- ✅ Reduz ruído para a IA
- ✅ Não requer bibliotecas pesadas (NLTK, spaCy)

---

## 🐛 Troubleshooting

### Erro: "API key inválida"
- Verifique se `GEMINI_API_KEY` está configurada no `.env`
- Confirme que a chave está ativa no [Google AI Studio](https://ai.google.dev/)

### Erro: "Quota excedida"
- Gemini Free tem limite de 15 requisições/minuto
- Aguarde alguns minutos antes de tentar novamente

### Erro ao ler PDF
- Confirme que o PDF não está corrompido
- PDFs com imagens/scan podem não funcionar (requer OCR)

### Interface não carrega estilos
- Verifique se os arquivos estão em `app/static/css/styles.css`
- Confirme que `url_for()` está funcionando corretamente

---

## 📚 Aprendizados

### O que foi implementado:
✅ Classificação robusta com regras + IA  
✅ Prompt engineering eficaz (few-shot)  
✅ Tratamento completo de erros  
✅ Interface moderna e intuitiva  
✅ Código limpo e organizado  
✅ Deploy-ready  

### Próximas melhorias (se fosse produção):
- [ ] Cache de respostas (Redis)
- [ ] Rate limiting por IP
- [ ] Histórico de classificações (banco de dados)
- [ ] Analytics e métricas
- [ ] Testes automatizados (pytest)
- [ ] CI/CD com GitHub Actions

---

## 👤 Autor

**[Seu Nome]**
- GitHub: [@seu-usuario](https://github.com/seu-usuario)
- LinkedIn: [/in/seu-perfil](https://linkedin.com/in/seu-perfil)
- Email: seu@email.com

---

## 📄 Licença

Este projeto foi desenvolvido exclusivamente para o case técnico da **AutoU**.

---

## 🙏 Agradecimentos

- **AutoU** pela oportunidade de demonstrar habilidades técnicas
- **Google** pelo Gemini API gratuito
- **Comunidade Python** pelas bibliotecas incríveis

---

<div align="center">

**Desenvolvido com ❤️ para o case AutoU**

⭐ Se gostou do projeto, deixe uma estrela!

</div>
