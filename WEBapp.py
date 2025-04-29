#from WebAppBot import (update_approvers_keyboard, get_all_users)
from flask import Flask, render_template,session, request, redirect, url_for, jsonify, send_file
from config import CHAT_TOKEN, EMPLOYEE_IDS, BOT_TOKEN, USER_CHAT_ID_MAPPING #данные из config
import telebot, random, os, logging
from telebot import types, TeleBot

app = Flask(__name__)
app.secret_key = os.urandom(24)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

bot = telebot.TeleBot(BOT_TOKEN)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
INSTRUCTION_FOLDER ='instructions'
app.config['INSTRUCTIONS_FOLDER']=INSTRUCTION_FOLDER

approval_status = {}
initiators_messages = {}
current_sogl = ""

def handle_done(chat_id, selected_approvers, sogl, sender_name="Unknown User"):
    global approval_status
    global initiators_messages
    global current_sogl
    current_sogl = sogl
    if selected_approvers:  # Check if the list is not empty
        # Create a dictionary for approver statuses
        approval_status[chat_id] = {
            approver: "⏳ Ожидает согласования" for approver in selected_approvers
        }

        approvers_status_list = '\n'.join(
            [f"{approver}: {approval_status[chat_id][approver]}" for approver in selected_approvers]
        )

        # Send message to initiator - change to chat_token
        logging.debug(f"Sending message to group chat ID: {CHAT_TOKEN}")
        try:
            sent_message = bot.send_message(
                CHAT_TOKEN,
                f"Новая заявка от {sender_name}: '{sogl}'.\nСтатусы согласантов:\n{approvers_status_list}\nВаш выбор отправлен согласующим. Спасибо!",
            )
            if chat_id not in initiators_messages:
                initiators_messages[chat_id] = {}
            initiators_messages[chat_id]['message_id'] = sent_message.message_id

        except Exception as e:
            logging.error(f"Error sending message to group chat: {e}")
        approver_found = False
        # Send messages to approvers with buttons
        for approver_id_str in selected_approvers:
            if approver_id_str in EMPLOYEE_IDS:
                for user_id, username in EMPLOYEE_IDS.items():
                    if username == approver_id_str:
                        if user_id in USER_CHAT_ID_MAPPING:
                            approver_chat_id = USER_CHAT_ID_MAPPING[user_id]
                            logging.debug(f"Sending message to approver chat ID: {approver_chat_id}")  # Log approver chat ID
                            markup = types.InlineKeyboardMarkup()
                            approve_button = types.InlineKeyboardButton(
                                "Согласовано ✅", callback_data=f"approve:{chat_id}:{approver_id_str}"
                            )
                            reject_button = types.InlineKeyboardButton(
                                "Отклонить ❌", callback_data=f"reject:{chat_id}:{approver_id_str}"
                            )
                            markup.add(approve_button, reject_button)
                            try:
                                bot.send_message(
                                    approver_chat_id,
                                    f"Вам пришёл запрос на согласование от {sender_name}\n\nСогласование: '{sogl}'",
                                    reply_markup=markup,
                                )
                            except Exception as e:
                                logging.error(f"Error sending message to user chat: {e}")

                            approver_found = True
                            break
        if not approver_found:
            try:
                bot.send_message(CHAT_TOKEN, "Вы не выбрали согласователей")
            except Exception as e:
                logging.error(f"Error sending message to chat with no approvers selected: {e}")

    else:
        try:
            bot.send_message(CHAT_TOKEN, "Вы не выбрали согласователей")
        except Exception as e:
            logging.error(f"Error sending message to chat with no approvers: {e}")

#пытался изменять сообщение "ожидает статуса"
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve") or call.data.startswith("reject"))
def handle_approval_decision(call):
    global initiators_messages
    global approval_status
    global current_sogl
    logging.debug(f"Received callback query: {call.data}")

    # Parse data from callback
    data = call.data.split(":")
    action = data[0]  # approve/reject
    initiator_chat_id = str(data[1])  # ID of the initiator
    approver_name = data[2]  # Name of the approver

    # Update approver status
    new_status = "✅ Согласовано" if action == "approve" else "❌ Отклонено"
    if initiator_chat_id in approval_status and approver_name in approval_status[initiator_chat_id]:
         approval_status[initiator_chat_id][approver_name] = new_status
    else:
        logging.error(f"Error: could not find initiator {initiator_chat_id} or approver {approver_name} in the approval status")

    # Update Message for Approver
    try:
      bot.edit_message_text(
          f"Ваш статус в '{current_sogl}': {new_status}",
          call.message.chat.id,
          call.message.message_id
      )
      bot.answer_callback_query(call.id, f"Статус изменен на: {new_status}")
    except Exception as e:
        logging.error(f"Error when editing message for approver: {e}")

    # Generate the updated status message
    if initiator_chat_id in approval_status:
      status_message = "\n".join([
          f"{name}: {status}" for name, status in approval_status[initiator_chat_id].items()
      ])
      # Edit message with the new status
      try:
        if initiator_chat_id in initiators_messages:
           bot.edit_message_text(
              chat_id=CHAT_TOKEN,
              message_id=initiators_messages[initiator_chat_id]['message_id'],
              text=f"Новая заявка от: {current_sogl}.\nСтатусы согласантов:\n{status_message}"
            )
      except Exception as e:
           logging.error(f"Error when editing the message for the group: {e}")
    else:
      logging.error(f"Error could not find initiator {initiator_chat_id} in the approval status")


