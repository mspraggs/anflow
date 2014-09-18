from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from datetime import datetime
import os
try:
    import cPickle as pickle
except ImportError:
    import pickle

from sqlalchemy import and_, asc, desc

from anflow.conf import settings
from anflow.db.history import History
from anflow.utils.debug import debug_message



def _recurse_delete(model_class, ids):
    from anflow.db.models import Model
    query = settings.session.query(model_class).filter(model_class.id.in_(ids))
    query.delete(synchronize_session=False)
    settings.session.expire_all()
    for base in model_class.__bases__:
        if issubclass(base, Model):
            _recurse_delete(base, ids)

class Datum(object):
    def __init__(self, params, data, central_value=None, error=None,
                 filename=None, timestamp=None):
        self._params = set(params.keys())
        self.value = data
        self._filename = filename
        self.central_value = central_value
        self.error = error
        for key, value in params.items():
            setattr(self, key, value)

        try:
            self.timestamp = (timestamp or
                              datetime.fromtimestamp(os.path
                                                     .getmtime(filename)))
        except (TypeError, OSError) as e:
            debug_message(e)
            self.timestamp = None
            
    def paramsdict(self):
        return dict([(key, getattr(self, key)) for key in self._params])
    
    def __getattribute__(self, attr):
        return object.__getattribute__(self, attr)
    
    def __setattr__(self, attr, value):
        non_params = ["value", "central_value", "error", "timestamp"]
        if not attr.startswith('_') and attr not in non_params:
            self._params.add(attr)
        return object.__setattr__(self, attr, value)
    
    def delete(self):
        os.unlink(self._filename)

    def save(self):
        try:
            os.makedirs(os.path.dirname(self._filename))
        except OSError as e:
            debug_message(e)
        save_object = (self.paramsdict(), self.value, self.central_value,
                       self.error)        
        with open(self._filename, 'wb') as f:
            pickle.dump(save_object, f, 2)
            
    @classmethod
    def load(cls, filename):
        with open(filename, 'rb') as f:
            params, value, central_value, error = pickle.load(f)
        return cls(params, value, central_value, error, filename)
    
    def __repr__(self):
        output = object.__repr__(self) + "\n"
        output += "Datum Parameters\n"
        output += "================\n"
        output += "\n".join(["{}: {}".format(key, value)
                             for key, value in self.paramsdict().items()])
        return output

class DataSet(object):

    def __init__(self, query, model_class):

        self.query = (query if query._entities
                      else query.add_entity(model_class))            
        self.model_class = model_class

    def all(self):
        return self.query.all()

    def filter(self, **kwargs):
        """Filter the data"""

        binops = []
        for key, value in kwargs.items():
            if key.endswith('__gt'):
                binop = getattr(self.model_class, key[:-4]) > value
            elif key.endswith('__gte'):
                binop = getattr(self.model_class, key[:-5]) >= value
            elif key.endswith('__lt'):
                binop = getattr(self.model_class, key[:-4]) < value
            elif key.endswith('__lte'):
                binop = getattr(self.model_class, key[:-5]) <= value
            elif key.endswith('__aprx'):
                absval = value if value >= 0 else -value
                attr = getattr(self.model_class, key[:-6])
                abs_lte = attr - value <= 1e-7
                abs_gte = attr - value >= -1e-7
                rel_lte = attr - value <= 1e-5 * absval
                rel_gte = attr - value >= -1e-5 * absval
                binop = and_(abs_lte, abs_gte, rel_lte, rel_gte)
            else:
                binop = getattr(self.model_class, key) == value
            binops.append(binop)
        new_query = self.query.filter(*binops)
        return DataSet(new_query, self.model_class)

    def order_by(self, *args):

        sqlalchemy_args = []
        for arg in args:
            if arg.startswith('-'):
                attr = arg[1:]
                order = desc
            else:
                attr = arg
                order = asc
            sqlalchemy_args.append(order(getattr(self.model_class, attr)))
        return DataSet(self.query.order_by(*sqlalchemy_args), self.model_class)

    def latest(self):

        history = (settings.session.query(History)
                   .order_by(desc(History.end_time)))
        if not history.first():
            return self
        else:
            return self.history(-1)

    def history(self, id):
        """Return the query for set of data that was saved during the specified
        run. If no data was saved during the specified run, return the query
        for the next most recent set of data saved."""

        num_runs = settings.session.query(History).count()
        history = (settings.session.query(History)
                   .order_by(desc(History.end_time)).all())
        if id < 1:
            id = history[id].id

        results = []
        while not results and id > 0:
            run = (settings.session.query(History).filter(History.id == id)
                   .first())
            start = run.start_time
            end = run.end_time
            new_query = self.filter(timestamp__gte=start,
                                    timestamp__lte=end).query
            results = new_query.all()
            id -= 1

        return DataSet(new_query, self.model_class)

    def first(self):
        return self.query.first()
                                   
    def delete(self, *args, **kwargs):
        from anflow.db.models import Model
        ids = [item.id for item in self.query]
        _recurse_delete(self.model_class, ids)
        settings.session.commit()

    def __iter__(self):
        return self.query.__iter__()
