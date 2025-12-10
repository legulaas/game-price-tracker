# GamePriceTracker (GPT)

Sistema automatizado para monitoramento de preços de jogos digitais com Bot Discord. O sistema permite consultas de preço instantâneas e rastreamento de jogos (wishlist) com notificações diárias sobre promoções.

## Funcionalidades

- ✅ Buscar preços de jogos em tempo real (Steam)
- ✅ Sistema de rastreamento (wishlist) por usuário
- ✅ Notificações automáticas diárias sobre promoções
- ✅ Armazenamento de histórico de preços
- ✅ Preço alvo customizável por jogo
- ✅ Interação completa via Discord Bot
- ✅ Arquitetura modular e escalável
- ✅ Deploy com Docker e Docker Compose

## Estrutura do Projeto

```
game-price-tracker/
├── src/
│   ├── bot/                    # Discord Bot
│   │   ├── bot.py             # Bot principal
│   │   └── cogs/              # Comandos do bot
│   │       ├── game_commands.py
│   │       └── tracker_commands.py
│   ├── scraper/               # Web Scraping (Playwright)
│   │   ├── base.py           # Classe base
│   │   ├── steam.py          # Scraper Steam
│   │   └── factory.py        # Factory de scrapers
│   ├── database/              # Banco de Dados
│   │   ├── config.py         # Configuração SQLAlchemy
│   │   └── models.py         # Modelos (User, Game, TrackedGame, etc)
│   ├── services/              # Regras de Negócio
│   │   ├── game_service.py
│   │   ├── tracker_service.py
│   │   └── notification_service.py
│   ├── scheduler.py           # Scheduler para notificações diárias
│   └── main.py               # Entrypoint
├── alembic/                   # Migrações de Banco
├── docker-compose.yml         # Definição dos serviços
├── Dockerfile
├── requirements.txt
└── README.md
```

## Stack Tecnológica

- **Python 3.11+**
- **Discord.py** - Bot Discord
- **Playwright** - Web scraping assíncrono
- **MySQL 8.0** - Banco de dados
- **SQLAlchemy** - ORM assíncrono
- **Alembic** - Migrações de banco
- **APScheduler** - Agendamento de tarefas
- **Docker & Docker Compose** - Containerização

## Instalação

### Opção 1: Docker (Recomendado)

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/game-price-tracker.git
cd game-price-tracker
```

2. Crie um arquivo `.env` baseado no `.env.example`:
```bash
cp .env.example .env
```

3. Configure seu token do Discord no arquivo `.env`:
```
DISCORD_TOKEN=seu_token_aqui
```

4. Inicie os serviços com Docker Compose:
```bash
docker-compose up -d
```

5. Verifique os logs:
```bash
docker-compose logs -f app
```

### Opção 2: Instalação Local

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/game-price-tracker.git
cd game-price-tracker
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
playwright install chromium
```

4. Configure as variáveis de ambiente (crie um arquivo `.env`):
```
DISCORD_TOKEN=seu_token_aqui
DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/game_price_tracker
```

5. Execute as migrações:
```bash
alembic upgrade head
```

6. Inicie o bot:
```bash
python src/main.py
```

## Configurando o Bot Discord

