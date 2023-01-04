import os

import pydantic_models
import requests
from dotenv import load_dotenv
from pydantic import ValidationError

load_dotenv()

api_url = os.getenv('API_URL')
# # создаем заголовок в котором указываем, что тип контента - форма.
# form_headers = {"Content-Type": "application/x-www-form-urlencoded"}
#
# # когда мы отправляем данные в виде формы,
# # то присваиваем значения параметрам через равно,
# # а перечисляем их через амперсанд.
# payload = 'username=admin&password=admin'
# raw_token = requests.post(
#     api_url + "/token",
#     headers=form_headers,
#     data=payload
# )
#
# # получаем словарь из ответа сервера.
# token = raw_token.json()
#
#
# # создаем экземпляр сессии.
# requests = requests.requests()
#
# # добавляем хедеры с токеном авторизации, благодаря чему API будет понимать кто мы и возвращать нужные нам ответы.
# requests.headers = {
#     "accept": "application/json",
#     "Authorization": "Bearer" + token["access_token"]
# }


def update_user(user: dict):
    """Обновляем юзера"""
    # валидируем данные о юзере, так как мы не под декоратором fastapi и это нужно делать вручную
    user = pydantic_models.UserToUpdate.validate(user)
    response = requests.put(f'{api_url}/user/{user.id}', data=user.json())
    try:
        return response.json()
    except ValidationError as er:
        print(er)


def delete_user(user_id: int):
    """
    Удаляем юзера
    :param user_id:
    :return:
    """
    return requests.delete(f'{api_url}/user/{user_id}').json()


def create_user(user: pydantic_models.UserToCreate):
    """
    Создаем Юзера
    :param user:
    :return:
    """
    user = pydantic_models.UserToCreate.validate(user)
    return requests.post(f'{api_url}/user/create', data=user.json()).json()


def get_info_about_user(user_id):
    """
    Получаем инфу по юзеру
    :param user_id:
    :return:
    """
    return requests.get(f'{api_url}/get_info_by_user_id/{user_id}').json()


def get_user_balance_by_id(user_id):
    """
    Получаем баланс юзера
    :param user_id:
    :return:
    """
    response = requests.get(f'{api_url}/get_user_balance_by_id/{user_id}')
    try:
        return float(response.text)
    except:
        return f'Error: Not a Number\nResponse: {response.text}'


def get_total_balance():
    """
    Получаем общий баланс

    :return:
    """
    response = requests.get(f'{api_url}/get_total_balance')
    try:
        return float(response.text)
    except:
        return f'Error: Not a Number\nResponse: {response.text}'


def get_users():
    """
    Получаем всех юзеров
    :return list:
    """
    return requests.get(f"{api_url}/users").json()


def get_user_wallet_by_tg_id(tg_id):
    """
    Получаем кошелек юзера по id аккаунта ТГ
    :param tg_id:
    :return:
    """
    user_dict = get_user_by_tg_id(tg_id)
    print(user_dict)
    return requests.get(f"{api_url}/get_user_wallet/{user_dict['id']}").json()


def get_user_by_tg_id(tg_id):
    """
    Получаем юзера по айди его ТГ
    :param tg_id:
    :return:
    """
    return requests.get(f"{api_url}/get_user_by_tg_id/{tg_id}").json()


def create_transaction(tg_id, receiver_address: str, amount_btc_without_fee: float):
    """
    Функция для создания транзакции
    :param tg_id:
    :param receiver_address:
    :param amount_btc_without_fee:
    :return:
    """
    user_dict = get_user_by_tg_id(tg_id)
    payload = {
        'receiver_address': receiver_address,
        'amount_btc_without_fee': amount_btc_without_fee
    }
    response = requests.post(f"{api_url}/create_transaction/{user_dict['id']}", json=payload)
    return response.text


def get_user_transactions(user_id: int):
    """
    Функция для получений транзакций юзера
    :param user_id:
    :return:
    """
    response = requests.get(f"{api_url}/get_user_transactions/{user_id}")

    try:
        response.json()
    except Exception as e:
        return e
