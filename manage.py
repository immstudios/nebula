#!/usr/bin/env python
#
# Nebula commandline administration tool
#

from nebula import *


print "\nCreate new nebula user\n"

login = raw_input("Login: ").strip()
password = raw_input("Password: ").strip()
is_admin = raw_input("Is it admin (yes/no): ").strip()

u = User()
u["login"] = u["full_name"] = login
u["is_admin"] = "true" if is_admin == "yes" else ""
u.set_password(password)
u.save()
print "\nUser created"

