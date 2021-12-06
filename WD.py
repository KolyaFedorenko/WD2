import requests, vk_api, schedule, datetime, time, sqlite3, threading, secrets, string
from bs4 import BeautifulSoup
from vk_api.utils import get_random_id

vk_session = vk_api.VkApi(token='3e0d60982cd52ce4790a744e3386709cbeff9ff8e821e0a9125b867122fa2e2891a9f9aae50e746678775')
sqlite_connection = sqlite3.connect('D:/Desktop/SQLiteStudio/SQLiteDataBase')
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
    vk.messages.send(chat_id=3, message=chatmessage, random_id=get_random_id())

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
                return(0)

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
                return (0)

def generate_token(lenght):
    messagesend('Введите токен')
    symbols = string.ascii_letters + string.digits
    token = ''.join(secrets.choice(symbols) for i in range (lenght))
    adminchatsend(token)
    for event in longpoll.listen():
      if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
          if event.text != '/back':
              if event.text == token:
                  admin_panel()
              if event.text != token:
                  messagesend('Неверный токен')
          else:
            messagesend('Список возможностей:\na) Получить текущий прогноз погоды\nb) Получить прогноз погоды за прошедшую неделю\nc) Получать прогноз погоды по расписанию')
            return (0)

def add_user():
    getuser = vk.users.get(user_id=event.user_id, fields='')
    getuser= ''.join(str(getuser) for getuser in getuser)
    getuser = list(filter(str.isdigit, getuser))
    getuser=str(getuser).replace("', '", "").replace("['", "").replace("']","")

    check_id=cursor.execute("SELECT User_ID from users")
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
    url = 'https://rp5.ru/Погода_в_Абакане'
    response = requests.get(url)
    print(response.status_code)
    soup = BeautifulSoup(response.text, 'lxml')
    forecasts = soup.find_all('div', class_='round-5')
    for forecast in forecasts:
        text=(forecast.text)
        text=text.replace("Сегодня ", "По Цельсию сегодня ").replace("ожидается ", "ожидается от ").replace("..", "° до ").replace("°C°F","°").replace(" °, ","°, ")
        text=text.replace("Завтра: ", "Завтра: по Цельсию от ").replace("°, +", "°, по Фаренгейту от +").replace("°, -", "°, по Фаренгейту от -")

    try:
        insertid=cursor.execute("SELECT ID FROM Forecasts WHERE ID=(SELECT MAX(ID) FROM Forecasts)")
        insertid=cursor.fetchone()
        insertid= ''.join(str(insertid) for insertid in insertid)
        insertid=int(insertid)+1
        messagesend(str(insertid))
        text=text.replace("По Цельсию сегодня ожидается", "Ожидается").replace("Завтра:", "На следующий день:")
        insertintotable=cursor.execute("INSERT INTO Forecasts (ID, Date, Forecast) VALUES ('" + str(insertid) + "', '" + str(datetime.date.today()) + "', '" + str(text) + "');")
        sqlite_connection.commit()
        adminchatsend('База была обновлена ' + str(datetime.date.today()) + ' в ' + str(datetime.datetime.now().time().strftime('%H:%M')))
    except Exception:
        adminchatsend('Возникла ошибка при обновлении базы ' + str(datetime.date.today()) + ' в ' + str(datetime.datetime.now().time().strftime('%H:%M')))

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
            messagesend('Список возможностей:\na) Получить текущий прогноз погоды\nb) Получить прогноз погоды за прошедшую неделю\nc) Получать прогноз погоды по расписанию')
        
        if event.text == 'a':
            messagesend(str(text))

        if event.text == 'b':
            date=cursor.execute("SELECT Date, Forecast FROM Forecasts")
            date=cursor.fetchall()
            datenew= ''.join(str(date) for date in date)
            datenew=datenew.replace("(","\n").replace(", '",": ").replace("'","").replace(")","")
            messagesend(datenew)

        if event.text == 'c':
            messagesend('Когда должен приходить прогноз погоды?\n\n1. Каждые полчаса\n2. Каждый час\n3. Каждые 3 часа\n4. Каждые 6 часов\n5. Утром и вечером')

        if event.text == '/admin':
            generate_token(30)

        if event.text == 'get': # get user_id test
            add_user()

        if event.text == 'up': # update db test
            update_db()

