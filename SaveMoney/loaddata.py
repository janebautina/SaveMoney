from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Savings, Items, User

#engine = create_engine('postgresql://catalog:catalogpwd@127.0.0.1/savemoney')
engine = create_engine('postgresql://savemoneyadmin:savemoneyadminpwd@127.0.0.1:5432/savemoney')
#engine = create_engine('postgresql://savemoneyadmin:savemoneyadminpwd@127.0.0.1/savemoney')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# --------------------------------------------------------------------------
session.commit()
user1 = User(name="Evgeniya", email="janebarinova@gmail.com")
session.add(user1)
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
