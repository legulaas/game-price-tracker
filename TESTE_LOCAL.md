# Guia de Teste Local - GamePriceTracker

## ✅ Pré-requisitos Concluídos

Já configuramos tudo que você precisa:

1. ✅ Python 3.14 instalado
2. ✅ Dependências instaladas (`discord.py`, `playwright`, `SQLAlchemy`, etc.)
3. ✅ Playwright browsers instalados
4. ✅ MySQL rodando em Docker (porta 3306)
5. ✅ Banco de dados criado com todas as tabelas
6. ✅ Scraper testado e funcionando

## 🤖 Como Obter um Token do Discord Bot

Para testar o bot, você precisa de um token do Discord:

### Passo a Passo:

1. Acesse https://discord.com/developers/applications
2. Clique em **"New Application"**
3. Dê um nome (ex: "GamePriceTracker Test")
4. Vá em **"Bot"** no menu lateral
5. Clique em **"Reset Token"** e copie o token
6. **IMPORTANTE**: Em "Privileged Gateway Intents", habilite:
   - ✅ Presence Intent
   - ✅ Server Members Intent
   - ✅ Message Content Intent (MUITO IMPORTANTE!)
7. Vá em **"OAuth2"** > **"URL Generator"**
8. Selecione os scopes:
   - ✅ `bot`
9. Selecione as permissões:
   - ✅ Send Messages
   - ✅ Embed Links
   - ✅ Read Message History
   - ✅ Read Messages/View Channels
10. Copie a URL gerada e abra no navegador para adicionar o bot ao seu servidor de teste

### Adicionar o Token ao Projeto:

Edite o arquivo `.env` e substitua `your_discord_bot_token_here` pelo token que você copiou:

```env
DISCORD_TOKEN=seu_token_aqui_sem_aspas
```

## 🚀 Iniciando o Bot

Com o token configurado, execute:

```bash
# Ativar o ambiente virtual (se ainda não estiver ativado)
.\venv\Scripts\activate

# Iniciar o bot
python src/main.py
```

Você deverá ver algo como:

```
INFO - Starting Game Price Tracker Bot...
INFO - Initializing database...
INFO - Database initialized successfully
INFO - Starting Discord bot...
INFO - Cogs loaded successfully
INFO - Bot logged in as GamePriceTracker#1234 (ID: 123456789)
INFO - Connected to 1 guilds
INFO - Scheduler started. Daily price check scheduled at 15:00
```

## 🧪 Testando os Comandos

Agora vá ao seu servidor Discord onde adicionou o bot e teste os comandos:

### 1. Buscar jogos:

```
!search Cyberpunk 2077
```

ou

```
!s Elden Ring
```

### 2. Verificar preço de um jogo específico:

```
!price https://store.steampowered.com/app/1091500/Cyberpunk_2077/
```

### 3. Adicionar um jogo à sua wishlist:

```
!track https://store.steampowered.com/app/1091500/Cyberpunk_2077/ 29.99
```

### 4. Ver sua wishlist:

```
!wishlist
```

ou

```
!list
```

### 5. Remover um jogo da wishlist:

```
!untrack 1
```

(O número 1 é o ID do jogo que aparece na sua wishlist)

### 6. Listar plataformas suportadas:

```
!platforms
```

### 7. Ver ajuda:

```
!help
```

## 🔍 Verificando o Banco de Dados

Para ver os dados salvos no banco:

```bash
# Ver usuários
docker exec gpt_mysql_local mysql -ugpt_user -pgpt_password game_price_tracker -e "SELECT * FROM users;"

# Ver jogos
docker exec gpt_mysql_local mysql -ugpt_user -pgpt_password game_price_tracker -e "SELECT id, title, current_price, is_on_sale FROM games;"

# Ver jogos rastreados
docker exec gpt_mysql_local mysql -ugpt_user -pgpt_password game_price_tracker -e "SELECT * FROM tracked_games;"
```

## 🧪 Teste do Scraper (Sem Bot Discord)

Se você quiser testar apenas o scraper sem configurar o bot Discord:

```bash
python test_scraper.py
```

Isso vai buscar informações sobre Cyberpunk 2077 na Steam.

## 📊 Monitorando Logs

Os logs são salvos em `logs/bot.log` e também aparecem no console.

Para ver os logs em tempo real:

```bash
# Windows
type logs\bot.log

# Ou acompanhar em tempo real (precisa ter tail instalado)
tail -f logs/bot.log
```

## 🛑 Parando o Ambiente

### Parar o bot:
Pressione `Ctrl+C` no terminal onde o bot está rodando

### Parar o MySQL:
```bash
docker-compose -f docker-compose.local.yml down
```

### Parar e remover dados do MySQL (cuidado!):
```bash
docker-compose -f docker-compose.local.yml down -v
```

## 🐛 Troubleshooting

### "DISCORD_TOKEN environment variable not set"
- Verifique se você editou o arquivo `.env` com seu token
- Certifique-se que o arquivo `.env` está na raiz do projeto

### "Could not connect to database"
- Verifique se o MySQL está rodando: `docker ps`
- Se não estiver, inicie: `docker-compose -f docker-compose.local.yml up -d`

### "Module not found"
- Certifique-se que está no ambiente virtual: `.\venv\Scripts\activate`
- Reinstale as dependências: `pip install -r requirements.txt`

### Bot não responde aos comandos
- Verifique se você habilitou "Message Content Intent" no Discord Developer Portal
- Certifique-se que o bot tem permissão para ler/enviar mensagens no canal

### Scraper retorna resultados vazios
- Pode ser bloqueio da Steam. Teste desabilitando headless no `.env`:
  ```
  HEADLESS=false
  ```

## 📝 Próximos Passos

Após testar localmente:

1. **Adicionar mais jogos à wishlist** e testar as notificações
2. **Testar o scheduler** (aguarde até 15h ou mude `NOTIFICATION_HOUR` no `.env`)
3. **Explorar o histórico de preços** no banco de dados
4. **Adicionar suporte para outras plataformas** (Epic, GOG, etc.)

## 🎯 Comandos Úteis Resumidos

```bash
# Iniciar MySQL
docker-compose -f docker-compose.local.yml up -d

# Ativar ambiente virtual
.\venv\Scripts\activate

# Iniciar bot
python src/main.py

# Testar scraper
python test_scraper.py

# Parar MySQL
docker-compose -f docker-compose.local.yml down

# Ver logs do MySQL
docker logs gpt_mysql_local

# Acessar MySQL diretamente
docker exec -it gpt_mysql_local mysql -ugpt_user -pgpt_password game_price_tracker
```

## 🎉 Pronto!

Seu ambiente de testes está configurado e funcionando! Agora é só adicionar o token do Discord e começar a testar.
