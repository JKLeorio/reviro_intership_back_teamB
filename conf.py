import decouple

DEBUG=decouple.config('DEBUG', default=True ,cast=bool)