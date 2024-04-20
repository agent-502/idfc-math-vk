import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import random
import json
import os
import time

# Initialize VK API
vk_session = vk_api.VkApi(token="7817c4357307acc6bd768b35d5a1af874fbcd305d5daa4a1ea6e66d0972d2b594f26602df2a06f540ea18")
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, "208528832")

# Create or load user scores from JSON file
if not os.path.exists("user_scores.json"):
    with open("user_scores.json", "w") as f:
        json.dump({}, f)
try:
    with open("user_scores.json", "r") as f:
        user_scores = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    user_scores = {}

# Dictionary to store chat-specific data
chat_data = {}

# Function to generate a random math question
def generate_question():
    operators = ["+", "-", "*", "/"]
    op = random.choice(operators)
    if op == '*':
        a = random.randint(1, 20)
        b = random.randint(1, 20)
    elif op == '+':
        a = random.randint(100, 1000)
        b = random.randint(100, 1000)
    elif op == '-':
        a = random.randint(100, 1000)
        b = random.randint(1, 1000)
    elif op == "/":
        a = random.randint(1, 100)
        b = random.randint(1, 20)
        while a % b != 0:
            a = random.randint(1, 100)
    question = f"{a} {op} {b}"
    answer = eval(question)
    if isinstance(answer, float) and answer.is_integer():
        answer = int(answer)
    return question, str(answer)

# Function to update user score
def update_user_score(user_id, score):
    user_scores[user_id] = score
    with open("user_scores.json", "w") as f:
        json.dump(user_scores, f)

# Function to get top scorers with indexing
def get_top_scorers(count=3):
    sorted_scores = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)
    top_scorers = []
    for index, (user_id, score) in enumerate(sorted_scores[:count], start=1):  # Start counting from 1
        user_info = vk.users.get(user_ids=user_id, fields="first_name,last_name")
        user_name = f"{user_info[0]['first_name']} {user_info[0]['last_name']}"
        top_scorers.append(f"{index}) {user_name} :- {score}")  # Include the index in the formatted string
    return top_scorers


# Function to initialize chat-specific data
def init_chat_data(chat_id):
    chat_data[chat_id] = {
        "message_count": 0,
        "user_ids": set(),
        "current_answer": None,
        "question_asked": False,
        "unique_users": set(),
        "remaining_messages": 20  # Add this line
    }

# Main loop
while True:
    try:
        for event in longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                chat_id = event.obj.message["peer_id"]
                user_id = event.obj.message["from_id"]
                message_text = event.obj.message["text"].lower()

                if chat_id not in chat_data:
                    init_chat_data(chat_id)

                chat_data_for_chat = chat_data[chat_id]
                chat_data_for_chat["user_ids"].add(user_id)
                chat_data_for_chat["unique_users"].add(user_id)

                if len(chat_data_for_chat["unique_users"]) > 1:
                    chat_data_for_chat["message_count"] += 1
                    chat_data_for_chat["remaining_messages"] -= 1

                if message_text == "/lp":
                    vk.messages.send(peer_id=chat_id, message=f'⚙ Ссылка на бот пользователя longpoll\nhttps://vk.com/@-208528832-idfc-lp-commands', random_id=random.randint(0, 2**64))

                if message_text in ['/help', 'помощь']:
                    user_info = vk.users.get(user_ids=user_id, fields="first_name,last_name")[0]
                    user_name = f" {user_info['first_name']} {user_info['last_name']} "
                    vk.messages.send(peer_id=chat_id, message=f'Дорогой {user_name}, напишите «/commands» или «/команды» для получения дополнительной информации', random_id=random.randint(0, 2**64))

                if message_text in ['/commands', 'cmd', '/команды', '/кмд']:
                    vk.messages.send(peer_id=chat_id, message=f'⚙ Полный список команд доступен по ссылке\nhttps://vk.com/@-208528832-idfc-bot-matematicheskaya-igra', random_id=random.randint(0, 2**64))
                if message_text in ['/link', '/ссылка']:
                    vk.messages.send(peer_id=chat_id, message=f'https://vk.com/public208528832', random_id=random.randint(0, 2**64))

                if message_text in ['/myrecords', '/мойрекорд', '/мр']:
                    user_info = vk.users.get(user_ids=user_id, fields="first_name,last_name")[0]
                    user_name = f"{user_info['first_name']} {user_info['last_name']}"
                    score = user_scores.get(str(user_id), 0)
                    score_message = f"{user_name}, ваша оценка: {score}." if score else f"{user_name}, вы еще не решили ни одного вопроса."
                    vk.messages.send(peer_id=chat_id, message=score_message, random_id=random.randint(0, 2**64))

                if message_text.startswith("/globaltop") or message_text.startswith("/глобалтоп") or message_text.startswith("/гт"):
                    try:
                        count = int(message_text.split()[1])
                    except (IndexError, ValueError):
                        count = 3
                    top_scorers_message = "Топ бомбардиры 🥇:\n" + "\n".join(get_top_scorers(count))
                    vk.messages.send(peer_id=chat_id, message=top_scorers_message, random_id=random.randint(0, 2**64))

                if message_text in ['/матх', '/math', '/пример']:
                    if chat_data_for_chat["question_asked"]:
                        vk.messages.send(peer_id=chat_id, message=f"Текущий вопрос: {question}", random_id=random.randint(0, 2**64))
                    else:
                        vk.messages.send(peer_id=chat_id, message=f"Математический вопрос придет после {chat_data_for_chat['remaining_messages']} сообщений.", random_id=random.randint(0, 2**64))

                if len(chat_data_for_chat["user_ids"]) > 1 and not chat_data_for_chat["question_asked"] and chat_data_for_chat["remaining_messages"] <= 0:
                    question, answer = generate_question()
                    chat_data_for_chat["current_answer"] = answer
                    vk.messages.send(peer_id=chat_id, message=f"Решите числовой вопрос: {question}", random_id=random.randint(0, 2**64))
                    chat_data_for_chat["question_asked"] = True
                    chat_data_for_chat["remaining_messages"] = 20  # Reset the remaining messages count

                if chat_data_for_chat["current_answer"] is not None and message_text == chat_data_for_chat["current_answer"]:
                    user_info = vk.users.get(user_ids=user_id, fields="first_name,last_name")[0]
                    user_name = f"{user_info['first_name']} {user_info['last_name']}"
                    score = user_scores.get(str(user_id), 0) + 1
                    update_user_score(str(user_id), score)
                    vk.messages.send(peer_id=chat_id, message=f"Правильный ответ, {user_name}! Ваша оценка теперь {score}.", random_id=random.randint(0, 2**64))
                    chat_data_for_chat["current_answer"] = None
                    chat_data_for_chat["question_asked"] = False
                    chat_data_for_chat["message_count"] = 0  # Reset the message count after a correct answer

            elif event.type == VkBotEventType.GROUP_MEMBER_IN:
                if event.obj.member_id == 208528832:  # You need to know your bot's user ID
                    chat_id = event.obj.peer_id
                    init_chat_data(chat_id)
                    vk.messages.send(
                        peer_id=chat_id,
                        message="Привет! Для списка команд напишите /help.",
                        random_id=random.randint(0, 2**64)
                    )

    except Exception as e:
        print(f"An error occurred: {e}")
        time.sleep(5)  # Wait for 5 seconds before retrying