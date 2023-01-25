import warnings
import bs4
import dataclasses
import copy
import datetime
import lxml
import logging
import re
import typing
import urllib.parse
import json
import requests
import os
from pyfiglet import Figlet


class TgPost:
    def __init__(self, post_instance, id, post_type, post_text=' '):
        self.post_instance = post_instance
        self.id = id
        self.post_type = post_type
        self.post_text = post_text


def create_TgPost(posts, post_type):
    tgpost_list = list()
    ids = get_ids(posts)
    for (post, id) in zip(posts, ids):
        tgpost_list.append(TgPost(post, id, post_type))
    return tgpost_list


def join_string(some_list):
    some_string = ''
    for digit in some_list:
        some_string += f'{digit} '
    return some_string[:len(some_string) - 1]


def get_info():
    global _type
    kwargs = {}
    url = f'https://t.me/{name}'
    page = requests.get(url, headers=headers)
    soup = bs4.BeautifulSoup(page.text, "lxml")
    page.close()
    membersDiv = soup.find('div', class_='tgme_page_extra')
    type_of_tg = None
    kwargs['name'] = name
    try:
        if membersDiv.text.endswith(' subscribers'):
            type_of_tg = 'channel'
            _type = type_of_tg
            members = join_string(re.findall(r'\d+', membersDiv.text))
            kwargs['members_all'] = members
            kwargs['members_online'] = 'None'
        if membersDiv.text.endswith(' online'):
            type_of_tg = 'chat'
            _type = type_of_tg
            members_text = membersDiv.text.split(',')
            members_all = join_string(re.findall(r'\d+', members_text[0]))
            members_online = join_string(re.findall(r'\d+', members_text[1]))
            kwargs['members_all'] = members_all
            kwargs['members_online'] = members_online
        titleDiv = soup.find('div', class_='tgme_page_title')
        kwargs['type'] = type_of_tg
        kwargs['title'] = titleDiv.find('span').text
        if type_of_tg == 'channel':
            description = soup.find('div', class_='tgme_page_description')
            kwargs['description'] = description.text
        else:
            kwargs['description'] = 'None'
        kwargs['verified'] = bool(titleDiv.find('i', class_='verified-icon'))
        kwargs['photo'] = soup.find('img', class_='tgme_page_photo_image').attrs['src']
        return kwargs
    except:
        print('Ошибка в названии канала/чата')


def get_info_about_tg():
    global _info
    # Собираем информацию о канале
    info = get_info()
    _info = info
    # Указываем папку сохранения данных
    # Сохраняем
    try:
        os.chdir(path=main_path)
    except FileNotFoundError:
        os.mkdir(path=main_path)
        os.chdir(path=main_path)
    if not os.path.isdir(current_channel_path):
        os.mkdir(current_channel_path)
    os.chdir(path=current_channel_path)
    if os.path.exists(photo_name):
        pass
    else:
        download_photo(info['photo'], photo_name)
    with open("info_file.json", "w") as write_file:
        json.dump(info, write_file)


def download_photo(photo, filename):
    photo_download = requests.get(photo, headers=headers)
    photo_download.close()
    with open(filename, 'wb') as folder:
        folder.write(photo_download.content)


def download_video(video, filename):
    video_download = requests.get(video, headers=headers)
    video_download.close()
    with open(filename, 'wb') as folder:
        folder.write(video_download.content)


def write_data(some_data, filename):
    with open(filename, "w") as write_file:
        json.dump(some_data, write_file)


def get_ids(posts):
    post_number_list = list()
    for post in posts:
        try:
            cur_post = post.attrs['data-post']
        except:
            cur_post = post.attrs['href']
        post_number = int(re.findall(r'\d+', cur_post)[0])
        post_number_list.append(post_number)
    return post_number_list


def find_id_in_another_list(some_instances_list, id):
    for item in some_instances_list:
        if item.id == id:
            return True
    return False


def return_id_from_another_list(some_instances_list, id):
    for item in some_instances_list:
        if item.id == id:
            return item
    return None


def get_type(post_id):
    global video_instances_list, photos_instances_list
    is_video = find_id_in_another_list(video_instances_list, post_id)
    is_photo = find_id_in_another_list(photos_instances_list, post_id)
    post_type = None
    if is_video:
        post_type = 'video'
    if is_photo:
        post_type = 'photo'
    else:
        post_type = 'undefined'
    return post_type


