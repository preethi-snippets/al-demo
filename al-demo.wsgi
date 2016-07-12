import site
import sys
import os
import logging

# Add virtualenv site packages
site.addsitedir(os.path.join(os.path.dirname(__file__), '/home/ubuntu/al-demo-env/local/lib/python2.7/site-packages'))
 
# Path of execution
sys.path.append('/var/www/al-demo')
 
# Fired up virtualenv before include application
activate_env = os.path.expanduser(os.path.join(os.path.dirname(__file__), '/home/ubuntu/al-demo-env/bin/activate_this.py'))
execfile(activate_env, dict(__file__=activate_env))
 
from application import application
