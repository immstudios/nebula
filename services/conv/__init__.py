from nx import *
from nx.services import BaseService
from nx.jobs import Job
from nx.objects import Asset

from encoders import Ffmpeg, Ftp

FORCE_INFO_EVERY = 20

encoders = {
    "ffmpeg" : Ffmpeg,
    "ftp" : Ftp
}



class Service(BaseService):
    def on_init(self):
        agent_type = "conv"
        id_service = self.id_service
        self.allowed_actions = {}
        db = DB()
        db.query("UPDATE nx_jobs set id_service=0, progress=-1, retries=0, stime=0, etime=0, message='Restart requested after service crash.' WHERE id_service=%s AND progress > -1", [id_service])
        db.commit()
        db.query("SELECT id_action, title, config FROM nx_actions ORDER BY id_action")
        for id_action, title, config in db.fetchall():
            try:
                config = ET.XML(config)
            except:
                logging.error("Unable to parse '{}' action configuration".format(title))
                continue

            try:
                svc_cond = config.find("on").text()
            except:
                match = True
            else:
                if not svc_cond:
                    continue

                match = False
                if eval(svc_cond):
                    match = True

            if not match:
                continue

            logging.debug("Registering action {}".format(title))
            self.allowed_actions[id_action] = config


    def on_main(self):
        job = Job(self.id_service, self.allowed_actions.keys())
        if not job:
            return

        id_asset = job.id_object
        asset = Asset(id_asset)

        try:
            vars = json.loads(job.settings)
        except:
            vars = {}

        action_config = self.allowed_actions[job.id_action]
        tasks = action_config.findall("task")


        job_start_time = last_info_time = time.time()
        for id_task, task in enumerate(tasks):
            task_start_time = time.time()

            try:
                using = task.attrib["using"]
            except:
                continue

            if not using in encoders:
                continue

            logging.debug("Configuring task {} of {}".format(id_task+1, len(tasks)) )
            encoder = encoders[using](asset, task, vars)
            err = encoder.configure()

            if err:
                job.fail(err)
                return

            logging.info("Starting task {} of {}".format(id_task+1, len(tasks)) )
            encoder.run()

            old_progress = 0
            while encoder.is_working():
                now = time.time()
                progress, msg = encoder.get_progress()
                if progress < 0:
                    break

                if progress != old_progress:
                    job.set_progress(progress*100, msg)
                    old_progress = progress

                if now - last_info_time > FORCE_INFO_EVERY:
                    logging.debug("{}: {}, {:.2f}% completed".format(asset, msg, progress*100))
                    last_info_time = now
                time.sleep(.0001)


            progress, msg = encoder.get_progress()
            if progress == FAILED:
                job.fail(msg)
                return

            logging.debug("Finalizing task {} of {}".format(id_task+1, len(tasks)) )
            err = encoder.finalize()
            if err:
                job.fail(err)
                return

            vars = encoder.vars


        job.done()


