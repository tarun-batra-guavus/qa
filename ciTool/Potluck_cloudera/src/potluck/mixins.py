# Singleton class mixin
class MetaSingleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(MetaSingleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class SingletonMixin(object):
    """A singleton mixin which can be subclassed to create singleton classes"""
    __metaclass__ = MetaSingleton
