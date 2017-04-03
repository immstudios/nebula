from nebula import *
from nx.jobs import Action

from encoders import Ffmpeg, Ftp

FORCE_INFO_EVERY = 20

encoders = {
    "ffmpeg" : Ffmpeg,
    "ftp" : Ftp
}



class Service(BaseService):
    def on_init(self):
        self.service_type = "conv"
        self.actions = []
        db.query("SELECT id, title, service_type, settings FROM actions ORDER BY id_action")
        for id_action, title, service_type, settings in db.fetchall():
            if service_type == self.service_type:
                logging.debug("Registering action {}".format(title))
                self.actions.append(Action(id, title, xml(settings)))

    def reset_jobs(self):
        db = DB()
        db.query("""
            UPDATE jobs SET
                id_service=0,
                progress=0,
                retries=0,
                status=0,
                message='Restart requested after service restart',
                start_time=0,
                end_time=0
            WHERE
                id_service=%s AND STATUS IN (0,1,5)"""
                [id_service]
            )
        db.commit()


    def on_main(self):
        db = DB()
        job = get_job(
                self.id_service,
                [action.id for action in self.actions],
                db=db
            )
        if not job:
            return




    def on_main_old(self):
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
