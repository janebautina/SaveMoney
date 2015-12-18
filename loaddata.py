from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Savings, Items, User

engine = create_engine('sqlite:///savemoneywithusers.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# --------------------------------------------------------------------------
User1 = User(name="Evgeniya Bautina", email="janebarinova@gmail.com",
             picture='http://pbs.twimg.com/media/B0yXek8CUAAUdRD.jpg')
session.add(User1)
session.commit()
saving1 = Savings(name="Sweets", user_id=1)
session.add(saving1)
session.commit()
# ---------------------------------------------------------------------------
saving2 = Savings(name="Shoes", user_id=1)
session.add(saving2)
session.commit()
# ---------------------------------------------------------------------------
saving3 = Savings(name="Yarn", user_id=1)
session.add(saving3)
session.commit()
# ----------------------------------------------------------------------------
saving4 = Savings(name="Books", user_id=1)
session.add(saving4)
session.commit()
# -----------------------------------------------------------------------------
