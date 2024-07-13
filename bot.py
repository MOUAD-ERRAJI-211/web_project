import sqlite3
import telegram
from typing import Final
from telegram.constants import ParseMode
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
import random
import re
import requests
import threading
import time
import asyncio
from telegram import Bot
import collections

# declarations

global name
global a
regex_name = r'^[\w_]+$'
TOKEN: Final = '6598226031:AAE_9SDgz5miIWU3kJXrWzVJkQxcF1oavBQ'
BOT_USERNAME: Final = '@Absence_aer_bot'
TEACHER_ID: Final = 642372854
PASSWORD: Final = '457457'
END_OPERATION: Final = 'end_operation'
bot_open = True

# chosen number
def choose_number():
    number = random.randint(1, 100)
    return number

def generate_choices(a):
    choices = [a] + [random.randint(1, 100) for _ in range(5)]
    random.shuffle(choices)
    return choices

# database functions

def init_db():
    conn = sqlite3.connect('student_records.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS GI
                 (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                  NAME TEXT NOT NULL,
                  NB_ABSENCE INTEGER DEFAULT 0,
                  NB_CHEAT_ATTEMPT INTEGER DEFAULT 0,
                  POINTS INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS IDSD
                 (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                  NAME TEXT NOT NULL,
                  NB_ABSENCE INTEGER DEFAULT 0,
                  NB_CHEAT_ATTEMPT INTEGER DEFAULT 0,
                  POINTS INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

init_db()
student_records_conn = sqlite3.connect('student_records.db')
student_records_cursor = student_records_conn.cursor()

def update_student_record(table_name: str, name: str, increment_absence: bool, increment_cheat: bool, decrement_absence: bool = False):
    conn = student_records_conn
    c = conn.cursor()

    if increment_absence:
        c.execute(f"UPDATE {table_name} SET NB_ABSENCE = NB_ABSENCE + 1 WHERE NAME = ?", (name,))

    if increment_cheat:
        c.execute(f"UPDATE {table_name} SET NB_CHEAT_ATTEMPT = NB_CHEAT_ATTEMPT + 1, NB_ABSENCE = NB_ABSENCE + 1 WHERE NAME = ?", (name,))

    if decrement_absence:
        c.execute(f"UPDATE {table_name} SET NB_ABSENCE = NB_ABSENCE - 1 WHERE NAME = ?", (name,))

    conn.commit()

def insert_student(table_name: str, name: str, chat_id: int):
    conn = student_records_conn
    c = conn.cursor()
    c.execute(f"INSERT INTO {table_name} (NAME, ID) VALUES (?, ?)", (name, chat_id))
    conn.commit()

def get_name_from_id(chat_id: int, table_name: str) -> str:
    if table_name:
        conn = student_records_conn
        c = conn.cursor()
        c.execute(f"SELECT NAME FROM {table_name} WHERE ID = ?", (chat_id,))
        result = c.fetchone()
        return result[0] if result else None
    else:
        return None

# after session functions

async def show_next_student(query, context, filiere):
    present_students = context.user_data.get('present_students', [])

    if present_students:
        student_name = present_students.pop(0)[0]

        keyboard = [[InlineKeyboardButton("Ignore", callback_data='ignore')],
                    [InlineKeyboardButton("Absent", callback_data=f'absent_{student_name}')],
                    [InlineKeyboardButton("End Operation", callback_data=END_OPERATION)]]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=f"Next student: {student_name}", reply_markup=reply_markup)
        context.user_data['current_student'] = student_name
        context.user_data['present_students'] = present_students
    else:
        await query.edit_message_text(text="No more present students")

async def show_next_absent_student(query, context, filiere):
    absent_students = context.user_data.get('absent_students', [])

    if absent_students:
        student_name = absent_students.pop(0)[0]

        keyboard = [[InlineKeyboardButton("Ignore", callback_data='ignore')],
                    [InlineKeyboardButton("Present", callback_data=f'present_{student_name}')],
                    [InlineKeyboardButton("End Operation", callback_data=END_OPERATION)]]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=f"Next absent student: {student_name}", reply_markup=reply_markup)
        context.user_data['current_student'] = student_name
        context.user_data['absent_students'] = absent_students
    else:
        await query.edit_message_text(text="No more absent students.")

async def start_absent_confirmation(query, context):
    conn = sqlite3.connect('student_records.db')
    c = conn.cursor()

    c.execute(f"SELECT NAME, NB_ABSENCE FROM GI WHERE NB_ABSENCE > 0 ORDER BY NAME")
    absent_students_gi = c.fetchall()
    c.execute(f"SELECT NAME, NB_ABSENCE FROM IDSD WHERE NB_ABSENCE > 0 ORDER BY NAME")
    absent_students_idsd = c.fetchall()

    absent_students = absent_students_gi + absent_students_idsd

    if absent_students:
        absent_student_names = "\n".join([f"{name} ({nb_absence} absences)" for name, nb_absence in absent_students])
        await query.edit_message_text(text=f"Absent students:\n{absent_student_names}")
    else:
        await query.edit_message_text(text="No absent students found.")

    conn.close()

# commands

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global a
    chat_id = update.effective_chat.id
    conn = student_records_conn
    c = conn.cursor()

    if bot_open:
        if chat_id == TEACHER_ID:
            a = choose_number()
            context.user_data['chosen_number'] = a  
            await update.message.reply_text(f'The chosen number is: {a}')
        else:
            filiere = context.user_data.get('filiere')  
            c.execute("SELECT NAME FROM GI WHERE ID = ?", (chat_id,))
            result_gi = c.fetchone()
            c.execute("SELECT NAME FROM IDSD WHERE ID = ?", (chat_id,))
            result_idsd = c.fetchone()

            if result_gi or result_idsd:
                name = result_gi[0] if result_gi else result_idsd[0]
                keyboard = [[InlineKeyboardButton("Present", callback_data='present')],
                            [InlineKeyboardButton("Absent", callback_data='absent')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(f'Hello {name}, are you present or absent?', reply_markup=reply_markup)
            else:
                keyboard = [[InlineKeyboardButton("GI", callback_data='GI')],
                            [InlineKeyboardButton("IDSD", callback_data='IDSD')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text('Please choose your filiere:', reply_markup=reply_markup)
                context.user_data['waiting_for_filiere'] = True
    else:
        await update.message.reply_text('Bot is currently closed.')

async def show_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = student_records_conn
    c = conn.cursor()
    chat_id = update.effective_chat.id
    chat_message = update.effective_message.text.split()

    filiere = context.user_data.get('filiere', 'GI')

    if filiere:
        is_teacher = chat_id == TEACHER_ID  
        if is_teacher:
            c.execute(f"SELECT NAME FROM {filiere} ORDER BY NAME")
            students = c.fetchall()
            if students:
                student_names = "\n".join([student[0] for student in students])
                output = f"Students in {filiere}:\n{student_names}"
                await update.effective_message.reply_text(output)
            else:
                await update.effective_message.reply_text(f"No students found in {filiere}.")
        else:
            name = get_name_from_id(chat_id, filiere)
            if name:
                c.execute(f"SELECT NB_ABSENCE, NB_CHEAT_ATTEMPT, POINTS FROM {filiere} WHERE NAME = ?", (name,))
                result = c.fetchone()
                if result:
                    nb_absence, nb_cheat_attempt, points = result
                    output = f"Name: {name}\nfiliere: {filiere}\nNumber of Absences: {nb_absence}\nNumber of Cheat Attempts: {nb_cheat_attempt}\nPoints: {points}"
                    await update.effective_message.reply_text(output)
                else:
                    await update.effective_message.reply_text("No record found for you.")
            else:
                await update.effective_message.reply_text("Please enter your name first.")
    else:
        await update.effective_message.reply_text("Please choose your filiere first.")


async def delete_database_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('student_records.db')
    c = conn.cursor()

    c.execute("DELETE FROM GI")
    c.execute("DELETE FROM IDSD")

    conn.commit()
    conn.close()
    await update.message.reply_text("All student records have been deleted from both tables.")

def close_bot_after_time(delay, token, teacher_id, context):
    conn = sqlite3.connect('student_records.db')
    c = conn.cursor()
    time.sleep(delay)
    global bot_open
    bot_open = False
    print("Bot has been closed automatically.")

    c.execute(f"SELECT NAME FROM GI WHERE NB_ABSENCE = 0 ORDER BY NAME")
    present_students_gi = c.fetchall()
    c.execute(f"SELECT NAME FROM GI WHERE NB_ABSENCE > 0 ORDER BY NAME")
    absent_students_gi = c.fetchall()

    if present_students_gi or absent_students_gi:
        keyboard = [[InlineKeyboardButton("Check Presents", callback_data='check_presents')],
                    [InlineKeyboardButton("Check Absents", callback_data='check_absents')],
                    [InlineKeyboardButton("Confirm", callback_data='confirm')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        bot = Bot(TOKEN)
        asyncio.run(bot.send_message(chat_id=TEACHER_ID, text=f"Total present students: {len(present_students_gi)}\nTotal absent students: {len(absent_students_gi)}", reply_markup=reply_markup))
        loop.close()
    else:
        print("No present or absent students found.")


async def open_bot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id == TEACHER_ID:
        global bot_open
        bot_open = True
        await update.message.reply_text('Bot is now open.')

        close_thread = threading.Thread(target=close_bot_after_time, args=(5, TOKEN, TEACHER_ID, context))
        close_thread.start()
    else:
        await update.message.reply_text('You are not authorized to open the bot.')

# user bot interaction functions

def handle_response(text: str) -> str:
    processed = text.lower()

    if re.match(regex_name, processed) and processed != 'present' and processed != 'absent':
        global name
        name = text.strip()
        keyboard = [[InlineKeyboardButton("Present", callback_data='present')],
                    [InlineKeyboardButton("Absent", callback_data='absent')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        return 'Are you present or absent?', reply_markup

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('waiting_for_name'):
        name = update.message.text
        chat_id = update.effective_chat.id
        filiere = context.user_data['filiere']
        insert_student(filiere, name, chat_id)
        context.user_data['waiting_for_name'] = False
        keyboard = [[InlineKeyboardButton("Present", callback_data='present')],
                    [InlineKeyboardButton("Absent", callback_data='absent')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f'Hello {name}, are you present or absent?', reply_markup=reply_markup)

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = update.effective_chat.id
    await query.answer()
    global a

    if chat_id == TEACHER_ID:
        if query.data == 'confirm':
            await query.edit_message_text(text="Operation confirmed and ended.")
            context.user_data.clear()


        elif query.data == 'check_presents':
            filiere = context.user_data.get('filiere', 'GI')
            conn = sqlite3.connect('student_records.db')
            c = conn.cursor()
            c.execute(f"SELECT NAME FROM {filiere} WHERE NB_ABSENCE = 0 ORDER BY NAME")
            present_students = c.fetchall()
            conn.close()
            context.user_data['present_students'] = present_students
            await show_next_student(query, context, filiere)

        elif query.data == 'check_absents':
             filiere = context.user_data.get('filiere', 'GI')
             conn = sqlite3.connect('student_records.db')
             c = conn.cursor()
             c.execute(f"SELECT NAME FROM {filiere} WHERE NB_ABSENCE > 0 ORDER BY NAME")
             absent_students = c.fetchall()
             conn.close()
             context.user_data['absent_students'] = absent_students
             await show_next_absent_student(query, context, filiere)

        elif query.data.startswith('absent_'):
            student_name = query.data.split('_')[1]
            filiere = context.user_data.get('filiere', 'GI')
            update_student_record(filiere, student_name, increment_absence=True, increment_cheat=False)
            await query.answer(text=f"{student_name} marked as absent.")
            await show_next_student(query, context, filiere)

        elif query.data.startswith('present_'):
            student_name = query.data.split('_')[1]
            filiere = context.user_data.get('filiere', 'GI')
            update_student_record(filiere, student_name, increment_absence=False, increment_cheat=False, decrement_absence=True)
            await query.answer(text=f"{student_name} marked as present.")
            await show_next_absent_student(query, context, filiere)

        elif query.data == 'ignore':
            filiere = context.user_data.get('filiere', 'GI')
            await show_next_student(query, context, filiere)

        elif query.data == END_OPERATION:
            await query.edit_message_text(text="Operation ended.")
            context.user_data.clear()

    elif query.data == 'GI' or query.data == 'IDSD':
        context.user_data['filiere'] = query.data
        await query.edit_message_text('Please enter your name:')
        context.user_data['waiting_for_name'] = True

    elif query.data == 'present':
        filiere = context.user_data.get('filiere', 'GI')
        name = get_name_from_id(chat_id, filiere)
        choices = generate_choices(a)
        context.user_data['choices'] = choices
        keyboard = [[InlineKeyboardButton(str(choice), callback_data=str(choice))] for choice in choices]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text='Choose the number:', reply_markup=reply_markup)
        context.user_data.setdefault('present_students', {}).update({chat_id: filiere})



    elif query.data == 'absent':
        filiere = context.user_data.get('filiere', 'GI')
        name = get_name_from_id(chat_id, filiere)
        update_student_record(filiere, name, increment_absence=True, increment_cheat=False)
        await query.edit_message_text(text='You are marked as absent.')
        context.user_data.setdefault('absent_students', {}).update({chat_id: filiere})



    elif query.data in [str(choice) for choice in context.user_data.get('choices', [])]:
        if query.data == str(a):
            filiere = context.user_data.get('filiere', 'GI')
            name = get_name_from_id(chat_id, filiere)
            update_student_record(filiere, name, increment_absence=False, increment_cheat=False)
            await query.edit_message_text(text='Number Correct, you are marked as present.')
        else:
            filiere = context.user_data.get('filiere', 'GI')
            name = get_name_from_id(chat_id, filiere)
            update_student_record(filiere, name, increment_absence=False, increment_cheat=True)
            data = {'filiere': filiere, 'name': name, 'increment_absence': True, 'increment_cheat': True, 'decrement_absence': False}
            await query.edit_message_text(text='Number Incorrect, you are marked as absent.')


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')



if __name__ == '__main__':
    print('12')

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('show', show_command))
    app.add_handler(CommandHandler('delete', delete_database_command))
    app.add_handler(CommandHandler('open', open_bot_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback_query))


    app.add_error_handler(error)

    print(regex_name)
    app.run_polling(poll_interval=3)

    student_records_conn.close()












