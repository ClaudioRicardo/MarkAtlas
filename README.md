# MarkAtlas

Este projeto é uma API para processar pedidos de compra (Supply Requests) e calcular os impostos brasileiros (ICMS, IPI, PIS, COFINS, ISS) usando a biblioteca `brazilian-tax`. Ele inclui um chatbot simples para consultar impostos por estado.

## 📁 Estrutura do Projeto

```
markatlas/
├── src/
│   ├── chatbot/
│   │   ├── config.py            # Configurações do Gemini (API Key)
│   │   ├── database.py          # Banco de dados SQLite para histórico
│   │   ├── intent_classifier.py # Classificador de intenções (regex + IA)
│   │   ├── utils.py             # Funções utilitárias
│   │   └── main.py              # Ponto de entrada do chatbot
│   ├── core/
│   │   └── tax_calculator.py    # Cálculo de impostos
│   ├── models/
│   │   ├── data_models.py       # Modelos Pydantic (SupplyRequest, TaxResponse)
│   │   └── schema.sql           # Script de criação do banco de dados
│   ├── server/
│   │   ├── api_config.py        # Configurações da API
│   │   ├── middleware.py        # Middlewares (cors, rate limit, auth)
│   │   └── main.py              # Ponto de entrada da API (FastAPI)
│   ├── utils/
│   │   └── helper_functions.py  # Funções auxiliares
│   └── prompts/
│       └── tax_classification.txt # Template de prompt para IA
├── openspec/
│   ├── specifications/          # Especificações técnicas e de arquitetura
│   ├── api-documentation.md     # Documentação da API (Swagger/OpenAPI)
│   └── system.md                # Documentação geral do sistema
├── .agent/                      # Configurações de IA do Antigravity
├── .env                         # Variáveis de ambiente (NÃO INCLUIR NO GIT)
├── .gitignore                   # Arquivos ignorados pelo Git
├── README.md                    # Este arquivo
├── requirements.txt             # Dependências do projeto
└── schema.sql                   # SQL para schema do banco de dados (backup/referência)
```

## 🚀 Como Executar

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
GEMINI_API_KEY=sua_api_key_google_aqui
RATE_LIMIT_MAX_REQUESTS=10
RATE_LIMIT_WINDOW_SECONDS=60
```

### 3. Executar a API

```bash
uvicorn src.server.main:app --reload
```

### 4. Interagir com o Chatbot

O chatbot está disponível na CLI. Execute:

```bash
uvicorn src.chatbot.main
```

ou rode os testes:

```bash
pytest tests/chatbot/test_integration.py
```

## 🔌 Endpoints da API

### Calcular Impostos
```http
POST /tax/calculate

Body:
{
  "product_name": "Produto Teste",
  "quantity": 10,
  "unit_price": 150.0,
  "origin_state": "sp",
  "destination_state": "rj",
  "tax_regime": "lucro_presumido"
}
```

### Chatbot
```http
POST /chatbot/ask

Body:
{
  "user_id": "user123",
  "message": "Qual é o ICMS para SP?"
}
```

## 🔧 Configuração do Chatbot

O chatbot usa:
- **Gemini API** para compreensão de linguagem natural
- **SQLite** para armazenar histórico de conversas
- **Regex + IA** para classificar intenções

### Criar Banco de Dados (Se não existir)
```bash
python -c "import sqlite3; conn = sqlite3.connect('chatbot.db'); conn.execute('CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, user_id TEXT, message TEXT, response TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)'); conn.commit(); conn.close()"
```

## 📚 Documentação

- [Documentação da API](openspec/api-documentation.md)
- [Especificações Técnicas](openspec/specifications/)
- [Arquitetura do Sistema](openspec/system.md)

## 📋 Testes

```bash
pytest tests/
```

## 🤝 Colaboração

### Como Contribuir
1. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
2. Commite suas mudanças (`git commit -m 'feat: Add some AmazingFeature'`)
3. Push para a branch (`git push origin feature/AmazingFeature`)
4. Abra um Pull Request

### Padrões
- Siga os padrões do PEP 8 para Python
- Use docstrings para todas as funções e classes
- Siga as convenções de tipos Pydantic
- Use o arquivo `schema.sql` como referência para o schema do banco de dados

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 📞 Suporte

Para suporte, abra uma issue no repositório.
