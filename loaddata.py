from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Savings, Items

engine = create_engine('sqlite:///savemoney.db')
Base.metadata.bind = engine 
DBSession = sessionmaker(bind=engine)
session = DBSession()


#-------------------------------------------------------------------------
saving1 = Savings(name = "Sweets")
session.add(saving1)
session.commit()

Item1_1 = Items(name = "Black Forest Cake", description = "Piece of choco cake", price = 7.50 , savings = saving1)

session.add(Item1_1)
session.commit()
Item1_2 = Items(name = "Banana Bread", description = "Piece of babana bread in Sturbacks", price = 5.30 , savings = saving1)
session.add(Item1_2)
session.commit()
#---------------------------------------------------------------------------
saving2 = Savings(name = "Shoes")
session.add(saving2)
session.commit()

Item2_1 = Items(name = "Dior gladiator sandals",  description = "Dior gladiator in Macis", price = 2000.00 , savings = saving2)
session.add(Item2_1)
session.commit()
Item2_2 = Items(name = "Christian Louboutin",  description = "Christian Louboutin from amazon", price = 3500.00 , savings = saving2)
session.add(Item2_2)
session.commit()
#---------------------------------------------------------------------------
saving3 = Savings(name = "Yarn")
session.add(saving3)
session.commit()
Item3_1 = Items(name = "Happy Cotton", description = "Happy Cotton at woolandgang", price = 15.00 , savings = saving3)
session.add(Item3_1)
session.commit()
Item3_2 = Items(name = "Alpaca super wool", description = "Alpaka super wool from woolandthegand", price = 200.00 , savings = saving3)
session.add(Item3_2)
session.commit()
#---------------------------------------------------------------------------
saving4 = Savings(name = "Books")
session.add(saving4)
session.commit()
Item4_1 = Items(name = "Super Sexy Diet",  description = "Super Sexy Diet from amazon", price = 56.00 , savings = saving4)
session.add(Item4_1)
session.commit()
Item4_2 = Items(name = "Linux", description = "Linux book from amazon", price = 70.00 , savings = saving4)
session.add(Item4_2)
session.commit()
#---------------------------------------------------------------------------
