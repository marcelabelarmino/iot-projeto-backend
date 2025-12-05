# IoT Backend - Flask API

Backend API para o sistema de monitoramento de umidade e temperatura. Construído com Flask, MongoDB e autenticação com bcrypt.

## 📋 Requisitos

- Python 3.8+
- MongoDB Atlas (ou MongoDB local)
- pip (gerenciador de pacotes Python)

## 🚀 Instalação e Configuração

### 1. Clonar o repositório

```bash
git clone https://github.com/seu-usuario/iot-backend.git
cd iot-backend
```

### 2. Criar ambiente virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente

Copie o arquivo `.env.example` para `.env`:

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas credenciais:

```env
MONGO_URI=mongodb+srv://seu_usuario:sua_senha@seu_cluster.mongodb.net/?retryWrites=true&w=majority
DB_NAME=seu_database
COLLECTION_NAME=sua_colecao
FLASK_ENV=development
PORT=5000
FRONTEND_URL=http://localhost:3000
```

### 5. Executar o servidor

```bash
python app.py
```

O servidor iniciará em `http://localhost:5000`

## 📚 API Endpoints

### Health Check

```
GET /api/health
```

Verifica o status da API e da conexão com o banco de dados.

### Dados de Sensores

```
GET /api/data?limit=100&start_date=2024-01-01&end_date=2024-01-31
```

Retorna dados de sensores (umidade e temperatura) com filtros opcionais.

### Usuários

**Listar usuários:**
```
GET /api/users
```

**Criar usuário:**
```
POST /api/users
Content-Type: application/json

{
  "nome": "João Silva",
  "email": "joao@email.com",
  "senha": "senha123",
  "funcao": "Operador",
  "status": "Ativo"
}
```

**Atualizar usuário:**
```
PUT /api/users/{id}
Content-Type: application/json

{
  "nome": "João Silva",
  "email": "joao@email.com",
  "funcao": "Administrador",
  "status": "Ativo",
  "senha": "nova_senha123"  // opcional
}
```

**Deletar usuário:**
```
DELETE /api/users/{id}
```

### Autenticação

**Login:**
```
POST /api/login
Content-Type: application/json

{
  "email": "joao@email.com",
  "senha": "senha123"
}
```

Retorna:
```json
{
  "message": "Login bem-sucedido",
  "user": {
    "id": 1,
    "nome": "João Silva",
    "email": "joao@email.com",
    "funcao": "Operador",
    "status": "Ativo"
  }
}
```

## 🔒 Segurança

- Senhas são hasheadas com bcrypt (nunca armazenadas em texto plano)
- CORS configurado para aceitar requisições apenas do frontend autorizado
- Senhas não são retornadas nas respostas da API

## 🌐 Deployment no Render

### 1. Criar conta no Render

Acesse [render.com](https://render.com) e faça login/cadastro.

### 2. Criar novo Web Service

- Clique em "New +" → "Web Service"
- Selecione este repositório do GitHub
- Configure:
  - **Name:** iot-backend
  - **Runtime:** Python 3
  - **Build Command:** `pip install -r requirements.txt`
  - **Start Command:** `gunicorn app:app`

### 3. Adicionar variáveis de ambiente

No dashboard do Render, em "Environment":

```
MONGO_URI=mongodb+srv://seu_usuario:sua_senha@seu_cluster.mongodb.net/?retryWrites=true&w=majority
DB_NAME=seu_database
COLLECTION_NAME=sua_colecao
FLASK_ENV=production
PORT=10000
FRONTEND_URL=https://seu-dominio-netlify.netlify.app
```

### 4. Deploy

Clique em "Create Web Service". O Render fará deploy automático a cada push no main.

## 🔧 Desenvolvimento

### Estrutura do projeto

```
iot-backend/
├── app.py              # Aplicação Flask principal
├── requirements.txt    # Dependências Python
├── .env.example       # Exemplo de variáveis de ambiente
├── .gitignore         # Arquivos a ignorar no Git
└── README.md          # Este arquivo
```

### Adicionar novas dependências

```bash
pip install nova-dependencia
pip freeze > requirements.txt
```

## 🐛 Troubleshooting

### "Conexão com MongoDB não estabelecida"

- Verifique se `MONGO_URI` está correto
- Confirme que seu IP está na whitelist do MongoDB Atlas
- Verifique nome do database em `DB_NAME`

### CORS errors

- Certifique-se que `FRONTEND_URL` está configurado corretamente
- Para local development, use `http://localhost:3000`
- Para Netlify, use `https://seu-dominio.netlify.app`

### Erro de autenticação

- Verifique se o usuário existe no banco
- Confirme se a senha está correta

## 📧 Contato e Suporte

Para dúvidas ou problemas, abra uma issue no repositório.

---

**Feito com ❤️ para monitoramento inteligente de ambientes**
