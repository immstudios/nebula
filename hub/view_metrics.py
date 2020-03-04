from nebula import *
from cherryadmin.stats import *
from cherryadmin import CherryAdminRawView

class ViewMetrics(CherryAdminRawView):
    def auth(self):
        return True

    def build(self, *args, **kwargs):
        db = DB()
        stor = {}
        cpu = []
        mem = []
        swp = []
        rfs = []
        db.query("SELECT hostname, last_seen, status FROM hosts")
        for hostname, last_seen, status in db.fetchall():
            if "cpu" in status:
                cpu.append([hostname, status["cpu"]])
            if status.get("mem", [0,0])[0]:
                mem.append([hostname, status["mem"][0], status["mem"][1]])
            if status.get("swp", [0,0])[0]:
                swp.append([hostname, status["swp"][0], status["swp"][1]])
            if status.get("rfs", [0,0])[0]:
                rfs.append([hostname, status["rfs"][0], status["rfs"][1]])
            for storage in status.get("stor",[]):
                if storage["id"] in stor:
                    continue
                stor[storage["id"]] = storage["title"], storage["total"], storage["free"]

        result = ""
        result += "#HELP nebula_cpu Nebula node CPU usage\n"
        result += "#TYPE nebula_cpu gauge\n"
        for hostname, value in cpu:
            result += "nebula_cpu{{site_name=\"{}\", hostname=\"{}\"}} {}\n".format(
                    config["site_name"], hostname, value
                    )

        result += "#HELP nebula_mem Nebula node memory usage\n"
        result += "#TYPE nebula_mem gauge\n"
        for hostname, total, free in mem:
            result += "nebula_mem{{site_name=\"{}\", hostname=\"{}\", mode=\"total\"}} {}\n".format(
                    config["site_name"], hostname, total
                    )
            result += "nebula_mem{{site_name=\"{}\", hostname=\"{}\", mode=\"free\"}} {}\n".format(
                    config["site_name"], hostname, free
                    )
            result += "nebula_mem{{site_name=\"{}\", hostname=\"{}\", mode=\"usage\"}} {}\n".format(
                    config["site_name"], hostname, 100*((total-free)/total)
                    )

        if swp:
            result += "#HELP nebula_swp Nebula node swap usage\n"
            result += "#TYPE nebula_swp gauge\n"
            for hostname, total, free in swp:
                result += "nebula_swp{{site_name=\"{}\", hostname=\"{}\", mode=\"total\"}} {}\n".format(
                        config["site_name"], hostname, total
                        )
                result += "nebula_swp{{site_name=\"{}\", hostname=\"{}\", mode=\"free\"}} {}\n".format(
                        config["site_name"], hostname, free
                        )
                result += "nebula_swp{{site_name=\"{}\", hostname=\"{}\", mode=\"usage\"}} {}\n".format(
                        config["site_name"], hostname, 100*((total-free)/total)
                        )

        if rfs:
            result += "#HELP nebula_rfs Nebula node root filesystem usage\n"
            result += "#TYPE nebula_rfs gauge\n"
            for hostname, total, free in rfs:
                result += "nebula_rfs{{site_name=\"{}\", hostname=\"{}\", mode=\"total\"}} {}\n".format(
                        config["site_name"], hostname, total
                        )
                result += "nebula_rfs{{site_name=\"{}\", hostname=\"{}\", mode=\"free\"}} {}\n".format(
                        config["site_name"], hostname, free
                        )
                result += "nebula_rfs{{site_name=\"{}\", hostname=\"{}\", mode=\"usage\"}} {}\n".format(
                        config["site_name"], hostname, 100*((total-free)/total)
                        )

        result += "#HELP nebula_storage Nebula storage usage\n"
        result += "#TYPE nebula_storage gauge\n"
        for id_storage in stor:
            title, total, free = stor[id_storage]
            result += "nebula_stor{{site_name=\"{}\", id=\"{}\", title=\"{}\", mode=\"total\"}} {}\n".format(
                    config["site_name"], id_storage, title, total
                    )
            result += "nebula_stor{{site_name=\"{}\", id=\"{}\", title=\"{}\", mode=\"free\"}} {}\n".format(
                    config["site_name"], id_storage, title, free
                    )
            result += "nebula_stor{{site_name=\"{}\", id=\"{}\", title=\"{}\", mode=\"usage\"}} {}\n".format(
                    config["site_name"], id_storage, title, 100*((total-free)/total)
                    )

        result += "#HELP nebula_api_requests Nebula API requests\n"
        result += "#TYPE nebula_api_requests counter\n"
        for user in request_stats:
            for method in request_stats[user]:
                result += "nebula_api_requests{{site_name=\"{}\", user=\"{}\", method=\"{}\"}} {}\n".format(config["site_name"], user, method, request_stats[user][method])


        result += "#HELP nebula_jobs Nebula jobs\n"
        result += "#TYPE nebula_jobs gauge\n"
        db.query("select status, count(status) from jobs group by status;")
        for status, count in db.fetchall():
            status_label = [
                        "pending",
                        "in_progress",
                        "completed",
                        "failed",
                        "aborted",
                        "restart",
                        "skipped"
                    ][status]
            result += "nebula_jobs{{site_name=\"{}\", status=\"{}\", status_label=\"{}\"}} {}\n".format(
                    config["site_name"],
                    status, status_label, count
                    )

        self.is_raw = True
        self.body = result
        self["mime"] = "text/txt"


