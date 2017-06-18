import logging
import os

def decorate_emit(fn):
    '''Get the log record'''
    def new(*args):
        '''Color levels'''
        level = [
                    { "name": "DEBUG"   , "color": "\033[35;1m" },
                    { "name": "INFO"    , "color": "\033[32;1m" },
                    { "name": "WARNING" , "color": "\033[33;1m" },
                    { "name": "ERROR"   , "color": "\033[31;1m" },
                    { "name": "CRITICAL", "color": "\033[31;1m" }
        ]

        for lvl in iter(level):
            if args[0].levelname is lvl['name']:
                args[0].levelname = "{0}{1}\033[0m".format(lvl['color'],
                                                            args[0].levelname)
        return fn(*args)
    return new

class __Log:
    def __init__(self, name='qtc.log', lvl=logging.DEBUG, in_file=True):
        log_dir = './log'
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        self.l = logging.getLogger(log_dir+name)
        if in_file:
            self.stream_handler = logging.FileHandler(name, mode='w')
        else:
            self.stream_handler = logging.StreamHandler()
        self.l.setLevel(lvl)
        self.l.addHandler(self.stream_handler)
        self.stream_handler.emit = decorate_emit(self.stream_handler.emit)

    def __call__(self):
        self.f, self.lineno, self.fn, self.stack_info = self.l.findCaller()
        self.fmt = "[%(levelname)s][{0}:{1}:{2}] %(message)s".format(
                                    self.f.split('/')[-1], self.fn, self.lineno
        )
        formatter = logging.Formatter(self.fmt)
        self.stream_handler.setFormatter(formatter)
        return self.l

L = __Log()

def DEBUG(*args):
    L().debug(*args)

def INFO(*args):
    L().info(*args)

def WARNING(*args):
    L().warning(*args)

def ERROR(*args):
    L().error(*args)

def CRITICAL(*args):
    L().critical(*args)
