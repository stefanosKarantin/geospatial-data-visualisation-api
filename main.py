# manage.py


import os
import unittest
import coverage

from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

COV = coverage.coverage(
    branch=True,
    include='src/*',
    omit=[
        'src/tests/*',
        'src/server/config.py',
        'src/server/*/__init__.py'
    ]
)
COV.start()

from src.server import app, db, models

db.init_app(app)

if __name__ == '__main__':
    print(os.getenv('ENVIRONMENT'), flush=True)
    app.run(host="0.0.0.0", port=5000, debug=False)