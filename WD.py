import requests
from bs4 import BeautifulSoup
import vk_api
from vk_api.utils import get_random_id
import schedule 
import time

vk_session = vk_api.VkApi(token='3e0d60982cd52ce4790a744e3386709cbeff9ff8e821e0a9125b867122fa2e2891a9f9aae50e74667877')

url = 'https://rp5.ru/Погода_в_Абакане'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'lxml')
forecasts = soup.find_all('div', class_='round-5')

for forecast in forecasts:
    text=(forecast.text)

from vk_api.longpoll import VkLongPoll, VkEventType
longpoll = VkLongPoll(vk_session)
vk = vk_session.get_api()

def weather_message():
    vk.messages.send(user_id=event.user_id, message=str(text), random_id=get_random_id())

def messagesend(botmessage):
    vk.messages.send(user_id=event.user_id, message=botmessage, random_id=event.random_id)

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
        if event.text == '1':
            shedule_every_minutes()

        if event.text == '2':
            shedule_every_hour()

        if event.text == '3':
            shedule_every_hours(3)

        if event.text == '4':
            shedule_every_hours(6)

        if event.text == '5':
            shedule_every_day()

        if event.text == 'Привет' or event.text == 'привет' or event.text == 'Начать' or event.text == 'начать':
            messagesend('Список возможностей:\na) Получить текущий прогноз погоды\nb) Получить прогноз погоды за прошедшую неделю\nc) Получать прогноз погоды по расписанию')
        
        if event.text == 'a':
            messagesend(str(text))

        if event.text == 'b':
            messagesend('123')

        if event.text == 'c':
            messagesend('Когда должен приходить прогноз погоды?\n\n1. Каждые полчаса\n2. Каждый час\n3. Каждые 3 часа\n4. Каждые 6 часов\n5. Утром и вечером')


            