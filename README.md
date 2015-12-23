# About SaveMoney

  SaveMoney is an app with a goal to help people reduce habitual spending on 
unhealthy or nonessential purchases, and spend that money on things they 
really want or need instead. For example, someone can be addicted to sweets 
and always order desserts in restaurants, but as we all know sugar is unhealthy. 
Someone else may be addicted to coffee, spending $10 at Starbucks every day. 
By savings these small amounts of money over time, users would be able 
to achieve some of their dreams, such as buying a tour package to Hawaii 
or financing their education.
 
This application that provides a list of savings options with a variety 
of savings' items as well as provide a user registration and authentication 
system. Onle registered users will have the ability to post, edit and delete 
their own savings and savings items. Also the application provides 
a JSON endpoint, at the very least.

# Getting Started

1. Install Vagrant and VirtualBox
2. Install software listed in requirements
3. Clone the SaveMoney repository
4. In terminal navigate to SaveMoney directory
5. Type the command to run VM: vagrant up
6. Type the commant to log into VM: vagrant ssh
7. Run application within the VM:
 - python database_setup.py
 - python loaddata.py
 - python savings.py
8. Access and test your application by visiting http://localhost:8080 locally

# Requirements
 - Python 3.0
 - Werkzeug 0.8.3
 - Flask 0.9
 - Flask-Login 0.1.3
 - SQLAlchemy 0.8.4



   
