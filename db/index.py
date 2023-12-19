from sqlalchemy import create_engine, Column, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import threading


class SingletonInstance:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(SingletonInstance, cls).__new__(cls)
                cls._instance.__initialized = False
        return cls._instance

    def __init__(self, *args, **kwargs):
        with self._lock:
            if not getattr(self, '__initialized', False):
                self.__initialized = True
                self.initialize(*args, **kwargs)

    def initialize(self, *args, **kwargs):
        pass  # Override this method in subclasses if needed


class DB(SingletonInstance):
    def initialize(self):
        self._engine = create_engine(
            "sqlite:///chzzk_data.db",
            echo=False
        )
        self._Base = declarative_base()
        self._Session = sessionmaker(
            autocommit=False, autoflush=False, bind=self._engine)

    @property
    def Base(self):
        return self._Base

    def create_all(self):
        self._Base.metadata.create_all(self._engine)

    def getSession(self):
        return self._Session()
