import cli.run
import cli.adduser
import cli.a
import cli.s
import cli.j

__all__ = ["modules"]

modules = {
        "run" : run.run,
        "adduser" :  adduser.adduser,
        "a" : a.a,
        "s" : s.s,
        "j" : j.j
    }
