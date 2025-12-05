from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
import bcrypt

load_dotenv()

app = Flask(__name__)

# ========================
# CORS CONFIGURATION
# ========================
# Allow requests from frontend (adjust based on your Netlify domain)
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://agrigrowthiot.netlify.app",  # Local development
            "http://localhost:5173",  # Vite development
            "http://localhost:8000",  # Alternative local
            os.getenv("FRONTEND_URL", "http://localhost:3000")  # Environment variable for production
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# ========================
# MongoDB Configuration
# ========================
MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = os.getenv('DB_NAME')
COLLECTION_NAME = os.getenv('COLLECTION_NAME')

print("\n" + "="*60)
print(" INICIANDO SERVIDOR BACKEND ")
print("="*60)
print(f"Tentando conectar ao MongoDB...")
print(f"Database: {DB_NAME}")
print(f"Collection: {COLLECTION_NAME}")

# Initialize variables
client = None
db = None
collection = None
users_collection = None

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("✓ Conectado ao MongoDB Atlas com sucesso!")

    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    
    # Check data in main collection
    count = collection.count_documents({})
    print(f"✓ Coleção '{COLLECTION_NAME}': {count} documento(s)")

    # Load users collection
    users_collection = db['users']
    user_count = users_collection.count_documents({})
    print(f"✓ Coleção 'users': {user_count} usuário(s)")

except Exception as e:
    print(f"✗ ERRO ao conectar com MongoDB: {e}")
    print("\nVerifique:")
    print("   - MONGO_URI está correto no .env")
    print("   - IP está permitido no Network Access do Atlas")
    print("   - Database e collections existem")

print("="*60 + "\n")

# ========================
# HEALTH CHECK ROUTE
# ========================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Check API and database health status"""
    try:
        if client and collection:
            client.admin.command('ping')
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'records': collection.count_documents({})
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'database': 'disconnected'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# ========================
# SENSOR DATA ROUTES
# ========================

