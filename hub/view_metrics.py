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
        boot_times = []
        run_times = []
        last_seens = []
        db.query("SELECT hostname, last_seen, status FROM hosts")
        for hostname, last_seen, status in db.fetchall():
            if "boot_time" in status:
                boot_times.append([hostname, status["boot_time"]])
            if "run_time" in status:
                run_times.append([hostname, status["run_time"]])
            last_seens.append([hostname, last_seen])
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
        for hostname, value in boot_times:
            result += "nebula_uptime_seconds{{site_name=\"{}\", hostname=\"{}\"}} {}\n".format(
                    config["site_name"], hostname, int(time.time() - value)
                    )

        for hostname, value in run_times:
            result += "nebula_runtime_seconds{{site_name=\"{}\", hostname=\"{}\"}} {}\n".format(
                    config["site_name"], hostname, int(time.time() - value)
                    )

        for hostname, value in last_seens:
            result += "nebula_inactive_seconds{{site_name=\"{}\", hostname=\"{}\"}} {}\n".format(
                    config["site_name"], hostname, max(0,int(time.time() - value))
                    )

        for hostname, value in cpu:
            result += "nebula_cpu_usage{{site_name=\"{}\", hostname=\"{}\"}} {}\n".format(
                    config["site_name"], hostname, value
                    )

        for hostname, total, free in mem:
            result += "nebula_memory_bytes_total{{site_name=\"{}\", hostname=\"{}\"}} {}\n".format(
                    config["site_name"], hostname, total
                    )
            result += "nebula_memory_bytes_free{{site_name=\"{}\", hostname=\"{}\"}} {}\n".format(
                    config["site_name"], hostname, free
                    )
            result += "nebula_memory_usage{{site_name=\"{}\", hostname=\"{}\"}} {}\n".format(
                    config["site_name"], hostname, 100*((total-free)/total)
                    )

        for hostname, total, free in swp:
            result += "nebula_swap_bytes_total{{site_name=\"{}\", hostname=\"{}\"}} {}\n".format(
                    config["site_name"], hostname, total
                    )
            result += "nebula_swap_bytes_free{{site_name=\"{}\", hostname=\"{}\"}} {}\n".format(
                    config["site_name"], hostname, free
                    )
            result += "nebula_swap_usage{{site_name=\"{}\", hostname=\"{}\"}} {}\n".format(
                    config["site_name"], hostname, 100*((total-free)/total)
                    )

        for hostname, total, free in rfs:
            result += "nebula_rootfs_bytes_total{{site_name=\"{}\", hostname=\"{}\"}} {}\n".format(
                    config["site_name"], hostname, total
                    )
            result += "nebula_rootfs_bytes_free{{site_name=\"{}\", hostname=\"{}\"}} {}\n".format(
                    config["site_name"], hostname, free
                    )
            result += "nebula_rootfs_usage{{site_name=\"{}\", hostname=\"{}\"}} {}\n".format(
                    config["site_name"], hostname, 100*((total-free)/total)
                    )

        for id_storage in stor:
            title, total, free = stor[id_storage]
            result += "nebula_storage_bytes_total{{site_name=\"{}\", id=\"{}\", title=\"{}\"}} {}\n".format(
                    config["site_name"], id_storage, title, total
                    )
            result += "nebula_storage_bytes_free{{site_name=\"{}\", id=\"{}\", title=\"{}\"}} {}\n".format(
                    config["site_name"], id_storage, title, free
                    )
            result += "nebula_storage_usage{{site_name=\"{}\", id=\"{}\", title=\"{}\"}} {}\n".format(
                    config["site_name"], id_storage, title, 100*((total-free)/total)
                    )

        for user in request_stats:
            for method in request_stats[user]:
                result += "nebula_api_requests{{site_name=\"{}\", user=\"{}\", method=\"{}\"}} {}\n".format(
                    config["site_name"], user, method, request_stats[user][method]
                    )


        db.query("select status, count(status) from jobs group by status;")
        for status, count in db.fetchall():
            status_label = [
                        "Pending",
                        "In progress",
                        "Completed",
                        "Failed",
                        "Aborted",
                        "Restart",
                        "Skipped"
                    ][status]
            result += "nebula_jobs{{site_name=\"{}\", status=\"{}\", status_label=\"{}\"}} {}\n".format(
                    config["site_name"],
                    status, status_label, count
                    )


        db.query("SELECT id, service_type, host, title, autostart, state, last_seen FROM services")
        for id, stype, hostname, title, autostart, state, last_seen in db.fetchall():
            result += "nebula_service_state{{site_name=\"{}\", hostname=\"{}\", id=\"{}\", title=\"{}\", service_type=\"{}\"}} {}\n".format(
                        config["site_name"],
                        hostname,
                        id,
                        title,
                        stype,
                        state
                    )
            result += "nebula_service_inactive_seconds{{site_name=\"{}\", hostname=\"{}\", id=\"{}\", title=\"{}\", service_type=\"{}\"}} {}\n".format(
                        config["site_name"],
                        hostname,
                        id,
                        title,
                        stype,
                        max(0,int(time.time() - last_seen))
                    )


        self.is_raw = True
        self.body = result
        self["mime"] = "text/txt"