1. Acesse o [Discord Developer Portal](https://discord.com/developers/applications)
2. Clique em "New Application"
3. Dê um nome ao seu bot
4. Vá em "Bot" no menu lateral
5. Clique em "Reset Token" e copie o token
6. Cole o token no arquivo `.env`
7. Em "Privileged Gateway Intents", habilite:
   - Presence Intent
   - Server Members Intent
   - Message Content Intent
8. Vá em "OAuth2" > "URL Generator"
9. Selecione os scopes: `bot`
10. Selecione as permissões: `Send Messages`, `Embed Links`, `Read Message History`
11. Copie a URL gerada e abra no navegador para adicionar o bot ao seu servidor

## Comandos Disponíveis

### Busca de Jogos

- `!search <nome do jogo>` ou `!s <nome do jogo>`
  - Busca jogos na Steam
  - Exemplo: `!search Cyberpunk 2077`

- `!price <URL do jogo>` ou `!p <URL do jogo>`
  - Verifica o preço atual de um jogo
  - Exemplo: `!price https://store.steampowered.com/app/1091500/Cyberpunk_2077/`

- `!platforms`
  - Lista as plataformas suportadas

### Rastreamento (Wishlist)

- `!track <URL do jogo> [preço alvo]` ou `!add <URL do jogo> [preço alvo]`
  - Adiciona um jogo à sua wishlist
  - Exemplo: `!track https://store.steampowered.com/app/1091500/ 29.99`
  - Se não especificar preço alvo, você será notificado em qualquer promoção

- `!untrack <ID do jogo>` ou `!remove <ID do jogo>`
  - Remove um jogo da sua wishlist
  - Exemplo: `!untrack 5`

- `!wishlist` ou `!list` ou `!tracked`
  - Mostra todos os jogos que você está rastreando

### Ajuda

- `!help`
  - Mostra todos os comandos disponíveis

## Sistema de Notificações

O bot verifica automaticamente os preços de todos os jogos rastreados diariamente às 15h (configurável via variável de ambiente `NOTIFICATION_HOUR`).

Você receberá uma mensagem direta (DM) do bot quando:
- Um jogo da sua wishlist entrar em promoção (se `notify_on_any_sale` = true)
- O preço atingir ou ficar abaixo do seu preço alvo (se configurado)

**Nota:** O bot só notifica uma vez a cada 24 horas por jogo para evitar spam.

## Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|---------|
| `DISCORD_TOKEN` | Token do bot Discord | *obrigatório* |
| `DATABASE_URL` | URL de conexão MySQL | `mysql+aiomysql://gpt_user:gpt_password@mysql:3306/game_price_tracker` |
| `MYSQL_ROOT_PASSWORD` | Senha root do MySQL | `root_password` |
| `MYSQL_DATABASE` | Nome do banco de dados | `game_price_tracker` |
| `MYSQL_USER` | Usuário do banco | `gpt_user` |
| `MYSQL_PASSWORD` | Senha do usuário | `gpt_password` |
| `NOTIFICATION_HOUR` | Hora das notificações (0-23) | `15` |
| `NOTIFICATION_MINUTE` | Minuto das notificações (0-59) | `0` |
| `HEADLESS` | Modo headless do navegador | `true` |

## Banco de Dados

### Modelos

- **User**: Usuários do Discord
- **Game**: Jogos e informações de preço
- **TrackedGame**: Relação entre usuários e jogos rastreados
- **PriceHistory**: Histórico de preços
- **Notification**: Log de notificações enviadas

### Migrações

Para criar uma nova migração:
```bash
alembic revision --autogenerate -m "descrição da mudança"
```

Para aplicar migrações:
```bash
alembic upgrade head
```

Para reverter uma migração:
```bash
alembic downgrade -1
```

## Desenvolvimento

### Adicionando Novas Plataformas

1. Crie um novo scraper em `src/scraper/` herdando de `BaseScraper`
2. Implemente os métodos `search_game()` e `get_game_details()`
3. Registre o scraper no `ScraperFactory` em `src/scraper/factory.py`

Exemplo:
```python
# src/scraper/epic.py
from .base import BaseScraper

class EpicScraper(BaseScraper):
    async def search_game(self, query: str):
        # Implementação
        pass

    async def get_game_details(self, url: str):
        # Implementação
        pass

# src/scraper/factory.py
class ScraperFactory:
    _scrapers = {
        "steam": SteamScraper,
        "epic": EpicScraper,  # Adicione aqui
    }
```

### Estrutura de Logs

Os logs são salvos em `logs/bot.log` e também exibidos no console.

## Deploy na Oracle Cloud

1. Provisione uma VM com Oracle Cloud Free Tier
2. Instale Docker e Docker Compose
3. Clone o repositório
4. Configure o arquivo `.env`
5. Execute `docker-compose up -d`

## Roadmap

- [ ] Suporte para Epic Games Store
- [ ] Suporte para GOG
- [ ] Interface web para gerenciamento
- [ ] Gráficos de histórico de preços
- [ ] Comparação de preços entre plataformas
- [ ] Sistema de alertas por webhook
- [ ] API REST
- [ ] Suporte para múltiplos idiomas

## Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

## Licença

MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## Suporte

Se encontrar problemas ou tiver sugestões, abra uma [issue](https://github.com/seu-usuario/game-price-tracker/issues) no GitHub.