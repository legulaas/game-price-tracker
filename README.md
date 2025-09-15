# Game Price Tracker

Bot para Discord que busca preços de jogos em diferentes plataformas (Steam, PSN, Xbox, Nintendo) e notifica sobre promoções.

## Funcionalidades

- ✅ Buscar preços de jogos em tempo real
- ✅ Armazenar histórico de preços
- ✅ Mostrar melhor preço dos últimos 6 meses
- ✅ Interação via bot Discord
- ⬜ Agendamento de buscas diárias (será implementado com Laravel)
- ⬜ Notificações de preço abaixo do limiar desejado (será implementado com Laravel)

## Estrutura do Projeto

```
game-price-tracker/
├── discord_bot/            # Bot Discord para interação com usuários
├── price_scraper/          # Sistema de scraping de preços
├── database/               # Arquivos CSV (temporário, será SQLite)
└── README.md               # Documentação
```

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/game-price-tracker.git
cd game-price-tracker
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
playwright install
```

3. Configure o bot Discord:
   - Crie um aplicativo em https://discord.com/developers/applications
   - Obtenha o token do bot
   - Edite o arquivo `config.json` com seu token

## Uso

### Iniciar o Bot Discord

```bash
python -m discord_bot.main
```

### Comandos Disponíveis

- `!preco <jogo> [plataforma]` - Busca o preço atual de um jogo
- `!historico <jogo> [dias]` - Exibe o histórico de preços de um jogo
- `!observar <jogo> [preço_alvo]` - Adiciona um jogo à lista de observação
- `!ajuda` - Exibe a lista de comandos disponíveis

### Buscar Preço Diretamente (Linha de Comando)

```bash
python -m price_scraper.main --title "Elden Ring" --platform steam
```

## Integração com Laravel (Futuro)

O projeto está preparado para integração com um backend Laravel que irá:

1. Gerenciar banco de dados SQLite
2. Agendar buscas diárias em horários específicos
3. Processar filas de buscas
4. Enviar notificações para o Discord

## Tecnologias Utilizadas

- Python 3.8+
- Discord.py - Bot para Discord
- Playwright - Automação web para scraping
- CSV (temporário) / SQLite (futuro) - Armazenamento de dados
- Laravel (futuro) - Backend para gerenciamento de tarefas

## Licença

MIT