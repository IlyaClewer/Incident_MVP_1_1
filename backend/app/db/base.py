from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

from app.db.models import cards
from app.db.models import diagnoses
from app.db.models import events
from app.db.models import experts
from app.db.models import logs