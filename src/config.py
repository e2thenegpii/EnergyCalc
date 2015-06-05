
from appdirs import *
from ConfigParser import *

appname   = 'EnergyCalc'
appauthor = 'Eldon Allred'

cache_directory = user_cache_dir(appname)
data_directory  = user_data_dir(appname)

config_files = [user_config_dir(appname) + '/config.txt',
        site_config_dir(appname) + '/config.txt']

config = SafeConfigParser()

config.read(config_files)