def get_pdf_list():
    """Get a list of PDF files from the pdf folder."""
    pdf_files = []
    if not os.path.exists(app.config['UPLOAD_FOLDER']): # create folder if does not exist
         os.makedirs(app.config['UPLOAD_FOLDER'])
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
         if filename.lower().endswith('.pdf'):
             pdf_files.append(filename)
    return pdf_files

def get_instructions():
    """Get a list of PDF files from PDF folder."""
    pdf_files = []
    if not os.path.exists(app.config['INSTRUCTIONS_FOLDER']):
        os.makedirs(app.config['INSTRUCTIONS_FOLDER'])
    for filename in os.listdir(app.config['INSTRUCTIONS_FOLDER']):
        if filename.lower().endswith('.pdf'):
            pdf_files.append(filename)
    return pdf_files

@app.route("/", methods = ["GET"])
def index():
    return render_template("index.html")

@app.route("/create_request")
def create_request():
    return render_template("create_request.html")


@app.route("/create_request/<obr>", methods=["GET", "POST"], endpoint="create_request_route")
def create_request(obr):
    if request.method == "POST":
        selected_approvers = request.form.getlist("approvers")
        chat_id = session.get('chat_id', random.randint(100000000, 999999999))  # Get the chat id, or create a new one
        sender_name = request.form.get('sender_name', "Unknown User")
        handle_done(chat_id, selected_approvers, obr, sender_name)
        session['chat_id'] = None
        return redirect(url_for("success"))
    return render_template("choose_approvers.html", approvers=EMPLOYEE_IDS, obr=obr)

@app.route("/access_approval", methods = ["GET"])
def access_approval():
    return render_template("access_approval.html")

@app.route("/access_approval/<sogl>", methods=["GET", "POST"])
def choose_approvers(sogl):
    if request.method == "POST":
        selected_approvers = request.form.getlist("approvers")
        chat_id = session.get('chat_id', random.randint(100000000, 999999999))  # Get the chat id, or create a new one
        sender_name = request.form.get('sender_name', "Unknown User")
        handle_done(chat_id, selected_approvers, sogl, sender_name)
        session['chat_id'] = None
        return redirect(url_for("success"))
    return render_template("choose_approvers.html", approvers=EMPLOYEE_IDS, sogl=sogl)

@app.route("/instructions")
def instructions():
    """Show a list of available PDF files."""
    instruction_files = get_instructions()
    return render_template('instructions.html', instruction_files=instruction_files)


@app.route("/instructions/<filename>", methods=["GET", "POST"], endpoint="instructions_open")
def instructions_open(filename):
    """Allow users to download a specific PDF file."""
    pdf_path = os.path.join(app.config['INSTRUCTIONS_FOLDER'], filename)

    if not os.path.exists(pdf_path):  # Check if file exists in the file system
        os.abort(404)
    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=filename
    )
@app.route("/media_resources")
def media_resources():
    """Show a list of available PDF files."""
    pdf_files = get_pdf_list()
    return render_template("media_resources.html", pdf_files=pdf_files)

@app.route("/media_resources/<filename>", methods=["GET", "POST"], endpoint="media_download")
def choose_approvers(filename):
    """Allow users to download a specific PDF file."""
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(pdf_path):  # Check if file exists in the file system
        os.abort(404)
    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=filename
    )
@app.route('/')
def home():
    return render_template("index.html")

@app.route("/feedback")
def feedback():
    return render_template("feedback.html")

@app.route("/success")
def success():
    return render_template("success.html")

@app.route("/Time")
def Time():
    return render_template("Time.html")

@app.route("/Opisanie_Peoblem")
def Opisanie_Peoblem():
    return render_template("Opisanie_Peoblem.html")

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
