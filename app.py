from flask import Flask, jsonify, request
from instagrapi import Client
import json
import os
from datetime import datetime
import threading
import time

app = Flask(__name__)

# aaa configuración de Instagram con cookies -bynd
SESSION_JSON = os.getenv('SESSION_JSON')  # ey las cookies desde variable de entorno -bynd

client = Client()
chats_data = {}

def login_instagram():
    # vavavava usamos las cookies directamente -bynd
    try:
        if SESSION_JSON:
            # chintrolas cargamos las cookies -bynd
            cookies_data = json.loads(SESSION_JSON)
            
            # ey configuramos las settings del client con las cookies -bynd
            settings = {
                "uuids": {
                    "phone_id": cookies_data.get('ig_did', ''),
                    "uuid": cookies_data.get('ig_did', ''),
                    "client_session_id": cookies_data.get('sessionid', ''),
                    "advertising_id": cookies_data.get('ig_did', ''),
                    "device_id": cookies_data.get('ig_did', '')
                },
                "cookies": {
                    "sessionid": cookies_data.get('sessionid', ''),
                    "ds_user_id": cookies_data.get('ds_user_id', ''),
                    "csrftoken": cookies_data.get('csrftoken', ''),
                    "mid": cookies_data.get('mid', ''),
                    "ig_did": cookies_data.get('ig_did', '')
                },
                "last_login": int(datetime.now().timestamp())
            }
            
            client.set_settings(settings)
            
            # fokeis verificamos q funcione -bynd
            user_info = client.account_info()
            print(f"✓ Login exitoso como @{user_info.username}")
        else:
            print("✗ No hay SESSION_JSON")
            raise Exception("No SESSION_JSON provided")
    except Exception as e:
        print(f"✗ Error en login: {e}")
        raise e

def fetch_instagram_messages():
    # q chidoteee esta función corre en background cada 30 seg -bynd
    while True:
        try:
            threads = client.direct_threads(amount=5)
            
            for thread in threads:
                thread_id = str(thread.id)
                messages = client.direct_messages(thread_id, amount=5)
                
                # aaa procesamos los mensajes -bynd
                chat_messages = []
                for msg in reversed(messages):  # orden cronológico -bynd
                    sender_name = str(msg.user_id)
                    # ey buscamos el username real -bynd
                    try:
                        if hasattr(msg, 'user') and msg.user:
                            sender_name = msg.user.username
                        else:
                            user_info = client.user_info(msg.user_id)
                            sender_name = user_info.username
                    except:
                        pass
                    
                    chat_messages.append({
                        'sender': sender_name,
                        'text': msg.text or '',
                        'timestamp': msg.timestamp.isoformat() if hasattr(msg.timestamp, 'isoformat') else str(msg.timestamp),
                        'is_new': not getattr(msg, 'seen', True)  # para el divisor de nuevos -bynd
                    })
                
                # chintrolas guardamos todo -bynd
                chat_name = thread.thread_title
                if not chat_name and hasattr(thread, 'users') and thread.users:
                    chat_name = thread.users[0].username
                if not chat_name:
                    chat_name = f"Chat {thread_id[:8]}"
                
                chats_data[thread_id] = {
                    'name': chat_name,
                    'messages': chat_messages,
                    'last_updated': datetime.now().isoformat()
                }
            
            print(f"✓ Fetched {len(chats_data)} chats")
                
        except Exception as e:
            print(f"✗ Error fetching messages: {e}")
        
        time.sleep(30)  # cada 30 segundos -bynd

@app.route('/chats', methods=['GET'])
def get_chats():
    # ey regresamos top 5 chats -bynd
    chats_list = []
    for thread_id, data in list(chats_data.items())[:5]:
        chats_list.append({
            'id': thread_id,
            'name': data['name'],
            'last_message': data['messages'][-1]['text'] if data['messages'] else '',
            'has_new': any(msg['is_new'] for msg in data['messages'])
        })
    
    return jsonify({'chats': chats_list})

@app.route('/chat/<thread_id>', methods=['GET'])
def get_chat_messages(thread_id):
    # aaa regresamos los mensajes de un chat específico -bynd
    if thread_id not in chats_data:
        return jsonify({'error': 'Chat no encontrado'}), 404
    
    chat = chats_data[thread_id]
    return jsonify({
        'name': chat['name'],
        'messages': chat['messages']
    })

@app.route('/send', methods=['POST'])
def send_message():
    # vavavava mandamos mensaje -bynd
    data = request.json
    thread_id = data.get('thread_id')
    message = data.get('message')
    
    if not thread_id or not message:
        return jsonify({'error': 'Faltan datos'}), 400
    
    try:
        client.direct_send(message, [int(thread_id)])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    # ey endpoint simple para verificar q todo jala -bynd
    return jsonify({'status': 'ok', 'chats_loaded': len(chats_data)})

def init_app():
    # chintrolas primero login y luego background thread -bynd
    print("Iniciando app...")
    login_instagram()
    
    # ala iniciamos el thread q fetchea mensajes -bynd
    fetch_thread = threading.Thread(target=fetch_instagram_messages, daemon=True)
    fetch_thread.start()
    print("✓ Background thread iniciado")

if __name__ == '__main__':
    # q chidoteee para desarrollo local -bynd
    init_app()
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
else:
    # vavavava para gunicorn en producción -bynd
    init_app()
