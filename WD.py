import requests, vk_api, schedule, datetime, time, sqlite3, threading, secrets, string
from bs4 import BeautifulSoup
from vk_api.utils import get_random_id

vk_session = vk_api.VkApi(token='3e0d60982cd52ce4790a744e3386709cbeff9ff8e821e0a9125b867122fa2e2891a9f9aae50e746678775')
sqlite_connection = sqlite3.connect('D:/SOULBURN/SQLiteStudio/SQLiteDataBase')
cursor = sqlite_connection.cursor()

from vk_api.longpoll import VkLongPoll, VkEventType
longpoll = VkLongPoll(vk_session)
vk = vk_session.get_api()

url = 'https://rp5.ru/Погода_в_Абакане'
response = requests.get(url)
print(response.status_code)
soup = BeautifulSoup(response.text, 'lxml')
forecasts = soup.find_all('div', class_='round-5')
for forecast in forecasts:
    text=(forecast.text)
    text=text.replace("Сегодня ", "По Цельсию сегодня ").replace("ожидается ", "ожидается от ").replace("..", "° до ").replace("°C°F","°").replace(" °, ","°, ")
    text=text.replace("Завтра: ", "Завтра: по Цельсию от ").replace("°, +", "°, по Фаренгейту от +").replace("°, -", "°, по Фаренгейту от -")

def messagesend(botmessage):
    vk.messages.send(user_id=event.user_id, message=botmessage, random_id=event.random_id)

def weather_message():
    vk.messages.send(user_id=event.user_id, message=str(text), random_id=get_random_id())

def adminchatsend(chatmessage):
    message_id=vk.messages.send(chat_id=3, message=chatmessage, random_id=get_random_id())
    return message_id

def select_sql():
    messagesend('Введите SELECT-запрос')
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
            if event.text != '/back':
                try:
                    date=cursor.execute(event.text)
                    date=cursor.fetchall()
                    datenew= ''.join(str(date) for date in date)
                    datenew=datenew.replace("(","\n").replace(", '"," | ").replace("'","").replace(")","")
                    messagesend(datenew)
                except Exception:
                    messagesend('Допущена ошибка в SQL-выражении')
            else:
                messagesend('Открыта админ-панель. Возможности:\n1. Ввести SQL-запрос, включающий SELECT\n2. Ввести SQL-запрос, используя INSERT, DELETE или UPDATE')
                return(0)

def delete_insert_update_sql():
    messagesend('Введите INSERT, DELETE или UPDATE-запрос')
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
            if event.text != '/back':
                try:
                    insertid=cursor.execute(event.text)
                    sqlite_connection.commit()
                    messagesend('Выражение выполнено успешно')
                except Exception:
                    messagesend('Допущена ошибка в SQL-выражении')
            else:
                messagesend('Открыта админ-панель. Возможности:\n1. Ввести SQL-запрос, включающий SELECT\n2. Ввести SQL-запрос, используя INSERT, DELETE или UPDATE')
                return

def admin_panel():
    messagesend('Открыта админ-панель. Возможности:\n1. Ввести SQL-запрос, включающий SELECT\n2. Ввести SQL-запрос, используя INSERT, DELETE или UPDATE')
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
            if event.text == '1':
                select_sql()
            if event.text == '2':
                delete_insert_update_sql()
            if event.text == '/back':
                messagesend('Еще раз введите "/back" для выхода из админ-панели')
                return

def generate_token(lenght):
    messagesend('Введите актуальный токен')
    symbols = string.ascii_letters + string.digits
    token = ''.join(secrets.choice(symbols) for i in range (lenght))
    token_message_id=adminchatsend(token)
    for event in longpoll.listen():
      if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
          if event.text != '/back':
              if event.text == token:
                  admin_panel()
              if event.text != token:
                  messagesend('Неверный токен')
          else:
            vk.messages.delete(message_ids=str(token_message_id), delete_for_all=1)
            messagesend('Список возможностей:\na) Получить текущий прогноз погоды\nb) Получить прогноз погоды за прошедшую неделю\nc) Получать прогноз погоды по расписанию\nd) Дополнительные возможности')
            return

