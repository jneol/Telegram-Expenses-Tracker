import logging
import telegram
import prettytable as pt
from telegram import Update, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext, ConversationHandler
from datetime import datetime, timedelta
import os
import csv
import pytz
import config

bot = telegram.Bot(token=config.telegram_token)

categories = 'Food', 'Transport', 'Groceries', 'Savings', 'Clothes', 'Entertain', 'Bills', 'Misc'

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

NEWDATE, NEWAMT, NEWFINAL = range(3)
DELETE2 = range(1)
REQACC2 = range(1)
AUTH1 = range(1)
IMPORT1 = range(1)
REVOKE1 = range(1)
RESET1 = range(1)

def auth_check(user_id):
    file = "subscribers.txt"
    try:
        with open(file, "r", newline="") as r:
            if str(user_id) in r.read():
                return True
            else:
                return False
    except IOError:
        open(file, "w").close
        auth_check(user_id)

def write_header(f, file_exists, headers):
    writer = csv.DictWriter(f, lineterminator='\r\n',fieldnames=headers)
    #if not file_exists:
    writer.writeheader()
    return

def help_command(update, context):
    update.message.reply_text('Please dm the creator should there be any bugs/suggestions!', parse_mode="HTML")
    
def reset(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(f"⚠ This action is not reversible!\nAre you sure you want to reset?\nType <b>CONFIRM</b> to reset. <i>(Case-sensitive)</i>", parse_mode="HTML", reply_markup=ForceReply(selective=True))
    return RESET1
    
def reset1(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    if text == "CONFIRM":
        user = update.effective_user
        bot.sendMessage(chat_id=update.message.chat.id,text="Records have been successfully reset.")
        file = str(user['id']) + ".csv"
        file_exists = os.path.isfile(file)
        with open(file, "w+", newline="") as f:
            headers = ['Date', 'Category', 'Amount', 'Description']
            write_header(f, file_exists, headers)
    else:
        bot.sendMessage(chat_id=update.message.chat.id,text="Records were not reset.")
    return -1

def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /newreminder is issued."""
    user = update.effective_user
    update.message.reply_markdown_v2(fr'Hi {user.mention_markdown_v2()} \! 👋')    
    if auth_check(user['id']) == True:
        bot.sendMessage(chat_id=update.message.chat.id,text="Your account is permitted to use the bot.")
        return -1
    else:
        bot.sendMessage(chat_id=update.message.chat.id,text='❌ You are not authorised to use the bot.')
        update.message.reply_text(f"⚠ Please type <b>req</b> to request access.", parse_mode="HTML", reply_markup=ForceReply(selective=True))
        return REQACC2

def reqacc2(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    if str(text).lower() == "req":
        bot.sendMessage(chat_id=update.message.chat.id,text="Request for access has been sent.\nYou will be notified when it has been granted.")
        user = update.effective_user
        bot.sendMessage(chat_id=config.admin_user_id, text="🚨 ADMIN PANEL 🚨\nUser: <b>@{}</b> has requested access:\nUser ID: {}\nFirst name: {}\nLast name: {}".format(str(user['username']),str(user['id']),str(user['first_name']),str(user['last_name'])), parse_mode="HTML")
        bot.sendMessage(chat_id=config.admin_user_id, text="{}".format(str(user['id'])), parse_mode="HTML")
        bot.sendMessage(chat_id=config.admin_user_id, text="Type /auth to authorise", parse_mode="HTML")
    else:
        bot.sendMessage(chat_id=update.message.chat.id,text="Please try again using /start")
    return -1

def auth(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(f"Please enter choice of User ID to authorise", reply_markup=ForceReply(selective=True))
    return AUTH1

def auth1(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    if user['id'] == config.admin_user_id:
        text = update.message.text
        file = "subscribers.txt"
        with open(file, "a+", newline="") as f:
            f.write(text+"\n")
        update.message.reply_text('✅ Access granted for User ID: {}'.format(text))
        bot.sendMessage(chat_id=int(text), text="✅ Request for access has been granted.")
    else:
        update.message.reply_text('❌ You are not permitted to use this command')
    return -1

def revoke(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    if user['id'] == config.admin_user_id:
        update.message.reply_text(f"Please enter choice of User ID to revoke", reply_markup=ForceReply(selective=True))
        file = "subscribers.txt"
        with open(file, "r", newline="") as r:
            for line in r:
                update.message.reply_text("{}".format(line))
        return REVOKE1
    else:
        update.message.reply_text('❌ You are not permitted to use this command')
    return -1

def revoke1(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    if user['id'] == config.admin_user_id:
        text = update.message.text
        file = "subscribers.txt"
        new_file = "subscribers1.txt"
        with open(file, "r", newline="") as r, open(new_file, "w+", newline="") as f:
            for line in r:
                if str(text) + "\n" in line:
                    pass
                else:
                    f.write(line)          
        os.remove(file)
        os.rename(new_file, file)                    
        update.message.reply_text('✅ Access revoked for User ID: {}'.format(text))
    else:
        update.message.reply_text('❌ You are not permitted to use this command')
    return -1

def import1(update: Update, context: CallbackContext) -> int:
    bot.sendMessage(chat_id=update.message.chat.id,text="Send a .csv file with the correct record formatting to replace the information that is currently on the cloud.")
    return IMPORT1

def import2(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    context.bot.get_file(update.message.document).download()
    with open(str(user['id']) + ".csv", 'wb') as f:
        context.bot.get_file(update.message.document).download(out=f)
    bot.sendMessage(chat_id=update.message.chat.id,text="Records successfully imported/replaced.")
    return -1

def delete1(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    if auth_check(user['id']) == True:
    
        user = update.message.from_user
        old_file = str(user['id']) + ".csv"
        
        table = pt.PrettyTable(['#', 'Date', 'Category', 'Amount'])
        table.align['#'] = 'l'
        table.align['Date'] = 'l'
        table.align['Category'] = 'r'
        table.align['Amount'] = 'r'
        
        table1 = pt.PrettyTable(['#', 'Date', 'Description'])
        table1.align['#'] = 'l'    
        table1.align['Date'] = 'l'
        table1.align['Description'] = 'r'
        
        data = []
        data1 = []    
        
        with open(old_file, "r", newline="\n") as r:
            r.readline() # read header
            crdr = csv.reader(r)
            try:
                filedata = sorted(crdr, key=lambda row: (datetime.strptime(row[0], "%d/%m/%Y")))
            except ValueError:
                bot.sendMessage(chat_id=update.message.chat.id,text="File contains invalid information. Use /debug to resolve.")
            i = 1
            for line in filedata:
                    data.append(tuple([i, datetime.strptime(line[0], "%d/%m/%Y").strftime("%d %b %y"), line[1], line[2]]))
                    data1.append(tuple([i, datetime.strptime(line[0], "%d/%m/%Y").strftime("%d %b %y"), line[3]]))
                    i += 1
            for no, date, category, amount in data:
                table.add_row([no, date, category, f'{float(amount):.2f}'])
            for no, date, desc in data1:
                table1.add_row([no, date, desc])
            if data != []:
                update.message.reply_text(f'<pre>{table}</pre>', parse_mode=ParseMode.HTML)
                update.message.reply_text(f'<pre>{table1}</pre>', parse_mode=ParseMode.HTML)
                update.message.reply_text(f"Please select a transaction to delete:", reply_markup=ForceReply(selective=True))
            else:
                 bot.sendMessage(chat_id=update.message.chat.id,text="No records found.")
            table.clear()
            table1.clear()
            data.clear()
            data1.clear()
        return DELETE2

    else:
        bot.sendMessage(chat_id=update.message.chat.id,text="❌ You are not permitted to use this command.")
    return -1

def delete2(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    user = update.message.from_user
    new_file = str(user['id']) + '_new.csv'
    old_file = str(user['id']) + '.csv'
    file_exists = os.path.isfile(new_file)
    try:
        with open(old_file, "r", newline="\n") as r:
            reader = csv.reader(r)
            r.readline() # read header
            lines = len(list(reader))
        if int(text)-1 in range(lines):            
            with open(new_file, "w+", newline="") as f, open(old_file, "r", newline="\n") as r:
                headers = ['Date', 'Category', 'Amount', 'Description']
                write_header(f, file_exists, headers)
                r.readline() # read header
                reader = csv.reader(r)
                filedata = sorted(reader, key=lambda row: (datetime.strptime(row[0], "%d/%m/%Y")))
                for i, row in enumerate(filedata):
                    if i == (int(text)-1):
                        print("Deleting in progress...")
                        # skip over this entry (to be deleted)
                    else:
                        csvwriter = csv.writer(f, quoting=csv.QUOTE_NONE)
                        entry = row[0], row[1], row[2], row[3]
                        csvwriter.writerow(entry)
            os.remove(old_file)
            os.rename(new_file, old_file)
            bot.sendMessage(chat_id=update.message.chat.id,text="Record successfully deleted.")        
            return -1
        else:
            bot.sendMessage(chat_id=update.message.chat.id,text="Invalid input. Please try again.")
        return -1                   
    except ValueError:
        bot.sendMessage(chat_id=update.message.chat.id,text="Invalid input. Please try again.")
        return -1       
    except IndexError:
        bot.sendMessage(chat_id=update.message.chat.id,text="Invalid input. Please try again.")
        return -1    
    return -1

def debug(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    new_file = str(user['id']) + '_new.csv'
    old_file = str(user['id']) + '.csv'
    file_exists = os.path.isfile(new_file)
    with open(new_file, "w+", newline="") as f, open(old_file, "r", newline="\n") as r:
        headers = ['Date', 'Category', 'Amount', 'Description']
        write_header(f, file_exists, headers)        
        r.readline() # read header
        crdr = csv.reader(r)
        for i, row in enumerate(crdr):
            try:
                datetime.strptime(row[0], "%d/%m/%Y")
                csvwriter = csv.writer(f, quoting=csv.QUOTE_NONE)
                entry = row[0], row[1], row[2], row[3]
                csvwriter.writerow(entry)                
            except:
                pass
    os.remove(old_file)
    os.rename(new_file, old_file)
    bot.sendMessage(chat_id=update.message.chat.id,text="Debug successful.")        
    return -1

def getrecords(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    if auth_check(user['id']) == True:    
    
        user = update.message.from_user
        file = str(user['id']) +".csv"
        try:
            bot.sendDocument(chat_id=update.message.chat.id, document=open(file, 'rb'))
            bot.sendMessage(chat_id=update.message.chat.id,text="Records downloaded successfully.")
        except:
            bot.sendMessage(chat_id=update.message.chat.id,text="No records found.")
        return -1

    else:
        bot.sendMessage(chat_id=update.message.chat.id,text="❌ You are not permitted to use this command.")
    return -1
        

def view_categories():
    keyboard = [
    [
        InlineKeyboardButton(text='Food', callback_data = 'view_food'),
        InlineKeyboardButton(text='Transport', callback_data = 'view_transport'),
    ],
    [
        InlineKeyboardButton(text='Groceries', callback_data = 'view_groceries'),
        InlineKeyboardButton(text='Savings', callback_data = 'view_savings'),
    ],
    [
        InlineKeyboardButton(text='Clothes', callback_data = 'view_clothes'),
        InlineKeyboardButton(text='Entertain', callback_data = 'view_entertain'),
    ],
    [
        InlineKeyboardButton(text='Bills', callback_data = 'view_bills'),
        InlineKeyboardButton(text='Misc', callback_data = 'view_misc'),
        InlineKeyboardButton(text='All', callback_data = 'all_cats'),
    ],
    ]
    markup = InlineKeyboardMarkup(keyboard, row_width=3, resize_keyboard=True)

    return markup

def view_months():
    keyboard = [
    [
        InlineKeyboardButton(text='Jan', callback_data = 'view_jan'),
        InlineKeyboardButton(text='Feb', callback_data = 'view_feb'),
        InlineKeyboardButton(text='Mar', callback_data = 'view_mar'),
        InlineKeyboardButton(text='Apr', callback_data = 'view_apr'),
    ],
    [
        InlineKeyboardButton(text='May', callback_data = 'view_may'),
        InlineKeyboardButton(text='Jun', callback_data = 'view_jun'),
        InlineKeyboardButton(text='Jul', callback_data = 'view_jul'),
        InlineKeyboardButton(text='Aug', callback_data = 'view_aug'),
    ],
    [
        InlineKeyboardButton(text='Sep', callback_data = 'view_sep'),
        InlineKeyboardButton(text='Oct', callback_data = 'view_oct'),
        InlineKeyboardButton(text='Nov', callback_data = 'view_nov'),
        InlineKeyboardButton(text='Dec', callback_data = 'view_dec'),
    ],
    [
        InlineKeyboardButton(text="All", callback_data = 'all_months'),
    ],    
    ]
    markup = InlineKeyboardMarkup(keyboard, row_width=3, resize_keyboard=True)

    return markup

def view_years():
    keyboard = [
    [
        InlineKeyboardButton(text='2017', callback_data = 'view_2017'),
        InlineKeyboardButton(text='2018', callback_data = 'view_2018'),
        InlineKeyboardButton(text='2019', callback_data = 'view_2019'),
    ],
    [
        InlineKeyboardButton(text='2020', callback_data = 'view_2020'),
        InlineKeyboardButton(text='2021', callback_data = 'view_2021'),
        InlineKeyboardButton(text='2022', callback_data = 'view_2022'),
    ],
    [
        InlineKeyboardButton(text="Today", callback_data = "view_today"),
    ],    
    [
        InlineKeyboardButton(text="All", callback_data = "all_years"),
    ],
    ]
    markup = InlineKeyboardMarkup(keyboard, row_width=3, resize_keyboard=True)

    return markup

def new_year():
    
    yesterday = str((datetime.now(pytz.timezone('Asia/Singapore'))-timedelta(days=1)).strftime("%d/%m/%Y"))
    twodaysago = str((datetime.now(pytz.timezone('Asia/Singapore'))-timedelta(days=2)).strftime("%d/%m/%Y"))
    threedaysago = str((datetime.now(pytz.timezone('Asia/Singapore'))-timedelta(days=3)).strftime("%d/%m/%Y"))
    fourdaysago = str((datetime.now(pytz.timezone('Asia/Singapore'))-timedelta(days=4)).strftime("%d/%m/%Y"))
    fivedaysago = str((datetime.now(pytz.timezone('Asia/Singapore'))-timedelta(days=5)).strftime("%d/%m/%Y"))
    sixdaysago = str((datetime.now(pytz.timezone('Asia/Singapore'))-timedelta(days=6)).strftime("%d/%m/%Y"))
    
    keyboard = [
    [
        InlineKeyboardButton(text="Today", callback_data = 'new_today'),
    ],
    [
        InlineKeyboardButton(text=yesterday, callback_data = 'new_yesterday'),
        InlineKeyboardButton(text=twodaysago, callback_data = 'new_twodaysago'),     
        InlineKeyboardButton(text=threedaysago, callback_data = 'new_threedaysago'),
    ],
    [
        InlineKeyboardButton(text=fourdaysago, callback_data = 'new_fourdaysago'),
        InlineKeyboardButton(text=fivedaysago, callback_data = 'new_fivedaysago'),
        InlineKeyboardButton(text=sixdaysago, callback_data = 'new_sixdaysago'),     
    ],
    [
        InlineKeyboardButton(text='Custom date', callback_data = 'new_customdate'),
    ],
    ]
    markup = InlineKeyboardMarkup(keyboard, row_width=3, resize_keyboard=True)

    return markup

def new_categories():
    keyboard = [
    [
        InlineKeyboardButton(text='Food', callback_data = 'new_food'),
        InlineKeyboardButton(text='Transport', callback_data = 'new_transport'),
    ],
    [
        InlineKeyboardButton(text='Groceries', callback_data = 'new_groceries'),
        InlineKeyboardButton(text='Savings', callback_data = 'new_savings'),
    ],
    [
        InlineKeyboardButton(text='Clothes', callback_data = 'new_clothes'),
        InlineKeyboardButton(text='Entertain', callback_data = 'new_entertain'),
    ],
    [
        InlineKeyboardButton(text='Bills', callback_data = 'new_bills'),
        InlineKeyboardButton(text='Misc', callback_data = 'new_misc'),
    ],
    ]
    markup = InlineKeyboardMarkup(keyboard, row_width=3, resize_keyboard=True)

    return markup

def viewtoday(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    if auth_check(user['id']) == True:
        
        date_today = str(datetime.now(pytz.timezone('Asia/Singapore')).strftime("%d/%m/%Y"))
        user = update.message.from_user
        file = str(user['id']) + ".csv"
        
        table = pt.PrettyTable(['Description', 'Category', 'Amount'])
        table.align['Category'] = 'r'
        table.align['Amount'] = 'r'
        table.align['Description'] = 'r'
        
        result = {}    

    try:
        with open(file, "r") as r:
            r.readline() # read header
            crdr = csv.reader(r, delimiter=',', quotechar='"')  
            for row in crdr:
                if row[0] in result:
                    result[row[0]].append((row[1], row[2], row[3]))
                else:
                    result[row[0]] = [(row[1], row[2], row[3])]
            print(result)
            try:
                filedata = sorted(crdr, key=lambda row: (datetime.strptime(row[0], "%d/%m/%Y")))
            except ValueError:
                bot.sendMessage(chat_id=update.message.chat.id,text="File contains invalid information. Use /debug to resolve.")
            i = 1
            total = 0


            for k, v in result.items():
                total = 0
            # Today, all categories         
                if str(datetime.now(pytz.timezone('Asia/Singapore')).strftime("%d/%m/%Y")) == str(k):
                    table.add_row(["==========","",""])
                    table.add_row([datetime.strptime(k, "%d/%m/%Y").strftime("%d %b %y"),"",""])
                    table.add_row(["==========","",""])
                    for category, amount, desc in v:                
                        table.add_row([desc, category, float(amount)])
                        total += float(amount)                              
                    table.add_row(["--","--","--"])
                    table.add_row(["","Total",total])
                    table.add_row(["","",""])

            if total != float(0):
                bot.sendMessage(chat_id=update.message.chat.id,text=f'<pre>{table}</pre>', parse_mode="HTML")
                #bot.sendMessage(chat_id=user,text="<b>Total: ${:.2f}</b>".format(total), parse_mode="HTML")        
            else:                   
                bot.sendMessage(chat_id=update.message.chat.id,text='No records found.', parse_mode="HTML")
            table.clear()
            result.clear()
            return -1
    except:      
        bot.sendMessage(chat_id=update.message.chat.id,text='No records found.', parse_mode="HTML")
        return -1
    else:
        bot.sendMessage(chat_id=update.message.chat.id,text="❌ You are not permitted to use this command.")
        return -1

def view(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    if auth_check(user['id']) == True:
        bot.sendMessage(update.message.chat.id,"Select a year:", reply_markup=view_years())
    else:
        bot.sendMessage(chat_id=update.message.chat.id,text="❌ You are not permitted to use this command.")
        return -1

def new(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    if auth_check(user['id']) == True:
        file = str(user['id']) + ".csv"
        file_exists = os.path.isfile(file)
        if file_exists == False:
            with open(file, "w+", newline="") as f:
                headers = ['Date', 'Category', 'Amount', 'Description']
                write_header(f, file_exists, headers)
            bot.sendMessage(update.message.chat.id,"Select date of new entry:", reply_markup=new_year())
        else:
            bot.sendMessage(update.message.chat.id,"Select date of new entry:", reply_markup=new_year())
    else:
        bot.sendMessage(chat_id=update.message.chat.id,text="❌ You are not permitted to use this command.")
        return -1

def view_filter(user):
    view_file = "view" + str(user) + ".txt"
    file = str(user) + ".csv"
    table = pt.PrettyTable(['Description', 'Category', 'Amount'])
    table.align['Category'] = 'r'
    table.align['Amount'] = 'r'
    table.align['Description'] = 'r'
    
    result = {}    

    try:
        with open(view_file, "r") as rf, open(file, "r") as r:
            r.readline() # read header
            crdr = csv.reader(r, delimiter=',', quotechar='"')  
            for row in crdr:
                if row[0] in result:
                    result[row[0]].append((row[1], row[2], row[3]))
                else:
                    result[row[0]] = [(row[1], row[2], row[3])]
            print(result)
            fr = rf.readlines()
            try:
                filedata = sorted(crdr, key=lambda row: (datetime.strptime(row[0], "%d/%m/%Y")))
            except ValueError:
                bot.sendMessage(chat_id=user,text="File contains invalid information. Use /debug to resolve.")
            i = 1
            total = 0
            selected_year = fr[0].rstrip("\n")
            print(selected_year)
            selected_month = fr[1].rstrip("\n")
            print(selected_month)
            selected_category = fr[2].rstrip("\n")
            print(selected_category)

            for k, v in result.items():
                total = 0
            # all years, all months, all categories        
                if "All" == str(selected_category):            
                    if "All" == str(selected_year):
                        if "All" == str(selected_month):
                            #table.add_row(["==========","",""])
                            table.add_row(["","",""])
                            table.add_row([datetime.strptime(k, "%d/%m/%Y").strftime("%d %b %y"),"",""])
                            table.add_row(["==","==","=="])
                            for category, amount, desc in v:                
                                table.add_row([desc, category, float(amount)])
                                total += float(amount)                    
                            #table.add_row(["--","--","--"])
                            #table.add_row(["","Total",total])
                            #table.add_row(["","",""])
                
            # specific year, all months, all categories
                if "All" == str(selected_category):            
                    if str(k[6:10]) == str(selected_year):
                        if "All" == str(selected_month):
                            table.add_row(["==========","",""])
                            table.add_row([datetime.strptime(k, "%d/%m/%Y").strftime("%d %b %y"),"",""])
                            table.add_row(["==========","",""])
                            for category, amount, desc in v:                   
                                table.add_row([desc, category, float(amount)])
                                total += float(amount)                    
                            table.add_row(["--","--","--"])
                            table.add_row(["","Total",total])
                            table.add_row(["","",""])
                    
            
            # specific year, specific month, all categories
                if "All" == str(selected_category):            
                    if str(k[6:10]) == str(selected_year):
                        if str(k[3:5]) == str(selected_month):
                            table.add_row(["==========","",""])
                            table.add_row([datetime.strptime(k, "%d/%m/%Y").strftime("%d %b %y"),"",""])
                            table.add_row(["==========","",""])
                            for category, amount, desc in v:                   
                                table.add_row([desc, category, float(amount)])
                                total += float(amount)                     
                            table.add_row(["--","--","--"])
                            table.add_row(["","Total",total])
                            table.add_row(["","",""])
            
            # specific year, specific month, specific category
                for category, amount, desc in v:
                    if str(category) == str(selected_category):                 
                        if str(k[6:10]) == str(selected_year):
                            if str(k[3:5]) == str(selected_month):
                                table.add_row(["==========","",""])
                                table.add_row([datetime.strptime(k, "%d/%m/%Y").strftime("%d %b %y"),"",""])
                                table.add_row(["==========","",""])
                                for category, amount, desc in v:
                                    if str(category) == str(selected_category):                    
                                        table.add_row([desc, category, float(amount)])
                                        total += float(amount)                        
                                table.add_row(["--","--","--"])
                                table.add_row(["","Total",total])
                                table.add_row(["","",""])    
                        
            # Today, all categories
                if "All" == str(selected_category):            
                    if str(datetime.now(pytz.timezone('Asia/Singapore')).strftime("%d/%m/%Y")) == str(selected_year):
                        if int(k[0:2]) == int(datetime.now(pytz.timezone('Asia/Singapore')).strftime("%d")):
                            if int(k[3:5]) == int(datetime.now(pytz.timezone('Asia/Singapore')).strftime("%m")):
                                table.add_row(["==========","",""])
                                table.add_row([datetime.strptime(k, "%d/%m/%Y").strftime("%d %b %y"),"",""])
                                table.add_row(["==========","",""])
                                for category, amount, desc in v:                
                                    table.add_row([desc, category, float(amount)])
                                    total += float(amount)                              
                                table.add_row(["--","--","--"])
                                table.add_row(["","Total",total])
                                table.add_row(["","",""])
             
                # Today, specific category
                for category, amount, desc in v:
                    if str(category) == str(selected_category):               
                        if str(datetime.now(pytz.timezone('Asia/Singapore')).strftime("%d/%m/%Y")) == str(selected_year):
                            if int(k[0:2]) == int(datetime.now(pytz.timezone('Asia/Singapore')).strftime("%d")):
                                if int(k[3:5]) == int(datetime.now(pytz.timezone('Asia/Singapore')).strftime("%m")):
                                    table.add_row(["==========","",""])
                                    table.add_row([datetime.strptime(k, "%d/%m/%Y").strftime("%d %b %y"),"",""])
                                    table.add_row(["==========","",""])
                                    for category, amount, desc in v:
                                        if str(category) == str(selected_category):                    
                                            table.add_row([desc, category, float(amount)])
                                            total += float(amount)                                 
                                    table.add_row(["--","--","--"])
                                    table.add_row(["","Total",total])
                                    table.add_row(["","",""])
            
            if total != float(0):
                bot.sendMessage(chat_id=user,text=f'<pre>{table}</pre>', parse_mode="HTML") 
            else:                   
                bot.sendMessage(chat_id=user,text='No records found.', parse_mode="HTML")
            table.clear()
            result.clear()
            return -1
    except:
        print("resultz:", result)        
        bot.sendMessage(chat_id=user,text='No records found.', parse_mode="HTML")
        return -1

def new_customdate(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    update.message.reply_text(f"Date selected: <b>{text}</b>.", parse_mode="HTML", reply_markup=ForceReply(selective=True))
    if len(text) != 10:
        bot.sendMessage(chat_id=update.message.chat.id,text="Invalid input. Please try again.")
        return -1
    try:
        valid_date_test = datetime.strptime(text, "%d/%m/%Y")
        user = update.effective_user
        f = open("new" + str(user['id']) + ".txt", "w+")
        f.write(text)
        f.close()
        bot.sendMessage(update.message.chat.id,"Select an expense category:", reply_markup=new_categories())
        return NEWAMT
    except IndexError:
        bot.sendMessage(chat_id=update.message.chat.id,text="Invalid input. Please try again.")
        return -1
    except ValueError:
        bot.sendMessage(chat_id=update.message.chat.id,text="Invalid input. Please try again.")
        return -1    

def new_amt(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    try:
        float(text)
        user = update.message.from_user
        f = open("new" + str(user['id']) + ".txt", "a+")
        f.write("\n" + text)
        f.close()
        update.message.reply_text(f"Please enter description of transaction:", reply_markup=ForceReply(selective=True))
        return NEWFINAL
    except ValueError:
        bot.sendMessage(chat_id=update.message.chat.id,text="Invalid input. Please try again.")
        return -1

def new_final(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    user = update.message.from_user

    table = pt.PrettyTable(['#', 'Date', 'Category', 'Amount'])
    table.align['#'] = 'l'
    table.align['Date'] = 'l'
    table.align['Category'] = 'r'
    table.align['Amount'] = 'r'

    table1 = pt.PrettyTable(['#', 'Date', 'Description'])
    table1.align['#'] = 'l'
    table1.align['Date'] = 'l'
    table1.align['Description'] = 'r'

    data = []
    data1 = []

    f = open("new" + str(user['id']) + ".txt", "a+")
    f.write("\n" + text)
    f.close()

    f = open("new" + str(user['id']) + ".txt", "r")
    fr = f.readlines()

    i = 1
    with open(str(user['id']) + ".csv", "a+", newline="") as fc:
        csvwriter = csv.writer(fc, escapechar=' ', quoting=csv.QUOTE_NONE)
        entry = fr[0].rstrip("\n"), fr[1].rstrip("\n"), fr[2].rstrip("\n"), fr[3].rstrip("\n")
        csvwriter.writerow(entry)
        data.append(tuple([i, datetime.strptime((fr[0].rstrip("\n")), "%d/%m/%Y").strftime("%d %b %y"), fr[1].rstrip("\n"), fr[2].rstrip("\n")]))
        data1.append(tuple([i, datetime.strptime((fr[0].rstrip("\n")), "%d/%m/%Y").strftime("%d %b %y"), fr[3].rstrip("\n")]))
    for no, date, category, amount in data:
        table.add_row([no, date, category, f'{float(amount):.2f}'])
    for no, date, desc in data1:
        table1.add_row([no, date, desc])
    if data != []:
        update.message.reply_text(f'<pre>{table}</pre>', parse_mode=ParseMode.HTML)
        update.message.reply_text(f'<pre>{table1}</pre>', parse_mode=ParseMode.HTML)
        bot.sendMessage(chat_id=update.message.chat.id,text="Please regularly keep a local record of your expenses via the /get_records command.")
    else:
        bot.sendMessage(chat_id=update.message.chat.id,text="Please enter a proper transaction.")
    f.close()
    table.clear()
    table1.clear()
    data.clear()
    data1.clear()
    return -1

def callback_query(update: Update, context: CallbackContext) -> int:
    call = update.callback_query
    new_file = "new" + str(call.message.chat.id) + ".txt"
    view_file = "view" + str(call.message.chat.id) + ".txt"
    file = str(call.message.chat.id) + ".csv"
    
    if call.data == "view_2017":
        bot.sendMessage(call.message.chat.id,"Select a month:", parse_mode="HTML", reply_markup=view_months())
        with open(view_file, "w+") as f:
            f.write("2017\n")
        call.edit_message_text(text="Selected year: 2017")
    if call.data == "view_2018":
        bot.sendMessage(call.message.chat.id,"Select a month:", parse_mode="HTML", reply_markup=view_months())
        with open(view_file, "w+") as f:
            f.write("2018\n")
        call.edit_message_text(text="Selected year: 2018")            
    if call.data == "view_2019":
        bot.sendMessage(call.message.chat.id,"Select a month:", parse_mode="HTML", reply_markup=view_months())
        with open(view_file, "w+") as f:
            f.write("2019\n")
        call.edit_message_text(text="Selected year: 2019")            
    if call.data == "view_2020":
        bot.sendMessage(call.message.chat.id,"Select a month:", parse_mode="HTML", reply_markup=view_months())
        with open(view_file, "w+") as f:
            f.write("2020\n")
        call.edit_message_text(text="Selected year: 2020")            
    if call.data == "view_2021":
        bot.sendMessage(call.message.chat.id,"Select a month:", parse_mode="HTML", reply_markup=view_months())
        with open(view_file, "w+") as f:
            f.write("2021\n")
        call.edit_message_text(text="Selected year: 2021")            
    if call.data == "view_2022":
        bot.sendMessage(call.message.chat.id,"Select a month:", parse_mode="HTML", reply_markup=view_months())
        with open(view_file, "w+") as f:
            f.write("2022\n")
        call.edit_message_text(text="Selected year: 2022")            
    if call.data == "all_years":
        bot.sendMessage(call.message.chat.id,"Select a category:", parse_mode="HTML", reply_markup=view_categories())
        with open(view_file, "w+") as f:
            f.write("All\n")
            f.write("All\n")
        call.edit_message_text(text="Selected year: All years")        
    if call.data == "view_today":
        bot.sendMessage(call.message.chat.id,"Select a category:", parse_mode="HTML", reply_markup=view_categories())
        with open(view_file, "w+") as f:
            date_today = str(datetime.now(pytz.timezone('Asia/Singapore')).strftime("%d/%m/%Y"))
            f.write(date_today+"\n")
            f.write("\n")
        call.edit_message_text(text="Selected date: Today")
            
            
    if call.data == "view_jan":
        bot.sendMessage(call.message.chat.id,"Select a category:", parse_mode="HTML", reply_markup=view_categories())
        with open(view_file, "a+") as f:
            f.write("1\n")
        call.edit_message_text(text="Selected month: January")            
    if call.data == "view_feb":
        bot.sendMessage(call.message.chat.id,"Select a category:", parse_mode="HTML", reply_markup=view_categories())
        with open(view_file, "a+") as f:
            f.write("2\n")
        call.edit_message_text(text="Selected month: February")            
    if call.data == "view_mar":
        bot.sendMessage(call.message.chat.id,"Select a category:", parse_mode="HTML", reply_markup=view_categories())
        with open(view_file, "a+") as f:
            f.write("3\n")
        call.edit_message_text(text="Selected month: March")             
    if call.data == "view_apr":
        bot.sendMessage(call.message.chat.id,"Select a category:", parse_mode="HTML", reply_markup=view_categories())
        with open(view_file, "a+") as f:
            f.write("4\n")
        call.edit_message_text(text="Selected month: April")            
    if call.data == "view_may":
        bot.sendMessage(call.message.chat.id,"Select a category:", parse_mode="HTML", reply_markup=view_categories())
        with open(view_file, "a+") as f:
            f.write("5\n")
        call.edit_message_text(text="Selected month: May")            
    if call.data == "view_jun":
        bot.sendMessage(call.message.chat.id,"Select a category:", parse_mode="HTML", reply_markup=view_categories())
        with open(view_file, "a+") as f:
            f.write("6\n")
        call.edit_message_text(text="Selected month: June")            
    if call.data == "view_jul":
        bot.sendMessage(call.message.chat.id,"Select a category:", parse_mode="HTML", reply_markup=view_categories())
        with open(view_file, "a+") as f:
            f.write("7\n")
        call.edit_message_text(text="Selected month: July")            
    if call.data == "view_aug":
        bot.sendMessage(call.message.chat.id,"Select a category:", parse_mode="HTML", reply_markup=view_categories())
        with open(view_file, "a+") as f:
            f.write("8\n")
        call.edit_message_text(text="Selected month: August")            
    if call.data == "view_sep":
        bot.sendMessage(call.message.chat.id,"Select a category:", parse_mode="HTML", reply_markup=view_categories())
        with open(view_file, "a+") as f:
            f.write("9\n")
        call.edit_message_text(text="Selected month: September")            
    if call.data == "view_oct":
        bot.sendMessage(call.message.chat.id,"Select a category:", parse_mode="HTML", reply_markup=view_categories())
        with open(view_file, "a+") as f:
            f.write("10\n")
        call.edit_message_text(text="Selected month: October")            
    if call.data == "view_nov":
        bot.sendMessage(call.message.chat.id,"Select a category:", parse_mode="HTML", reply_markup=view_categories())
        with open(view_file, "a+") as f:
            f.write("11\n")
        call.edit_message_text(text="Selected month: November")      
    if call.data == "view_dec":
        bot.sendMessage(call.message.chat.id,"Select a category:", parse_mode="HTML", reply_markup=view_categories())
        with open(view_file, "a+") as f:
            f.write("12\n")
        call.edit_message_text(text="Selected month: December")            
    if call.data == "all_months":
        bot.sendMessage(call.message.chat.id,"Select a category:", parse_mode="HTML", reply_markup=view_categories())
        with open(view_file, "a+") as f:
            f.write("All\n")
        call.edit_message_text(text="Selected month: All months")            
            
    if call.data == "view_food":
        with open(view_file, "a+") as f:
            f.write(categories[int(1)-1]+"\n")
        call.edit_message_text(text="Selected category: Food")
        view_filter(call.message.chat.id)
    if call.data == "view_transport":
        with open(view_file, "a+") as f:
            f.write(categories[int(2)-1]+"\n")
        view_filter(call.message.chat.id)
        call.edit_message_text(text="Selected category: Transport")
    if call.data == "view_groceries":
        with open(view_file, "a+") as f:
            f.write(categories[int(3)-1]+"\n")
        view_filter(call.message.chat.id)
        call.edit_message_text(text="Selected category: Groceries")
    if call.data == "view_savings":
        with open(view_file, "a+") as f:
            f.write(categories[int(4)-1]+"\n")
        view_filter(call.message.chat.id)
        call.edit_message_text(text="Selected category: Savings")
    if call.data == "view_clothes":
        with open(view_file, "a+") as f:
            f.write(categories[int(5)-1]+"\n")
        view_filter(call.message.chat.id)
        call.edit_message_text(text="Selected category: Clothes")
    if call.data == "view_entertain":
        with open(view_file, "a+") as f:
            f.write(categories[int(6)-1]+"\n")
        view_filter(call.message.chat.id)
        call.edit_message_text(text="Selected category: Entertain")
    if call.data == "view_bills":
        with open(view_file, "a+") as f:
            f.write(categories[int(7)-1]+"\n")
        view_filter(call.message.chat.id)
        call.edit_message_text(text="Selected category: Bills")
    if call.data == "view_misc":
        with open(view_file, "a+") as f:
            f.write(categories[int(8)-1]+"\n")
        view_filter(call.message.chat.id)
        call.edit_message_text(text="Selected category: Misc")
    if call.data == "all_cats":
        with open(view_file, "a+") as f:
            f.write("All\n")
        view_filter(call.message.chat.id)
        call.edit_message_text(text="Selected category: All categories")


    if call.data == "new_food":
        with open(new_file, "a+") as f:
            f.write("\n"+categories[int(1)-1])
        call.edit_message_text(text="Selected category: Food")
        call.message.reply_text(f"Please enter transaction amount:", reply_markup=ForceReply(selective=True))
        return NEWAMT
    if call.data == "new_transport":
        with open(new_file, "a+") as f:
            f.write("\n"+categories[int(2)-1])
        call.edit_message_text(text="Selected category: Transport")
        call.message.reply_text(f"Please enter transaction amount:", reply_markup=ForceReply(selective=True))
        return NEWAMT
    if call.data == "new_groceries":
        with open(new_file, "a+") as f:
            f.write("\n"+categories[int(3)-1])
        call.edit_message_text(text="Selected category: Groceries")
        call.message.reply_text(f"Please enter transaction amount:", reply_markup=ForceReply(selective=True))
        return NEWAMT
    if call.data == "new_savings":
        with open(new_file, "a+") as f:
            f.write("\n"+categories[int(4)-1])
        call.edit_message_text(text="Selected category: Savings")
        call.message.reply_text(f"Please enter transaction amount:", reply_markup=ForceReply(selective=True))
        return NEWAMT
    if call.data == "new_clothes":
        with open(new_file, "a+") as f:
            f.write("\n"+categories[int(5)-1])
        call.edit_message_text(text="Selected category: Clothes")
        call.message.reply_text(f"Please enter transaction amount:", reply_markup=ForceReply(selective=True))
        return NEWAMT
    if call.data == "new_entertain":
        with open(new_file, "a+") as f:
            f.write("\n"+categories[int(6)-1])
        call.edit_message_text(text="Selected category: Entertain")
        call.message.reply_text(f"Please enter transaction amount:", reply_markup=ForceReply(selective=True))
        return NEWAMT
    if call.data == "new_bills":
        with open(new_file, "a+") as f:
            f.write("\n"+categories[int(7)-1])
        call.edit_message_text(text="Selected category: Bills")
        call.message.reply_text(f"Please enter transaction amount:", reply_markup=ForceReply(selective=True))
        return NEWAMT
    if call.data == "new_misc":
        with open(new_file, "a+") as f:
            f.write("\n"+categories[int(8)-1])
        call.edit_message_text(text="Selected category: Misc")
        call.message.reply_text(f"Please enter transaction amount:", reply_markup=ForceReply(selective=True))
        return NEWAMT

def callback_query1(update: Update, context: CallbackContext) -> int:
    call = update.callback_query
    new_file = "new" + str(call.message.chat.id) + ".txt"
    view_file = "view" + str(call.message.chat.id) + ".txt"
    file = str(call.message.chat.id) + ".csv"
    if call.data == "new_customdate":
        call.edit_message_text(text=f"Selected date: Custom date")
        call.message.reply_text(f"Please enter a date:", reply_markup=ForceReply(selective=True))
        return NEWDATE

def callback_query2(update: Update, context: CallbackContext) -> int:
    today = str(datetime.now(pytz.timezone('Asia/Singapore')).strftime("%d/%m/%Y"))
    yesterday = str((datetime.now(pytz.timezone('Asia/Singapore'))-timedelta(days=1)).strftime("%d/%m/%Y"))
    twodaysago = str((datetime.now(pytz.timezone('Asia/Singapore'))-timedelta(days=2)).strftime("%d/%m/%Y"))
    threedaysago = str((datetime.now(pytz.timezone('Asia/Singapore'))-timedelta(days=3)).strftime("%d/%m/%Y"))
    fourdaysago = str((datetime.now(pytz.timezone('Asia/Singapore'))-timedelta(days=4)).strftime("%d/%m/%Y"))
    fivedaysago = str((datetime.now(pytz.timezone('Asia/Singapore'))-timedelta(days=5)).strftime("%d/%m/%Y"))
    sixdaysago = str((datetime.now(pytz.timezone('Asia/Singapore'))-timedelta(days=6)).strftime("%d/%m/%Y"))
    
    call = update.callback_query
    new_file = "new" + str(call.message.chat.id) + ".txt"
    view_file = "view" + str(call.message.chat.id) + ".txt"
    file = str(call.message.chat.id) + ".csv"   
    if call.data == "new_today":
        bot.sendMessage(call.message.chat.id,"Selected a category:", parse_mode="HTML", reply_markup=new_categories())
        with open(new_file, "w+") as f:
            f.write(str(today))
        call.edit_message_text(text=f"Selected date: {today}")
        return NEWAMT
    if call.data == "new_yesterday":
        bot.sendMessage(call.message.chat.id,"Selected a category:", parse_mode="HTML", reply_markup=new_categories())
        with open(new_file, "w+") as f:
            f.write(str(yesterday))
        call.edit_message_text(text=f"Selected date: {yesterday}")
        return NEWAMT
    if call.data == "new_twodaysago":
        bot.sendMessage(call.message.chat.id,"Selected a category:", parse_mode="HTML", reply_markup=new_categories())
        with open(new_file, "w+") as f:
            f.write(str(twodaysago))
        call.edit_message_text(text=f"Selected date: {twodaysago}")
        return NEWAMT
    if call.data == "new_threedaysago":
        bot.sendMessage(call.message.chat.id,"Selected a category:", parse_mode="HTML", reply_markup=new_categories())
        with open(new_file, "w+") as f:
            f.write(str(threedaysago))
        call.edit_message_text(text=f"Selected date: {threedaysago}")
        return NEWAMT
    if call.data == "new_fourdaysago":
        bot.sendMessage(call.message.chat.id,"Selected a category:", parse_mode="HTML", reply_markup=new_categories())
        with open(new_file, "w+") as f:
            f.write(str(fourdaysago))
        call.edit_message_text(text=f"Selected date: {fourdaysago}")
        return NEWAMT
    if call.data == "new_fivedaysago":
        bot.sendMessage(call.message.chat.id,"Selected a category:", parse_mode="HTML", reply_markup=new_categories())
        with open(new_file, "w+") as f:
            f.write(str(fivedaysago))
        call.edit_message_text(text=f"Selected date: {fivedaysago}")
        return NEWAMT
    if call.data == "new_sixdaysago":
        bot.sendMessage(call.message.chat.id,"Selected a category:", parse_mode="HTML", reply_markup=new_categories())
        with open(new_file, "w+") as f:
            f.write(str(sixdaysago))
        call.edit_message_text(text=f"Selected date: {sixdaysago}")
        return NEWAMT


def cancel(update: Update, context: CallbackContext) -> int:
    return ConversationHandler.END


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(config.telegram_token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    #dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(callback_query))

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
   
    conv_handler_new_customdate = ConversationHandler(
        #entry_points=[CallbackQueryHandler(callback_query)],
        entry_points=[CallbackQueryHandler(callback_query1)],
        states={
            NEWDATE: [
                MessageHandler(
                    Filters.regex(''), new_customdate
                )
            ],            
            NEWAMT: [
                MessageHandler(
                    Filters.regex(''), new_amt
                )
            ],    
            NEWFINAL: [
                MessageHandler(
                    Filters.regex(''), new_final
                )
            ],                                 
        },
        fallbacks=[MessageHandler(Filters.command, cancel)],
        allow_reentry=True,
    )    

    conv_handler_new_specificdate = ConversationHandler(
        #entry_points=[CallbackQueryHandler(callback_query)],
        entry_points=[CallbackQueryHandler(callback_query2)],
        states={
            NEWAMT: [
                MessageHandler(
                    Filters.regex(''), new_amt
                )
            ],    
            NEWFINAL: [
                MessageHandler(
                    Filters.regex(''), new_final
                )
            ],                                 
        },
        fallbacks=[MessageHandler(Filters.command, cancel)],
        allow_reentry=True,
    )    
    
    conv_handler4 = ConversationHandler(
        entry_points=[CommandHandler("delete", delete1)],
        states={
            DELETE2: [
                MessageHandler(
                    Filters.regex(''), delete2
                )
            ],
        },
        fallbacks=[MessageHandler(Filters.command, cancel)],
        allow_reentry=True,
    )

    conv_handler5 = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            REQACC2: [
                MessageHandler(
                    Filters.regex(''), reqacc2
                )
            ],
        },
        fallbacks=[MessageHandler(Filters.command, cancel)],
        allow_reentry=True,
    )

    conv_handler6 = ConversationHandler(
        entry_points=[CommandHandler("auth", auth)],
        states={
            AUTH1: [
                MessageHandler(
                    Filters.regex(''), auth1
                )
            ],
        },
        fallbacks=[MessageHandler(Filters.command, cancel)],
        allow_reentry=True,
    )

    conv_handler7 = ConversationHandler(
        entry_points=[CommandHandler("revoke", revoke)],
        states={
            REVOKE1: [
                MessageHandler(
                    Filters.regex(''), revoke1
                )
            ],
        },        
        fallbacks=[MessageHandler(Filters.command, cancel)],
        allow_reentry=True,
    )

    conv_handler8 = ConversationHandler(
        entry_points=[CommandHandler("import", import1)],
        states={
            IMPORT1: [
                MessageHandler(
                    Filters.regex(''), import2
                )
            ],
        },
        fallbacks=[MessageHandler(Filters.command, cancel)],
        allow_reentry=True,
    )    

    conv_handler9 = ConversationHandler(
        entry_points=[CommandHandler("reset", reset)],
        states={
            RESET1: [
                MessageHandler(
                    Filters.regex(''), reset1
                )
            ],
        },
        fallbacks=[MessageHandler(Filters.command, cancel)],
        allow_reentry=True,
    )

    dispatcher.add_handler(conv_handler_new_customdate,4)
    dispatcher.add_handler(conv_handler_new_specificdate,5)
    dispatcher.add_handler(conv_handler4,6)
    dispatcher.add_handler(conv_handler5,7)
    dispatcher.add_handler(conv_handler6,8)
    dispatcher.add_handler(conv_handler7,8)
    dispatcher.add_handler(conv_handler8,9)
    dispatcher.add_handler(conv_handler9,12)
    dispatcher.add_handler(CommandHandler("view", view),1)
    dispatcher.add_handler(CommandHandler("help", help_command),2)
    dispatcher.add_handler(CommandHandler("new", new),3)
    dispatcher.add_handler(CommandHandler("get_records", getrecords),10)
    dispatcher.add_handler(CommandHandler("debug", debug),11)
    dispatcher.add_handler(CommandHandler("today", viewtoday),13)
    dispatcher.add_handler(MessageHandler(Filters.document, import2))
    
    # Start the Bot
    updater.start_polling()
    
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    #updater.idle()


if __name__ == '__main__':
    main()
