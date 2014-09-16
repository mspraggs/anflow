from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from sqlalchemy import desc

from anflow.conf import settings
from anflow.db.history import History



def main(argv):
    query = settings.session.query(History)

    history = query.order_by(desc(History.end_time)).all()

    print("Run History")
    print("===========")

    row_format = "{:<4}{:<21}{:<21}{:<8}{:<7}{:<13} {}"
    header = row_format.format('id', 'start', 'end', 'models', 'views',
                               'dependencies', 'studies')
    print(header)
    print('-' * len(header))
    for run in history:
        start_format = run.start_time.strftime("%H:%M:%S %d/%m/%Y")
        end_format = run.end_time.strftime("%H:%M:%S %d/%m/%Y")
        studies_format = ", ".join(run.studies)
        row = [run.id, start_format, end_format, run.run_models.__repr__(),
               run.run_views.__repr__(), run.run_dependencies.__repr__(),
               studies_format]
        print(row_format.format(*row))
