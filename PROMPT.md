# Project Name: GamePriceTracker (GPT)

## 1. Visão Geral do Projeto
O **GamePriceTracker** é um sistema automatizado para monitoramento de preços de jogos digitais. A interface primária atual é um Bot do Discord, mas a arquitetura deve ser agnóstica para suportar uma interface Web futura.
O sistema permite consultas de preço instantâneas e um sistema de rastreamento (wishlist) que notifica usuários diariamente sobre promoções.

## 2. Stack Tecnológica Recomendada
* **Linguagem:** Python 3.11+
* **Interface Discord:** `discord.py` ou `hikari`
* **Web Scraper:** Playwright (Python sync/async)
* **Banco de Dados:** MySQL
* **ORM:** SQLAlchemy (Async) ou Prisma Client Python
* **Gerenciamento de Tarefas:** `APScheduler` (para o cronjob das 15h)
* **Infraestrutura:** Docker & Docker Compose (Essencial para deploy na Oracle Cloud)

## 3. Arquitetura de Pastas Sugerida
O projeto deve ser reestruturado para uma arquitetura modular, abandonando scripts soltos na raiz.

```text
/game-price-tracker
├── /src
│   ├── /bot             # Lógica do Discord Bot (Cogs/Commands)
│   ├── /scraper         # Lógica do Playwright (Search & Product Page)
│   ├── /database        # Modelos do Banco e Configuração de Conexão
│   ├── /services        # Regras de Negócio (ex: NotificationService, TrackerService)
│   └── main.py          # Entrypoint que inicia o Bot e o Scheduler
├── /alembic             # Migrações de Banco de Dados (se usar SQLAlchemy)
├── docker-compose.yml   # Definição dos serviços (App + MySQL)
├── Dockerfile
├── requirements.txt
└── README.md