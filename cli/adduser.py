from .common import *

def adduser(*args):
    print
    try:
        login = raw_input("Login: ").strip()
        password = raw_input("Password: ").strip()
        is_admin = raw_input("Is it admin (yes/no): ").strip()
    except KeyboardInterrupt:
        print
        logging.warning("Interrupted by user")
        sys.exit(0)
    u = User()
    u["login"] = u["full_name"] = login
    u["is_admin"] = 1 if is_admin == "yes" else 0
    u.set_password(password)
    u.save()
    print
    logging.goodnews("User created")
