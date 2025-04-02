#рабочий бот
import telebot
from telebot import types
from config import API_TOKEN, CHAT_ID #Должны бить в конфиге

IT_DEPARTAMENT_TOKEN = ''
bot = telebot.TeleBot(API_TOKEN)

waiting_for_message = {}
sogl_type = {}
selected_approvers = {}
approver_statuses = {}
approval_status = {}
initiators_messages = {}

approval_messages = {}

MAIN_BUTTON = "Согласование"
SOGL_TECH = "🛠️ Согласование техники"
SOGL_NET_FOLDER = "📁 Согласование доступов к сетевой папке"
SOGL_ECP = "Согласование доступов к ЭЦП"
BUTTON_BACK = "↩️ Вернуться назад"
BUTTON_DONE = "Готово"
BUTTON_START_WORK = "🚀 Начать работы"
Web_Prilojenie = 'Веб-приложение'
Web_app_open = 'Открыть веб-приложение'

# Наши согласанты
employees = ["Иванов", "Гаджин", "Торогов", "Панов"]

# ID согласантов
employee_ids = {"Иванов": 1076447694, "Гаджин": 1912799360, "Панов": 797809533}

def generate_status_message(sogl, statuses):
    status_lines = [f"{approver} - {status}" for approver, status in statuses.items()]
    return f"Ваше согласование: '{sogl}'.\nСтатусы согласантов:\n{'\n'.join(status_lines)}"

def create_approval_buttons():
    markup = types.InlineKeyboardMarkup()
    approve_button = types.InlineKeyboardButton("Согласовано ✅", callback_data="approved")
    reject_button = types.InlineKeyboardButton("Отклонить ❌", callback_data="rejected")
    markup.add(approve_button, reject_button)
    return markup

