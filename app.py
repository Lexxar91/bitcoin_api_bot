# from fastapi import FastAPI, HTTPException, Depends, status, Body, Path
import os

import fastapi
from dotenv import load_dotenv
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

import pydantic_models
from database import crud, models
from pydantic_models import (Admin, Token, TokenData, UserInDB, UserToCreate,
                             UserToUpdate)

load_dotenv()
api = fastapi.FastAPI()

# SECRET_KEY = config.SECRET_KEY
# ALGORITHM = config.ALGORITHM

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password_):
    return pwd_context.hash(password_)


def get_user(username: str | int):
    if username == config.USERNAME:
        return UserInDB(username=username, hashed_password=config.PASSWORD)
    return False


def authenticate_user(username: str | int, password_: str | int):
    # user = get_user(username)
    # if not user or verify_password(password_, config.PASSWORD):
    #     return False
    # return user
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password_, user.hashed_password):
        return False
    return user


def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = fastapi.Depends(oauth2_scheme)):
    credentials_exception = fastapi.HTTPException(
        status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get('sub')
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


@api.post('/token', response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = fastapi.Depends()):
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={'sub': user.username}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@api.get("/users/me/", response_model=Admin)
async def read_users_me(current_user: Admin = Depends(get_current_user)):
    return current_user


"""
ТЕПЕРЬ ДОБАВЛЯЕМ АРГУМЕНТ
current_user: Admin = Depends(get_current_user)
В КАЖДУЮ ФУНКЦИЮ С ОБРАБОТКОЙ ПУТИ,
ЧТОБЫ ДОСТУП К ФУНКЦИЯМ БЫЛ ТОЛЬКО
У АВТОРИЗОВАННОГО КЛИЕНТА
"""

# current_user: Admin = fastapi.Depends(get_current_user)


@api.get('/get_user_wallet/{user_id:int}')
@crud.db_session
def get_user_wallet(user_id):
    """
    Функция для получения кошелька юзера.
    по user_id: int
    :param current_user:
    :param user_id:
    :return:
    """
    return crud.get_wallet_info(crud.User[user_id].wallet)


@api.put('/user/{user_id}')
@crud.db_session
def update_user(user_id: int, user: UserToUpdate = fastapi.Body(),
                current_user: Admin = fastapi.Depends(get_current_user)):
    """
    Обновляем данные юзера.
    :param user_id:
    :param user:
    :param current_user:
    :return:
    """
    if user_id == user.id:
        return crud.update_user(user).to_dict()
    return False


@api.delete('/user/{user_id}')
@crud.db_session
def delete_user(user_id: int = fastapi.Path(),
                current_user: Admin = fastapi.Depends(get_current_user)):
    """
    Удаляем юзера.
    :param current_user:
    :param user_id:
    :return:
    """
    # if fastapi.Request.user != user_id:
    #     return False
    return crud.get_user_by_id(user_id).delete()


@api.post('/user/create')
def create_user(user: UserToCreate):
    """
    Создаем Юзера.
    :param user:
    :return:
    """
    return crud.create_user(
        tg_id=user.tg_ID,
        nick=user.nick if user.nick else None
    ).to_dict()


@api.get('/get_info_by_user_id/{user_id:int}')
@crud.db_session
def get_info_about_user(
        user_id,
        current_user: Admin = Depends(get_current_user)):
    """
    Получаем информацию по юзеру.
    :param current_user:
    :param user_id:
    :return:
    """
    return crud.get_user_info(crud.User[user_id])

# current_user: Admin = Depends(get_current_user)


@api.get('/get_user_balance_by_id/{user_id:int}')
@crud.db_session
def get_user_balance_by_id(user_id):
    """
    Получаем баланс юзера.
    :param current_user:
    :param user_id:
    :return:
    """
    crud.update_wallet_balance(crud.User[user_id].wallet)
    print(crud.User[user_id].wallet.balance)
    return crud.User[user_id].wallet.balance


@api.get('/get_total_balance')
@crud.db_session
def get_total_balance():
    """
    Получаем общий баланс.
    :return: balance
    """
    balance = 0.0
    crud.update_all_wallets()
    for user in crud.User.select()[:]:
        balance += user.wallet.balance
    return balance


@api.get('/users')
@crud.db_session
def get_users():
    """
    Получаем всех юзеров.
    :return:
    """
    return crud.get_all_users()


# current_user: Admin = Depends(get_current_user)
@api.get('/get_user_by_tg_id/{tg_id}')
@crud.db_session
def get_user_by_tg_id(tg_id: int):
    """
    Получаем юзера по id его Тelegram.
    :param current_user:
    :param tg_id:
    :return:
    """
    user = crud.get_user_info(crud.User.get(tg_ID=tg_id))
    return user

# current_user: Admin = Depends(get_current_user)


@api.post("/create_transaction/{user_id:int}")
@crud.db_session
def create_transaction(
        user_id,
        transaction: pydantic_models.CreateTransaction):
    """
    Создаем транзакцию.
    :param user_id:
    :param transaction:
    :param current_user:
    :return:
    """
    return crud.create_transaction(
        crud.get_user_by_id(user_id),
        transaction.amount_btc_without_fee,
        transaction.receiver_address
    )

# current_user: Admin = Depends(get_current_user)


@api.get('/get_user_transactions/{user_id}')
@crud.db_session
def get_transactions(user_id: int):
    """
    Получаем транзакции юзера.
    :param user_id:
    :param current_user:
    :return:
    """
    return crud.get_user_transactions(user_id)
