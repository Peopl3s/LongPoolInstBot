import requests
import vk_api
from vk_api import VkUpload
from vk_api.longpoll import VkLongPoll, VkEventType
import json
import re

def loadIns(link):
    '''
    Получает и возвращает html-код страницы, переданной по ссылке

    '''
    headers = {'User-Agent': 'Mozilla/5.0\
               (Macintosh; Intel Mac OS X 10.9; rv:45.0)\
               Gecko/20100101 Firefox/45.0'}
    body = ""
    try:
        body = str(requests.get(link, headers=headers).text) 
    except requests.exceptions.RequestException as reqErr:
        print(reqErr)
    return body

def parseJson(jsonFile='C://Server/www/tokenowner.json'):
    '''
    Получает access token страницы из json-файла jsonFile
    
    '''
    try:
        jsObj = open(jsonFile, 'r')
        pObj = json.load(jsObj)
    except ValueError as vErr:
        print(vErr)
    except IOError as ioErr:
        print(ioErr)
    finally:
        jsObj.close()
    return pObj['access_token']

def listOfContent(body):
    '''
    Ищет в html-коде страницы строки вида: "display_url"/"video_url"):"https:
    Формирует список ссылок на фото или видео контент страницы
       
    '''
    content = []
    regEx = re.compile(r'(("display_url"|"video_url"):\"https://(.*?).(jpg|mp4)")')
    result = regEx.finditer(body)
    if result:
        for match in result:
            if str(match.group(0)) not in content:
                content.append(str(match.group(0)))            
    return content

def getAttach(typeContent, url, attachments, session, upload, profile):
    '''
    Создаёт список прикреплённых материалов для отправки пользователю
    Прикрепляется фото или видео файл, полученный по ссылке
       
    '''
    text = "Из профиля пользователя: " + profile[profile.index('=')+1:]
    if not url:
        return 'Error'
    if typeContent == 'photo':
        image = session.get(url, stream=True)
        photo = upload.photo_messages(photos=image.raw)[0]
        attachments.append('photo{}_{}'.format(photo['owner_id'], photo['id']))
    else:
        video_f = session.get(url, stream=True)
        video = upload.video(video_file=video_f.raw, is_private=1)
        attachments.append('video{}_{}'.format(video['owner_id'], video['video_id']))
    return text        
        
def main():
    '''
    Функция реализующая авторизацию страницы и работу бота

    '''
    session = requests.Session()
    tokenn = parseJson() 
    vk_session = vk_api.VkApi(token=tokenn)
    longpoll = VkLongPoll(vk_session)
    vk = vk_session.get_api()
    upload = VkUpload(vk_session)
    
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
            print('id{}: "{}"'.format(event.user_id, event.text), end=' ')  
            attachments = []
            delSize = 0
            typeContent = ""
            content = listOfContent(loadIns(event.text))
            if len(content) > 0:
                for newUrl in content:
                    if "video" in newUrl:
                        delSize = 13
                        typeContent = "video"
                    else:
                        delSize = 15
                        typeContent = "photo"
                    url = newUrl[delSize:len(newUrl)-1]
                    text = getAttach(typeContent,
                                   url,
                                   attachments,
                                   session,
                                   upload,
                                   event.text)
                vk.messages.send(
                    user_id=event.user_id,
                    attachment=','.join(attachments),
                    message=text)
            else:
                vk.messages.send(user_id=event.user_id,
                                 message='Ошибка.Некорректная ссылка\
                                 или ссылка на закрытый аккаунт')
            
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