def get_text(post_instance):
    text = ' '
    params = {'message': list(), 'message_views': list(), 'message_time': list()}
    if post_instance is not None:
        inf = re.findall(r'\n{1,5}[\d\w\s\.]*\d\d:\d\d', post_instance.post_instance.text)
        messages_data = post_instance.post_instance.text
        if inf is not []:
            params['message'].append(messages_data.split(inf[0])[0])
            params['message_views'].append(re.findall(r'[\d\.K]+', inf[0])[0])
            params['message_time'].append(re.findall(r'\d\d:\d\d', messages_data)[0])
    text = params['message']
    return text


def write_all_data_from_instance(post_path, some_instance, is_main):
    global _count
    #messages_data = reversed_data[i].post_instance.text
    messages_data = some_instance.post_instance.text
    inf = re.findall(r'\n{1,5}[\d\w\s\.]*\d\d:\d\d', messages_data)
    params = {'message': list(), 'message_views': list(), 'message_time': list()}
    if some_instance.post_text != ' ':
        params['message'] = some_instance.post_text
        pass
    if is_main:
        os.chdir(path=main_path + "\\" + current_channel_path + "\\" + post_path)
        write_data(params, f"{some_instance.id}_messages_data.json")
    media_object = return_id_from_another_list(photos_instances_list, some_instance.id)
    if media_object is None:
        media_object = return_id_from_another_list(video_instances_list, some_instance.id)

    if media_object is not None:
        if media_object.post_type == 'video':
            try:
                content = media_object.post_instance.find_all('video', class_='tgme_widget_message_video')[0].attrs[
                    'src']
                download_video(content, f"{some_instance.id}_video.mp4")
                _count += 1
            except:
                print(f'Unable to download id_{media_object.id}')
        if media_object.post_type == 'photo':
            content = re.findall(r"https://[\w\d\.\s\-\/]*",
                                 re.findall(r"url\('https://[\w\d\.\s\-\/]*'\)",
                                            media_object.post_instance.attrs['style'])[0])[0]
            download_photo(content, f"{some_instance.id}_photo.jpg")
            _count += 1



def write_single_post(post_path, post_instance):
    params = {'message': list(), 'message_views': list(), 'message_time': list()}
    if not os.path.isdir(main_path+"\\"+current_channel_path+"\\"+post_path):
        os.mkdir(path=main_path+"\\"+current_channel_path+"\\"+post_path)
    messages_data = post_instance[1].post_instance.text
    inf = re.findall(r'\n{1,5}[\d\w\s\.]*\d\d:\d\d', messages_data)
    params['message'].append(messages_data.split(inf[0])[0])
    params['message_views'].append(re.findall(r'[\d\.K]+', inf[0])[0])
    params['message_time'].append(re.findall(r'\d\d:\d\d', messages_data)[0])
    os.chdir(path=main_path+"\\"+current_channel_path+"\\"+post_path)
    media_object = return_id_from_another_list(photos_instances_list, post_instance[1].id)
    if media_object is None:
        media_object = return_id_from_another_list(video_instances_list, post_instance[1].id)

    if media_object is not None:
        if media_object.post_type == 'video':
            try:
                content = media_object.post_instance.find_all('video', class_='tgme_widget_message_video')[0].attrs['src']
                download_video(content, f"{post_instance[1].id}_video.mp4")
            except:
                print(f'Unable to download id_{media_object.id}')
        if media_object.post_type == 'photo':
            content = re.findall(r"https://[\w\d\.\s\-\/]*",
                                 re.findall(r"url\('https://[\w\d\.\s\-\/]*'\)",
                                            media_object.post_instance.attrs['style'])[0])[0]
            download_photo(content, f"{post_instance[1].id}_photo.jpg")

    write_data(params, f"{post_instance[1].id}_messages_data.json")


def write_group_post(post_path, post_instance):
    global _count
    params = {'message': list(), 'message_views': list(), 'message_time': list()}
    if not os.path.isdir(main_path + "\\" + current_channel_path + "\\" + post_path):
        os.mkdir(path=main_path + "\\" + current_channel_path + "\\" + post_path)
    reversed_data = list(reversed(post_instance))
    main_post = reversed_data[0]
    write_all_data_from_instance(post_path, main_post, True)
    for i in range (1, len(reversed_data) - 1):
        write_all_data_from_instance(post_path, reversed_data[i], False)
    _count = 1


