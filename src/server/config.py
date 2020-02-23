# src/server/config.py

import os
basedir = os.path.abspath(os.path.dirname(__file__))
postgres_local_base = 'postgresql://postgres:postgres@localhost:5431/'
database_name = 'devdb'


class BaseConfig:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'sm#@.qlQox/SA/VtA5.Qt{o86/89BHG%l-H#tbU/5\gR]Iq{vmP-a7S.u!Qofk<')
    SECRET_REFRESH_KEY = os.getenv('SECRET_REFRESH_KEY', 'npX#l.9;G9UO}:ZisGsm#r)c<"~G`YVCO)O>Sv&}Lz!&.o>oh#Wk5zy`GVVZdW`')
    DEBUG = False
    BCRYPT_LOG_ROUNDS = 13
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True
    BCRYPT_LOG_ROUNDS = 4
    SQLALCHEMY_DATABASE_URI = postgres_local_base + database_name


class TestingConfig(BaseConfig):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    BCRYPT_LOG_ROUNDS = 4
    SQLALCHEMY_DATABASE_URI = postgres_local_base + database_name
    PRESERVE_CONTEXT_ON_EXCEPTION = False


class ProductionConfig(BaseConfig):
    """Production configuration."""
    SECRET_KEY = 'my_precious'
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = postgres_local_base + database_name
