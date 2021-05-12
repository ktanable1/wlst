#
# WLST script: status.py 
# Start, Stop, ForceStop, Restart, ForceRestart
# @author - Kenji Tan
#

from datetime import datetime
import re
import sys
import os
import getopt



SERVERS = 'Servers'
ENVS = {
  "DEV11" : "t3://shepadmin-lt1:7811",
  "DEV12" : "t3://shepadmin-lt1:7521",
  "DEV21" : "t3://shepadmin-lt1:7411",
}


svc_names = None
env       = None
app_names = None


def usage():
  script_name = sys.argv[0]
  usage_text = """
    %s -e <env_name> [ -n <service_name or names_separated_by_comma> ]
  
  E.g. 
    [1] Start service
    %s -e DEV11  -n estrapp1_1,websvcapp1_1  start
    
    [2] Stop service (gracefully)
    %s -e DEV11  -n estrapp1_1  stop
    
    [3] Force stop service (much faster kill)
    %s -e DEV11  -n estrapp1_1  force_stop
    
    [4] Restart (stop + start)
    %s -e DEV12  -n sympay1_1  restart
    
    [5] Force restart (force_stop + start)
    %s -e DEV12  -n sympay1_1  force_restart
    
    [6] Get status of service
    %s -e DEV11  -n estrapp1_1,websvcapp1_1  status
    %s -e DEV11  -n estrapp1_1,websvcapp1_1

  """ % (script_name,script_name,script_name,script_name,script_name,script_name,script_name,script_name)
  print usage_text
  sys.exit(1)


def elapsed_time(func):
  def inner(*args, **kw):
    start_time = datetime.now()
    result = func(*args, **kw)
    print "Elapsed time: [%s]\n" % (datetime.now() - start_time)
    return result
  return inner      

def _start_():
  for svc_name in svc_names: 
    print " @@@@@  STARTING: (%s)  @@@@@ \n" % svc_name
    start(svc_name, 'Server', block='true')
    _status_()

def _stop_(force='false'):
  for svc_name in svc_names:
    print " #####  STOP (force:%s): (%s)  ##### \n" % (force, svc_name) 
    shutdown(svc_name, 'Server', force, block='true')
    _status_()

def _force_stop_():
  _stop_(force='true')

def _restart_():
  _stop_()
  _start_()

def _force_restart_():
  _force_stop_()
  _start_()

def _status_():
  print " %%%%% STATUS: %%%%% "
  if not svc_names: 
    [ state(app) for app in app_names ]
  else:
    if not [ _ for _ in svc_names if _ in app_names ]:
      print "No such service name !!!"
      sys.exit(1)
    else: 
      [ state(app) for app in svc_names if app in app_names ]
  print "\n"


try:
  opts, args = getopt.getopt(sys.argv[1:], "e:n:h")
except getopt.GetoptError, (err):
  print str(err)
  sys.exit(1)

for o,a in opts:
  if o in ('-h', '--help'):
    usage()
  elif o in ('-n', '--name'):
    svc_names = a.split(',')
  elif o in ('-e', '--env'):    
    env = a 
      
if env == None:
    print "!!! Target ENV name is a required parameter !!!"      
    sys.exit(1)

args = [ _.lower() for _ in args ]
print " <<< ENV: %s >>> <<< NAME:%s >>> <<< ARGS: %s >>> " % (env, svc_names, args)

connect(os.getenv("WEBLOGIC_USERNAME"), os.getenv("WEBLOGIC_PASSWORD"), ENVS[env])
print """
######################################################################
%s
 * serverName: %s
 * isAdminServer: %s 
 * domainName: %s
 * connected: %s
######################################################################
""" % (version, serverName, isAdminServer, domainName, connected)

print "Enumerating all services: "
servers = ls(SERVERS)
app_names = [ re.split("\s+", _)[1] for _ in [ i for i in servers.split('\n') if i!='' ] ]

# write out app_names into csv file
print "*** app_names: %s ***\n" % (app_names)
f = None
try:
  f = open("services.csv", "w")
  f.write("[%s]\n" % env)
  f.write(",".join(app_names))
  f.write("\n")
finally:
  if f:
    f.close()

func_map = {
  "start"         : elapsed_time(_start_),
  "stop"          : elapsed_time(_stop_),
  "force_stop"    : elapsed_time(_force_stop_),
  "restart"       : elapsed_time(_restart_),
  "force_restart" : elapsed_time(_force_restart_), 
  "status"        : elapsed_time(_status_),
}
func_map.get(dict(enumerate(args)).get(0), func_map['status'])()

disconnect()
exit()

sys.exit(0)
