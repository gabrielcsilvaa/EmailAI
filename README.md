# Email AI Classifier (Case AutoU)

Projeto de classificacao automatica de emails com sugestao de resposta, conforme o desafio da AutoU para uma empresa do setor financeiro que recebe alto volume de mensagens.

## Contexto do desafio

A empresa recebe emails produtivos (que exigem acao) e improdutivos (mensagens sociais, agradecimentos, spam). O objetivo e automatizar a leitura, classificar e sugerir uma resposta adequada, reduzindo o trabalho manual do time.

## Objetivo do projeto

- Classificar emails em Produtivo ou Improdutivo.
- Sugerir uma resposta curta e adequada para a categoria identificada.
- Entregar uma interface web simples com upload de .txt/.pdf ou texto digitado.

## Como a solucao funciona

1) O usuario envia um texto ou arquivo (txt/pdf) pela interface.
2) O backend extrai o texto (txt ou pdf) e faz limpeza basica.
3) Regras deterministicas detectam mensagens sociais/triviais, spam ou no-reply.
4) Caso nao caia nas regras, a IA (Gemini) classifica e gera a resposta em JSON.
5) A API valida o JSON, aplica ajustes e retorna categoria + resposta para a interface.

## Funcionalidades principais

- Upload de .txt/.pdf ou texto digitado.
- Classificacao Produtivo/Improdutivo.
- Resposta sugerida automaticamente.
- Regras para reduzir custo de IA (mensagens sociais, triviais, spam, no-reply).
- Tratamento de erros e validacao de JSON de retorno da IA.

## Tecnologias

- Backend: Python 3.12, Flask, google-generativeai, pypdf
- Frontend: HTML, CSS e JavaScript
- Deploy: Vercel (configurado via `vercel.json`)

## Estrutura do projeto

```
email-ai-classifier/
  api/
    index.py                     # Entry point para Vercel
  app/
    __init__.py                  # Factory e registro de rotas
    config.py
    routes/
      rotas_api.py               # POST /api/process
      rotas_site.py              # GET /
    services/
      cliente_ia.py              # Regras + chamada Gemini + parsing JSON
      leitor_arquivo.py          # Leitura de txt/pdf
      prompt/
        prompt.py                # Prompt de classificacao
    utils/
      Normaliza_texto.py         # Normalizacao basica
      preprocessamento_texto.py  # Stopwords e limpeza
      ProcessaPdf.py             # Extracao de pdf
      ProcessaTxt.py             # Extracao de txt
      Processa_texto.py          # Limpeza do texto digitado
      Respostas.py               # Regras sociais/triviais/spam
    templates/
      index.html                 # Interface web
    static/
      css/styles.css
      js/main.js
      icon/favicon.ico
  requirements.txt
  runtime.txt
  run.py                         # Execucao local
  vercel.json
  .env.example
  README.md
```

## Como rodar localmente (use python 3.12)

1) Criar e ativar o ambiente virtual
```bash
python -m venv venv
venv\Scripts\activate
```

2) Instalar dependencias
```bash
pip install -r requirements.txt
```

3) Configurar variaveis de ambiente
```bash
copy .env.example .env
```
Edite o `.env` e preencha `GEMINI_API_KEY`.

4) Iniciar o servidor
```bash
python run.py
```

5) Abrir no navegador
```
http://localhost:5000
```

## Variaveis de ambiente

Arquivo `.env` (exemplo em `.env.example`):

```env
FLASK_ENV=development
SECRET_KEY=dev
GEMINI_API_KEY=coloque_sua_chave
GEMINI_MODEL=models/gemini-2.5-flash
```

## API

`POST /api/process`

Entrada JSON:
```json
{ "text": "Preciso do status do caso 12345" }
```

Entrada FormData:
```js
const formData = new FormData();
formData.append("file", arquivo);
```

Resposta:
```json
{
  "categoria": "Produtivo",
  "resposta": "Vou verificar o status do caso 12345 e retorno em breve.",
  "justificativa_curta": "Solicitacao de status de caso em aberto.",
  "preview": "Preciso do status do caso 12345"
}
```

## Deploy

O projeto esta pronto para deploy em Vercel usando `api/index.py` como entry point.
Para outros provedores (Render, Heroku), basta apontar para `run.py` e configurar as variaveis de ambiente.

## Video demonstrativo

- Introducao e contexto do desafio.
- Demonstra a interface e o upload de um email.
- Mostra a classificacao e a resposta sugerida.
- Explicacao tecnica resumida (regras + Gemini + Flask).
- Conclusao e aprendizados.
