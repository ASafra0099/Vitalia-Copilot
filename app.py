from flask import Flask, render_template, request, redirect, url_for, Response
from flask_socketio import SocketIO, join_room, leave_room, emit
import os
import openai
import json

app = Flask(__name__,template_folder="templates")
app.config['SECRET_KEY'] = 'secret key'
socketio = SocketIO(app)     #Allows real-time communication between the server and clients using WebSockets.
                             #join, stop_chat, and send_message. These events are used for real-time chat functionality. 
openai.api_key = "api key"



def generate_transcript_and_summary(room):
    filename = f'chats/{room}.txt'
    with open(filename, 'r') as file:
        chat_content = file.read()
        
    function_description = [
        {
            "name": "Transcript",
            "description": "Extract the consultation information from the chat conversation stored in chat_content",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient name": {
                        "type": "string",
                        "description": "display the name of  patient mentioned in the chat_content. ",
                    },
                    "symptoms": {
                        "type": "string",
                        "description": "display the symptoms of the patient mentioned in the chat_content. ",
                    },
                    "Allergies": {
                        "type": "string",
                        "description": "display the allergies of the patient mentioned in the chat_content.",
                    },
                    "illness": {
                        "type": "string",
                        "description": "display the illness of the patient mentioned in the chat_content.",
                    },
                    "Medications": {
                        "type": "string",
                        "description": "display the Medications of the patient mentioned in the chat_content.",
                    },
                },
                "required": ["Patient_Name", "symptoms", "Allergies", "illness", "Medications"],
            },
        }
    ]

    prompt = f"return information from chat_content: {chat_content}"
    messages = [{"role": "user", "content": prompt}]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=messages,
        functions=function_description,
        function_call="auto"
    )

    arguments = response["choices"][0]["message"]["function_call"]["arguments"]
    json_obj = json.loads(arguments)

  
    transcript_summary = (
f"Patient name: {json_obj['patient name']}\n\n\n"
f"Symptoms: {json_obj['symptoms']}\n\n\n"
f"Allergies: {json_obj['Allergies']}\n\n\n"
f"Illness: {json_obj['illness']}\n\n\n"
f"Medications: {json_obj['Medications']}"

    )

    return transcript_summary

@app.route('/')
def home():
    return render_template('Home.html')


@app.route('/start')
def start():
    return render_template('start.html')


@app.route('/chat')
def chat():
    user_type = request.args.get('user-type')
    room = request.args.get('room')
    if user_type and room:
        return render_template('chat.html', user_type=user_type, room=room)
    else:
        return redirect('/')


@socketio.on('join')
def handle_join(data):
    user_type = data['user_type']
    room = data['room']
    join_room(room)
    emit('message', {'user_type': user_type, 'message': f' has joined the room'}, room=room)
    
def save_message(room, message):
    filename = f'chats/{room}.txt'
    with open(filename, 'a') as file:
        file.write(message + '\n')
        
def delete_conversation(room):
    filename = f'chats/{room}.txt'
    if os.path.exists(filename):
        os.remove(filename)
        print(f'Conversation in room {room} deleted.')
        
        
@socketio.on('stop_chat')
def handle_stop_chat(data):
    room = data['room']
    emit('confirm_stop', {'room': room}, room=room)




@socketio.on('send_message')
def handle_send_message(data):
    user_type = data['user_type']
    room = data['room']
    message = data['message']
    emit('message', {'user_type': user_type, 'message': message}, room=room)
    save_message(room, f'{user_type}: {message}')



@app.route('/transcript/<room>')
def transcript(room):
    transcript_summary = generate_transcript_and_summary(room)
    return render_template('transcript.html', transcript_summary=transcript_summary)




if __name__ == '__main__':
    app.run()




