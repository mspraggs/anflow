from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from sqlalchemy import and_, asc, desc
from sqlalchemy.sql import false

from anflow.conf import settings
from anflow.db.models.history import History



def _recurse_delete(model_class, ids):
    from anflow.db.models import Model
    query = settings.session.query(model_class).filter(model_class.id.in_(ids))
    query.delete(synchronize_session=False)
    settings.session.expire_all()
    for base in model_class.__bases__:
        if issubclass(base, Model):
            _recurse_delete(base, ids)

class DataSet(object):

    def __init__(self, query, model_class):

        self.query = (query if query._entities
                      else query.add_entity(model_class))            
        self.model_class = model_class

    def all(self):
        return self.query.all()

    def count(self):
        return self.query.count()

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

    def latest(self, orphans_only=False):

        history = (settings.session.query(History)
                   .order_by(desc(History.end_time)))
        if not history.first():
            return self
        else:
            end = history.first().end_time
            orphans = self.filter(timestamp__gte=end)
            if len(orphans.all()) > 0 or orphans_only:
                return orphans
            else:
                return self.history(-1)

    def history(self, index, exact_match=False):
        """Return the query for set of data that was saved during the specified
        run. If no data was saved during the specified run and exact_match is
        False, return the query for the next most recent set of data saved."""

        num_runs = History.data.count()
        index = index % num_runs
        if num_runs == 0:
            return DataSet(self.query.filter(false()), self.model_class)

        ids = [datum.id for datum in History.data.order_by('end_time')]

        result = []
        while not result and index > -1:
            run = History.data.filter(id=ids[index]).first()
            new_dataset = self.filter(history=run)
            if exact_match:
                break
            result = new_dataset.all()
        return new_dataset

    def first(self):
        return self.query.first()
                                   
    def delete(self, *args, **kwargs):
        ids = [item.id for item in self.query]
        _recurse_delete(self.model_class, ids)
        settings.session.commit()

    def update(self, values, synchronize_session='evaluate'):
        """Updates the objects specified by the query"""
        new_query = self.query.update(values, synchronize_session)
        settings.session.commit()

    def __iter__(self):
        return self.query.__iter__()