def update_approvers_keyboard(chat_id):
    # Проверяем, инициализирован ли словарь
    if chat_id not in selected_approvers:
        selected_approvers[chat_id] = []

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for employee in employees:
        if employee in selected_approvers.get(chat_id, []):
            markup.add(f"{employee} ✅")
        else:
            markup.add(employee)
    markup.add(BUTTON_DONE, BUTTON_BACK)  # Добавляем кнопки "Готово" и "Назад"
    # Отправляем обновлённую клавиатуру
    bot.send_message(chat_id, "Выберите согласантов (нажимайте для добавления/удаления):", reply_markup=markup)


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(MAIN_BUTTON)
    chat_id = message.chat.id
    bot.send_message(chat_id, "Какую функцию вы хотите выбрать?", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Согласовать")
def handle_approval_request(message):
    global initiators_messages  # Работаем с глобальной переменной
    chat_id = message.chat.id
    # Создаём фейковое согласование
    sogl = "Согласование примера"
    approvers = ['Иванов', 'Петров']  # Фейковый список согласантов
    # Сохраняем статусы согласантов
    approval_status[chat_id] = {approver: "⏳ Ожидает согласования" for approver in approvers}
    # Формируем статусы согласантов
    approvers_status_list = "\n".join([f"{approver}: {approval_status[chat_id][approver]}" for approver in approvers])
    # Отправляем сообщение инициатору
    sent_message = bot.send_message(
        chat_id, f"Ваше согласование: '{sogl}'.\nСтатусы согласантов:\n{approvers_status_list}"
    )
    # Сохраняем ID сообщения инициатора
    initiators_messages[chat_id] = {
        'message_id': sent_message.message_id
    }
    bot.send_message(chat_id, "Ваш запрос отправлен на согласование!")
@bot.message_handler(content_types=['text'])
def handler(message):
    chat_id = message.chat.id
    if message.text == MAIN_BUTTON:
        waiting_for_message[chat_id] = True
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(SOGL_TECH, SOGL_NET_FOLDER, SOGL_ECP)
        markup.row(BUTTON_BACK)
        bot.send_message(chat_id, "Выберете из предложенных вариантов или обратитесь в тех. поддержку",
                         reply_markup=markup)
    elif message.text == Web_Prilojenie:
        markup = types.InlineKeyboardMarkup()
        web_app_button = types.InlineKeyboardButton(text="Открыть веб-приложение",url="https://chatgptchatapp.com/" )
        markup.add(web_app_button)
        bot.send_message(chat_id, "Перейдите в приложение", reply_markup=markup)
    elif message.text == SOGL_TECH:
        waiting_for_message[chat_id] = True
        sogl_type[chat_id] = SOGL_TECH
        selected_approvers[chat_id] = []
        update_approvers_keyboard(chat_id)
    elif message.text == SOGL_NET_FOLDER:
        waiting_for_message[chat_id] = True
        sogl_type[chat_id] = SOGL_NET_FOLDER
        selected_approvers[chat_id] = []
        update_approvers_keyboard(chat_id)
    elif message.text == SOGL_ECP:
        waiting_for_message[chat_id] = True
        sogl_type[chat_id] = SOGL_ECP
        selected_approvers[chat_id] = []
        update_approvers_keyboard(chat_id)
    elif message.text in [employee + " ✅" for employee in employees]:
        employee_name = message.text.replace(" ✅", "")
        if chat_id in sogl_type:
            if employee_name in selected_approvers.get(chat_id, []):
                selected_approvers[chat_id].remove(employee_name)
                bot.send_message(chat_id, f"{employee_name} ❌ удалён из списка согласантов.")
            else:
                selected_approvers[chat_id].append(employee_name)
                bot.send_message(chat_id, f"{employee_name} ✅ добавлен в список согласантов.")
            update_approvers_keyboard(chat_id)
    elif message.text in employees:
        if chat_id in sogl_type:
            selected_approvers[chat_id].append(message.text)
            bot.send_message(chat_id, f"{message.text} ✅ добавлен в список согласантов.")
            update_approvers_keyboard(chat_id)

    elif message.text == BUTTON_DONE:
        if chat_id in selected_approvers and selected_approvers[chat_id]:
            sogl = sogl_type.get(chat_id, "Без названия")
            # Создаём словарь для статусов согласантов
            approval_status[chat_id] = {approver: "⏳ Ожидает согласования" for approver in selected_approvers[chat_id]}
            # Формируем строку со статусами согласантов
            approvers_status_list = '\n'.join(
                [f"{approver}: {approval_status[chat_id][approver]}" for approver in selected_approvers[chat_id]])
            # Отправляем сообщение инициатору и сохраняем ID для редактирования
            sent_message = bot.send_message(
                chat_id,
                f"Ваше согласование: '{sogl}'.\nСтатусы согласантов:\n{approvers_status_list}"
            )
            # Сохраняем ID сообщения инициатору
            if chat_id not in initiators_messages:
                initiators_messages[chat_id] = {}
            initiators_messages[chat_id]['message_id'] = sent_message.message_id
            bot.send_message(chat_id, 'Ваш выбор отправлен согласантам. Спасибо!')
            # Разослать сообщения согласантам с кнопками
            for approver in selected_approvers[chat_id]:
                if approver in employee_ids:  # Проверяем наличие ID согласанта
                    approver_id = employee_ids[approver]
                    # Создаём инлайн-кнопки
                    markup = types.InlineKeyboardMarkup()
                    approve_button = types.InlineKeyboardButton("Согласовано ✅",
                                                                callback_data=f"approve:{chat_id}:{approver}")
                    reject_button = types.InlineKeyboardButton("Отклонить ❌",
                                                               callback_data=f"reject:{chat_id}:{approver}")
                    markup.add(approve_button, reject_button)
                    # Отправляем сообщение согласанту
                    bot.send_message(
                        approver_id,
                        f"Вам пришёл запрос на согласование от "
                        f"{message.chat.first_name} @{message.chat.username}\n\nСогласование: '{sogl}'",
                        reply_markup=markup
                    )
        else:
            bot.send_message(chat_id, "Вы не выбрали согласантов.")
    elif message.text == BUTTON_BACK:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(MAIN_BUTTON)
        markup.row(Web_Prilojenie)
        bot.send_message(chat_id, "Вы вернулись в главное меню.", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == BUTTON_DONE)
def handle_done(message):
    chat_id = message.chat.id
    selected = selected_approvers.get(chat_id, [])
    if not selected:
        bot.send_message(chat_id, "Вы не выбрали согласантов.")
        return

    approval_status[chat_id] = {approver: "⏳ Ожидает согласования" for approver in selected}
    for approver in selected:
        if approver in employee_ids:
            approver_id = employee_ids[approver]
            bot.send_message(
                approver_id,
                f"Вам пришел запрос на согласование от пользователя {message.chat.first_name}.",
                reply_markup=create_approval_buttons()
            )

    status_message = generate_status_message("Ваше согласование", approval_status[chat_id])
    bot.send_message(chat_id, f"Согласование отправлено:\n\n{status_message}")
    bot.send_message(chat_id, "Ждём ответа от согласантов.", reply_markup=types.ReplyKeyboardRemove())


@bot.callback_query_handler(func=lambda call: call.data.startswith("approve") or call.data.startswith("reject"))
def handle_approval_decision(call):
    global initiators_messages  # Работаем с глобальной переменной

    # Распарсить данные из callback
    data = call.data.split(":")
    action = data[0]  # approve/reject
    initiator_chat_id = int(data[1])  # ID инициатора
    approver_name = data[2]  # Имя согласанта

    # Обновляем статус согласанта
    new_status = "✅ Согласовано"\
        if action == "approve"\
        else "❌ Отклонено"
    approval_status[initiator_chat_id][approver_name] = new_status

    # Формируем обновлённый статус
    status_message = "\n".join([
        f"{name}: {status}" for name, status in approval_status[initiator_chat_id].items()
    ])

    # Редактируем сообщение у инициатора
    if initiator_chat_id in initiators_messages:
        bot.edit_message_text(
            chat_id=initiator_chat_id,
            message_id=initiators_messages[initiator_chat_id]['message_id'],
            text=f"Ваше согласование: 'Согласование примера'.\nСтатусы согласантов:\n{status_message}")

if __name__ == '__main__':
   bot.polling(none_stop=True)