import multiprocessing
from multiprocessing import Queue
from BAAH import BAAH_core_process

class RunningBAAHProcess:
    def __init__(self):
        self.__ctx = multiprocessing.get_context("spawn")
        self.__name2process:dict[str, multiprocessing.Process] = dict()
        self.__name2queue:dict[str, multiprocessing.Queue] = dict()
        self.__name2status:dict[str, dict] = dict()
    
    def get_status_obj(self, configname):
        if configname not in self.__name2status:
            self.__name2status[configname] = {
                "stop_signal": 0,
                "runing_signal": 0,
                "now_logArea_id": 0 # 当前聚焦的日志窗口id，当新的窗口打开时，旧的窗口的监听日志的while循环会break
            }
        return self.__name2status[configname]

    def check_is_running(self, configname):
        status = self.get_status_obj(configname)
        return status["runing_signal"] == 1
    
    def get_process(self, configname):
        return self.__name2process.get(configname, None)

    def get_queue(self, configname):
        return self.__name2queue.get(configname, None)
    
    def run_task(self, configname):
        if not self.check_is_running(configname):
            # 用于共享消息
            queue = multiprocessing.Queue()
            self.__name2queue[configname] = queue
            # 启动进程
            p = self.__ctx.Process(target=BAAH_core_process, kwargs={
                "reread_config_name": configname,
                "must_auto_quit": True,
                "msg_queue": queue
            },
            daemon=True)
            self.__name2process[configname] = p
            p.start()
            # 更新status
            this_status = self.get_status_obj(configname)
            this_status["runing_signal"] = 1
            this_status["stop_signal"] = 0

        return self.__name2queue[configname]
        
    def stop_task(self, configname):
        if self.check_is_running(configname):
            process = self.__name2process[configname]
            if process.is_alive():
                process.terminate()
            queue = self.__name2queue[configname]
            queue.close()

        # 更新status
        this_status = self.get_status_obj(configname)
        this_status["runing_signal"] = 0
        this_status["stop_signal"] = 0
        
RunningBAAHProcess_instance = RunningBAAHProcess()