"""Import every ORM model so SQLAlchemy's mapper registry is complete.

Import this module for its side effects anywhere that needs fully-configured
mappers *without* importing the whole app (e.g. Alembic and standalone scripts).
When you add a module with models, add its import here.
"""

from app.modules.auth import models as auth_models  # noqa: F401
from app.modules.users import models as user_models  # noqa: F401
