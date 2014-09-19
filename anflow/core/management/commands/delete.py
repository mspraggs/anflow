from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

import sys

from argparse import ArgumentParser

from anflow.db.history import History
from anflow.db.models import CachedData
from anflow.conf import settings
from anflow.core.management.commands.run import gather_models
from anflow.utils.logging import logger



def main(argv):

    log = logger()

    parser = ArgumentParser()
    parser.add_argument('--cache', dest='clear_cache', action='store_true')
    parser.add_argument('--run-ids', dest='run_ids', action='store')
    parser.add_argument('--studies', dest='studies', action='store')
    parser.set_defaults(clear_cache=False)
    args = parser.parse_args(argv)

    if not args.studies:
        studies = []
    else:
        studies = (settings.ACTIVE_STUDIES
                   if args.studies == 'all'
                   else args.studies.split(","))
    ids = (settings.session.query(History.id).all()
           if args.run_ids == 'all'
           else [int(i) for i in args.run_ids.split()])

    confirmation = raw_input("This action cannot be undone. Are you sure? "
                             "[yes/no] ")
    if confirmation != "yes":
        sys.exit()

    models = gather_models(studies)
    
    for id in ids:
        for model in models:
            log.info("Deleting data for model {} and run id {}"
                     .format(model.__name__, id))
            model.data.history(id, exact_match=True).delete()
        if args.clear_cache:
            log.info("Deleting cached data for run id {}".format(id))
            CachedData.data.history(id, exact_match=True).delete()
        log.info("Erasing history entry with id {}".format(id))
        settings.session.query(History).filter(History.id == id).delete()
        settings.session.commit()

    log.info("Selected models erased from database")