@app.route('/api/data', methods=['GET'])
def get_sensor_data():
    """Get sensor data with optional filtering"""
    if collection is None:
        return jsonify({'error': 'Conexão com MongoDB não estabelecida'}), 500

    try:
        limit = int(request.args.get('limit', 100))
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        query = {}
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter['$gte'] = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if end_date:
                date_filter['$lte'] = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query['created_at'] = date_filter

        feeds = list(collection.find(
            query,
            {'_id': 0, 'field1': 1, 'field2': 1, 'created_at': 1}
        ).sort('created_at', -1).limit(limit))

        formatted_feeds = []
        for feed in reversed(feeds):
            formatted_feeds.append({
                'field1': feed.get('field1'),
                'field2': feed.get('field2'),
                'created_at': feed.get('created_at')
            })

        valid_feeds = [f for f in formatted_feeds if f['field1'] is not None and f['field2'] is not None]

        return jsonify({
            'feeds': formatted_feeds,
            'channel': {'id': 'mongodb_channel', 'name': 'MongoDB Sensor Data'},
            'stats': {
                'total': len(formatted_feeds),
                'valid': len(valid_feeds),
                'filters_applied': {
                    'limit': limit,
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
        }), 200

    except Exception as e:
        print(f"Erro em /api/data: {e}")
        return jsonify({'error': str(e)}), 500


# ========================
# USER MANAGEMENT ROUTES
# ========================

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users (without passwords)"""
    if users_collection is None:
        return jsonify({'error': 'Banco de dados indisponível'}), 500
    try:
        users = list(users_collection.find({}, {'_id': 0, 'senha': 0}).sort('id', 1))
        return jsonify(users), 200
    except Exception as e:
        print(f"Erro GET /api/users: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/users', methods=['POST'])
def create_user():
    """Create a new user"""
    if users_collection is None:
        return jsonify({'error': 'Banco de dados indisponível'}), 500

    try:
        data = request.get_json()
        if not data or not data.get('nome') or not data.get('email') or not data.get('senha'):
            return jsonify({'error': 'Nome, email e senha são obrigatórios'}), 400

        email = data['email'].strip().lower()
        if users_collection.find_one({'email': email}):
            return jsonify({'error': 'Este email já está cadastrado'}), 400

        # Generate next ID
        last = users_collection.find().sort('id', -1).limit(1)
        last_doc = next(last, None)
        new_id = (last_doc['id'] + 1) if last_doc else 1

        # Hash password
        hashed_senha = bcrypt.hashpw(data['senha'].encode('utf-8'), bcrypt.gensalt())

        new_user = {
            'id': new_id,
            'nome': data['nome'].strip(),
            'email': email,
            'funcao': data.get('funcao', 'Operador'),
            'status': data.get('status', 'Ativo'),
            'senha': hashed_senha
        }

        users_collection.insert_one(new_user)
        del new_user['senha']
        return jsonify(new_user), 201

    except Exception as e:
        print(f"Erro ao criar usuário: {e}")
        return jsonify({'error': 'Erro interno ao salvar usuário'}), 500


@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update an existing user"""
    if users_collection is None:
        return jsonify({'error': 'Banco de dados indisponível'}), 500

    try:
        data = request.get_json()
        if not data or not data.get('nome') or not data.get('email'):
            return jsonify({'error': 'Nome e email são obrigatórios'}), 400

        email = data['email'].strip().lower()

        # Check email conflict
        if users_collection.find_one({'email': email, 'id': {'$ne': user_id}}):
            return jsonify({'error': 'Este email já está em uso por outro usuário'}), 400

        updated = {
            'nome': data['nome'].strip(),
            'email': email,
            'funcao': data.get('funcao', 'Operador'),
            'status': data.get('status', 'Ativo')
        }

        # Update password if provided
        if data.get('senha'):
            if data['senha'] != data.get('confirmarSenha', ''):
                return jsonify({'error': 'Senhas não coincidem'}), 400
            hashed_senha = bcrypt.hashpw(data['senha'].encode('utf-8'), bcrypt.gensalt())
            updated['senha'] = hashed_senha

        result = users_collection.update_one({'id': user_id}, {'$set': updated})
        if result.modified_count:
            updated['id'] = user_id
            return jsonify(updated), 200
        else:
            return jsonify({'error': 'Usuário não encontrado'}), 404

    except Exception as e:
        print(f"Erro ao atualizar usuário: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user"""
    if users_collection is None:
        return jsonify({'error': 'Banco de dados indisponível'}), 500

    try:
        result = users_collection.delete_one({'id': user_id})
        if result.deleted_count:
            return jsonify({'message': 'Usuário excluído com sucesso'}), 200
        else:
            return jsonify({'error': 'Usuário não encontrado'}), 404
    except Exception as e:
        print(f"Erro ao excluir usuário: {e}")
        return jsonify({'error': str(e)}), 500


# ========================
# AUTHENTICATION ROUTES
# ========================

@app.route('/api/login', methods=['POST'])
def login():
    """User login endpoint"""
    if users_collection is None:
        return jsonify({'error': 'Banco de dados indisponível'}), 500

    try:
        data = request.get_json()
        if not data or not data.get('email') or not data.get('senha'):
            return jsonify({'error': 'Email e senha são obrigatórios'}), 400

        email = data['email'].strip().lower()
        user = users_collection.find_one({'email': email}, {'_id': 0})

        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 401

        if not bcrypt.checkpw(data['senha'].encode('utf-8'), user['senha']):
            return jsonify({'error': 'Senha incorreta'}), 401

        # Return user without password
        del user['senha']
        return jsonify({'message': 'Login bem-sucedido', 'user': user}), 200

    except Exception as e:
        print(f"Erro no login: {e}")
        return jsonify({'error': 'Erro interno no login'}), 500


# ========================
# START SERVER
# ========================

if __name__ == '__main__':
    print("\n" + "="*60)
    print(" SERVIDOR BACKEND RODANDO ")
    print("="*60)
    print("\nRotas disponíveis:")
    print("   GET    /api/health")
    print("   GET    /api/data")
    print("   GET    /api/users")
    print("   POST   /api/users")
    print("   PUT    /api/users/<id>")
    print("   DELETE /api/users/<id>")
    print("   POST   /api/login")
    print("\nURL: http://localhost:5000")
    print("="*60 + "\n")
    
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    app.run(debug=debug, port=port, host='0.0.0.0')
