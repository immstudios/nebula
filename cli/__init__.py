import cli.run
import cli.adduser
import cli.passwd
import cli.a
import cli.s
import cli.j

__all__ = ["modules"]

modules = {
        "run" : run.run,
        "adduser" :  adduser.adduser,
        "passwd" :  passwd.passwd,
        "a" : a.a,
        "s" : s.s,
        "j" : j.j
    }
