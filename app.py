from flask import Flask, jsonify, request
from instagrapi import Client
import json
import os
from datetime import datetime
import threading
import time

app = Flask(__name__)

# aaa configuración de Instagram -bynd
INSTAGRAM_USERNAME = os.getenv('IG_USERNAME')
INSTAGRAM_PASSWORD = os.getenv('IG_PASSWORD')

client = Client()
chats_data = {}

def login_instagram():
    # ey intentamos login con session guardada primero -bynd
    try:
        if os.path.exists('session.json'):
            client.load_settings('session.json')
            client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
            print("Login exitoso con session guardada")
        else:
            raise Exception("No session file")
    except:
        # chintrolas no había session, login normal -bynd
        client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        client.dump_settings('session.json')
        print("Login exitoso, session nueva guardada")

def fetch_instagram_messages():
    # vavavava esta función corre en background cada 30 seg -bynd
    while True:
        try:
            threads = client.direct_threads(amount=5)
            
            for thread in threads:
                thread_id = str(thread.id)
                messages = client.direct_messages(thread_id, amount=5)
                
                # aaa procesamos los mensajes -bynd
                chat_messages = []
                for msg in reversed(messages):  # q queden en orden cronológico -bynd
                    sender_name = msg.user_id
                    # ey buscamos el username real -bynd
                    try:
                        user_info = client.user_info(msg.user_id)
                        sender_name = user_info.username
                    except:
                        pass
                    
                    chat_messages.append({
                        'sender': sender_name,
                        'text': msg.text or '',
                        'timestamp': msg.timestamp.isoformat(),
                        'is_new': not msg.seen  # para el divisor de nuevos -bynd
                    })
                
                # chintrolas guardamos todo -bynd
                chats_data[thread_id] = {
                    'name': thread.thread_title or thread.users[0].username,
                    'messages': chat_messages,
                    'last_updated': datetime.now().isoformat()
                }
            
            # fokeis guardamos en archivo por si acaso -bynd
            with open('chats.json', 'w') as f:
                json.dump(chats_data, f)
                
        except Exception as e:
            print(f"Error fetching messages: {e}")
        
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
    return jsonify({'status': 'ok'})

def init_app():
    # chintrolas primero login y luego background thread -bynd
    login_instagram()
    
    # ala iniciamos el thread q fetchea mensajes -bynd
    fetch_thread = threading.Thread(target=fetch_instagram_messages, daemon=True)
    fetch_thread.start()

if __name__ == '__main__':
    # q chidoteee para desarrollo local -bynd
    init_app()
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
else:
    # vavavava para gunicorn en producción -bynd
    init_app()
