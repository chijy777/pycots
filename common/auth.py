"""
COT Service

Author: Tony Chi
Updated at: 2018-06
Content : messaging utility module 
"""
# -*- coding: utf-8 -*-
import os.path
import string
import configparser
from collections import namedtuple
from random import choice
from cryptography.fernet import Fernet

DEFAULT_KEY_FILENAME = "{}/.pyaiot/keys".format(os.path.expanduser("~"))

Keys = namedtuple('Keys', ['private', 'secret'])

def generate_secret_key():
    """
    用字母和数字生成长度为32的随机密钥.
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(choice(alphabet) for i in range(32))


def generate_private_key():
    """
    生成base64编码的32字节私人密钥.
    """
    return Fernet.generate_key().decode()


def write_keys_to_file(filename, keys):
    """
    将秘钥写入文件名.
    """
    config = configparser.ConfigParser()
    config['keys'] = {'secret': keys.secret, 'private': keys.private}
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename), mode=0o700)

    with open(filename, 'w') as f:
        config.write(f)


def check_key_file(filename=DEFAULT_KEY_FILENAME):
    """
    校验文件是否存在，且格式正确.
    """
    filename = os.path.expanduser(filename)
    if not os.path.isfile(filename):
        raise ValueError("Key file provided doesn't exists: '{}'".format(filename))

    config = configparser.ConfigParser()
    config.read(filename)

    if (not config.has_option('keys', 'secret') or not config.has_option('keys', 'private')):
        raise ValueError("Invalid key file provided: '{}'".format(filename))

    return Keys(
        private=config['keys']['private'],
        secret=config['keys']['secret']
    )


def verify_auth_token(token, keys):
    """
    校验授权令牌是否有效.
    """
    return (
        Fernet(keys.private.encode()).decrypt(token.encode()) == keys.secret.encode()
    )


def auth_token(keys):
    """
    从给定的私钥和密钥，生成一个令牌.
    """
    return Fernet(keys.private.encode()).encrypt(keys.secret.encode())
