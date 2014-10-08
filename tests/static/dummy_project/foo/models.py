from sqlalchemy import Column, String, Integer, Float
from anflow.db import models
from anflow.core.wrappers import Datum

class MyModel(models.Model):

    input_stream = [Datum({'foo': str(i), 'bar': 2 * i}, i**2)
                    for i in range(10)]
    foo = Column(String)
    bar = Column(Float)
    some_var = Column(Integer)
    
    @staticmethod
    def main(data, foo, bar, some_var):
        return data // some_var