def load_more(posts):
    last_post = posts[len(posts) - 1].attrs['data-post']
    last_post_number = int(re.findall(r'\d+', last_post)[0])
    url = f'https://t.me/s/{name}?before={last_post_number}'
    page = requests.get(url, headers=headers)
    page.close()
    if page.status_code != 200:
        print('Error')
    soup = bs4.BeautifulSoup(page.text, "lxml")


def get_parsed_post(post_count):
    kwargs = {}
    global _type, video_instances_list, photos_instances_list
    # Парсим посты
    url = f'https://t.me/s/{name}'
    page = requests.get(url, headers=headers)
    if page.status_code != 200:
        print('Error')
    soup = bs4.BeautifulSoup(page.text, "lxml")
    if _type == 'channel':
        # Список постов
        posts = soup.find_all('div', attrs={'class': 'tgme_widget_message'})
        posts = list(reversed(posts))
        post_number_list = get_ids(posts)
        # Список сгруппированных постов
        grouped_media = list(reversed(soup.find_all('a', attrs={'class': 'grouped_media_wrap'})))
        grouped_media_number_list = get_ids(grouped_media)

        grouped_posts_list = sorted(list(set(post_number_list) & set(grouped_media_number_list)), reverse=True)

        posts_id = posts
        posts_instances_list = create_TgPost(posts_id, 'undefined')

        photos_id = soup.find_all('a', attrs={'class': 'tgme_widget_message_photo_wrap'})
        photos_instances_list = create_TgPost(photos_id, 'photo')

        videos_id = soup.find_all('a', attrs={'class': 'tgme_widget_message_video_player'})
        video_instances_list = create_TgPost(videos_id, 'video')
        posts_list = list([])

        prev_group = 0
        for i in range(0, len(posts)):
            if post_number_list[i] in grouped_media_number_list:
                new_group = grouped_media_number_list.index(post_number_list[i])
                posts_list.append(['Grouped'])
                length = len(grouped_media_number_list[prev_group:new_group]) + 1

                for j in range (prev_group, prev_group+length):
                    local_id = grouped_media_number_list[j]
                    text = get_text(return_id_from_another_list(posts_instances_list, local_id))
                    if len(text) != 0:
                        text = text[0]
                    else:
                        text = ' '
                    posts_list[i].append(TgPost(grouped_media[j], grouped_media_number_list[j], get_type(grouped_media_number_list[j]), text))
                prev_group = new_group + 1
            else:
                posts_list.append(['Single', TgPost(posts[i], post_number_list[i], get_type(post_number_list[i]))])
        views = soup.find_all('span', attrs={'class': 'tgme_widget_message_views'})
        videos_content = soup.find_all('video', attrs={'class': 'tgme_widget_message_video'})
        messages_data = []
        for i in range(0, post_count):
            messages_data.append(posts[i].text)
        kwargs['message'] = []
        kwargs['message_views'] = []
        kwargs['message_time'] = []
        for i in range(0, post_count):
            inf = re.findall(r'\n{1,5}[\d\w\s\.]*\d\d:\d\d', messages_data[i])
            kwargs['message'].append(messages_data[i].split(inf[0])[0])
            kwargs['message_views'].append(re.findall(r'[\d\.K]+', inf[0])[0])
            kwargs['message_time'].append(re.findall(r'\d\d:\d\d', messages_data[i])[0])

        # Создаём папку и выкачиваем всю инфу о посте (текст, фото/видео)
        for item in posts_list:
            if item[0] == "Single":
                post_path = f'{item[1].id}_single'
                write_single_post(post_path, item)
            if item[0] == "Grouped":
                post_path = f'{item[len(item) - 1].id}_group'
                write_group_post(post_path, item)
            print(item)
    page.close()


_count = 1
video_instances_list = list()
photos_instances_list = list()
_SINGLE_MEDIA_LINK_PATTERN = re.compile(r'^https://t\.me/[^/]+/\d+\?single$')
_logger = logging.getLogger(__name__)
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'}
_info = None
_type = None

if __name__ == "__main__":
    while True:
        f = Figlet(font='slant')
        print(f.renderText('TG PARSER'))
        print('Введите имя тг-канала:', end='')
        name = input()
        photo_name = f'@{name}_photo.jpg'
        current_channel_path = f'@{name}_tg_parse'
        print('Путь сохранения: C:\\', end='')
        main_path = "C:\\" + input()
        print('post_count=', end='')
        post_count = 9
        get_info_about_tg()
        get_parsed_post(post_count=post_count)
        break