def get_user_id():
    getuser = vk.users.get(user_id=event.user_id, fields='')
    getuser= ''.join(str(getuser) for getuser in getuser)
    getuser = list(filter(str.isdigit, getuser))
    getuser=str(getuser).replace("', '", "").replace("['", "").replace("']","")
    return getuser

def check_user_role():
    id=get_user_id()
    role=cursor.execute("SELECT Role FROM Users WHERE User_ID='" + id + "'")
    role=cursor.fetchall()
    role=str(role).replace("',), ('"," ").replace("[('","").replace("',)]","")
    return role

def add_user():
    getuser=get_user_id()
    check_id=cursor.execute("SELECT User_ID from Users")
    check_id=cursor.fetchall()
    check_id= ''.join(str(check_id) for check_id in check_id)
    check_id=check_id.replace("[(", "").replace(")]","").replace(",,",", ").replace("(","").replace(")","").replace(","," ")
    check_id="" + getuser + "" in check_id
    check_id=str(check_id)
    if check_id == 'True':
        adminchatsend('Пользователь с ID "' + getuser + '" не добавлен, так как уже существует в базе')
    if check_id == 'False':
        try:
            cursor.execute("SELECT ID FROM Users WHERE ID=(SELECT MAX(ID) FROM Users)")
            userid=cursor.fetchone()
            userid= ''.join(str(userid) for userid in userid)
            userid=int(userid)+1
            add_user=cursor.execute("INSERT INTO Users (ID, User_ID, Role) VALUES ('" + str(userid) + "', '" + getuser + "', 'User');")
            sqlite_connection.commit()
            adminchatsend('Добавлен новый пользователь с ID "' + getuser + '"')
        except Exception:
            adminchatsend('При добавлении пользователя с ID "' + getuser + '" возникла ошибка')

def update_db():
    response = requests.get(url)
    print(response.status_code)
    soup = BeautifulSoup(response.text, 'lxml')
    forecasts = soup.find_all('div', class_='round-5')
    for forecast in forecasts:
        text=(forecast.text)
        text=text.replace("Сегодня ", "По Цельсию сегодня ").replace("ожидается ", "ожидается от ").replace("..", "° до ").replace("°C°F","°").replace(" °, ","°, ")
        text=text.replace("Завтра: ", "Завтра: по Цельсию от ").replace("°, +", "°, по Фаренгейту от +").replace("°, -", "°, по Фаренгейту от -")

    check_date=cursor.execute("SELECT Date from Forecasts")
    check_date=cursor.fetchall()
    check_date= ''.join(str(check_date) for check_date in check_date)
    check_date=check_date.replace("',)('"," ").replace("  "," ").replace("(","").replace(")","").replace("'","").replace(",","")
    check_date="" + str(datetime.date.today()) + "" in check_date
    check_date=str(check_date)

    if check_date == 'True':
        update_forecast=cursor.execute("UPDATE Forecasts SET Forecast='" + str(text) + "' WHERE Date='" + str(datetime.date.today()) + "'")
        sqlite_connection.commit()
        adminchatsend('Прогноз на дату ' + str(datetime.date.today()) + ' обновлен, так как дата уже добавлена')

    if check_date == 'False':
        try:
            insertid=cursor.execute("SELECT ID FROM Forecasts WHERE ID=(SELECT MAX(ID) FROM Forecasts)")
            insertid=cursor.fetchone()
            insertid= ''.join(str(insertid) for insertid in insertid)
            insertid=int(insertid)+1
            text=text.replace("По Цельсию сегодня ожидается", "Ожидается").replace("Завтра:", "На следующий день:")
            insertintotable=cursor.execute("INSERT INTO Forecasts (ID, Date, Forecast) VALUES ('" + str(insertid) + "', '" + str(datetime.date.today()) + "', '" + str(text) + "');")
            sqlite_connection.commit()
            adminchatsend('База была обновлена ' + str(datetime.date.today()) + ' в ' + str(datetime.datetime.now().time().strftime('%H:%M')))
        except Exception:
            adminchatsend('Возникла ошибка при обновлении базы ' + str(datetime.date.today()) + ' в ' + str(datetime.datetime.now().time().strftime('%H:%M')))

