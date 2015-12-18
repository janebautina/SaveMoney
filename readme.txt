
Welcome to SaveMoney!
 
 This application that provides a list of savings options within a variety 
 of savings' items as well as provide a user registration and authentication 
 system. Onle registered users will have the ability to post, edit and delete 
 their own savings and savings items. Also the application provides 
 a JSON endpoint, at the very least.

Running instructions:
1. Install Vagrant and VirtualBox
2. Install python 3.0, SQLAlchemy, werkzeug 0.8.3, flask 0.9, Flask-Login 0.1.3
2. Clone the SaveMoney
3. Run and log into VM
4. Run application within the VM:
    python database_setup.py
    python loaddata.py 
    python savings.py
5. Access and test your application by visiting http://localhost:8080 locally