def assistant_panel():
    messagesend('\nОткрыта панель ассистента. Возможности:\n1. Добавить прогноз погоды на сегодня')
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
            if event.text == '1':
                messagesend('Добавление актуального прогноза...')
                update_db()
                messagesend('Прогноз погоды на сегодня успешно добавлен')
                return

def shedule_every_minutes():
    messagesend('Прогноз погоды будет приходить каждые полчаса')
    schedule.every(30).minutes.do(weather_message)
    while True:
        schedule.run_pending()
        time.sleep(1)

def shedule_every_hour():
    messagesend('Прогноз погоды будет приходить каждый час')
    schedule.every().hour.do(weather_message)
    while True:
        schedule.run_pending()
        time.sleep(1)

def shedule_every_hours(hours):
    messagesend('Прогноз погоды будет приходить каждые ' + str(hours) + ' часа(ов)')
    schedule.every(hours).hours.do(weather_message)
    while True:
        schedule.run_pending()
        time.sleep(1)

def shedule_every_day():
    messagesend('Прогноз погоды будет приходить утром и вечером')
    schedule.every().day.at("06:00").do(weather_message)
    schedule.every().day.at("22:00").do(weather_message)
    while True:
        schedule.run_pending()
        time.sleep(1)

for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
        event.text=event.text.lower()

        if event.text == '1':
            minutes_thread=threading.Thread(target=shedule_every_minutes).start()

        if event.text == '2':
            one_hour_thread=threading.Thread(target=shedule_every_hour).start()

        if event.text == '3':
            three_hours_thread=threading.Thread(target=shedule_every_hours, kwargs={'hours':3}).start()

        if event.text == '4':
            six_hours_thread=threading.Thread(target=shedule_every_hours, kwargs={'hours':6}).start()

        if event.text == '5':
            everyday_thread=threading.Thread(target=shedule_every_day).start()

        if event.text == 'привет' or event.text == 'начать' or event.text == 'menu' or event.text == 'меню' or event.text == 'назад':
            add_user()
            messagesend('Список возможностей:\na) Получить текущий прогноз погоды\nb) Получить прогноз погоды за прошедшую неделю\nc) Получать прогноз погоды по расписанию\nd) Дополнительные возможности')
        
        if event.text == 'a':
            messagesend(str(text))

        if event.text == 'b':
            date=cursor.execute("SELECT Date, Forecast FROM Forecasts ORDER BY ID DESC LIMIT 7")
            date=cursor.fetchall()
            datenew= ''.join(str(date) for date in date)
            datenew=datenew.replace("(","\n").replace(", '",": ").replace("'","").replace(")","").replace("2021","\n2021")
            messagesend(datenew)

        if event.text == 'c':
            messagesend('Когда должен приходить прогноз погоды?\n\n1. Каждые полчаса\n2. Каждый час\n3. Каждые 3 часа\n4. Каждые 6 часов\n5. Утром и вечером')

        if event.text == 'd':
            role=check_user_role()
            adminrole="Admin" in role
            assistantrole="Assistant" in role
            userrole="User" in role
            if adminrole:
                messagesend('Вы являетесь администратором. Для открытия панели администратора введите "/admin". Для закрытия панели администратора введите "/back". Все токены для входа в панель администратора отправляются в чат администраторов')
            else:
                if assistantrole:
                    messagesend('Вы являетесь ассистентом. Для открытия панели ассистента введите "/assistant". Для закрытия панели администратора введите "/back"')
                else:
                    if userrole:
                        messagesend('Вам недоступны дополнительные возможности')



        if event.text == '/admin':
            role=check_user_role()
            messagesend('Проверка вашей роли...')
            role="Admin" in role
            if role:
                generate_token(30)
            else:
                messagesend('Вы не являетесь администратором')

        if event.text == 'get': # get user_id test
            add_user()

        if event.text == 'up': # update db test
            update_db()

        if event.text == '/assistant':
            role=check_user_role()
            messagesend('Проверка вашей роли...')
            role="Assistant" in role
            if role:
                assistant_panel()
            else:
                messagesend('Вы не являетесь ассистентом')



