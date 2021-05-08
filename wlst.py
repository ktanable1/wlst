#
# WLST script: azure_deploy.py 
# Deploy, Status
# @author - Kenji Tan
#

from datetime import datetime
import re
import sys
import os
import getopt



SERVERS = '/Servers'
ENVS = {
  "DEV4" : "t3://weblogicadmindev401:8080",
  "DEV5" : "t3://weblogicadmindev501:8080",
}

#
# { app_name : { env : { role : (target_host, deploy_path) } } }
# or 
# { app_name : { env : (target_host, deploy_path) } }
#
APPS = {
  "searchserver" : {
    "DEV4" : {
      "master" : (
        "searchmasterdev401", "/apps/dev4/deploy/app/searchserver.war"
      ),
      "slave"  : (
        "searchslavedev401", "/apps/dev4/deploy/app/searchserver.war"
      ),  
    },
    "DEV5" : {
      "master" : (
        "searchmasterdev501", "/apps/dev5/deploy/app/searchserver.war"
      ),
      "slave"  : (
        "searchslavedev501", "/apps/dev5/deploy/app/searchserver.war"
      ),  
    },
  },
  
  "estore" : { 
    "DEV4" : ("estoredev401", "/apps/dev4/deploy/app/estore.war"),
    "DEV5" : ("estoredev501", "/apps/dev5/deploy/app/estore.war"),
  },
  
  "notifier" : {
    "DEV4" : ("estorenotifierdev401", "/apps/dev4/deploy/app/notifier.war"),
    "DEV5" : ("estorenotifierdev501", "/apps/dev5/deploy/app/notifier.war"),
  },
  
  "om" : {
    "DEV4" : ("estoreomdev401", "/apps/dev4/deploy/app/estore-om.war"),
    "DEV5" : ("estoreomdev501", "/apps/dev5/deploy/app/estore-om.war"),
  },
  
  "settle" : {
    "DEV4" : ("estoresettledev401", "/apps/dev4/deploy/app/estore-settle.war"),
    "DEV5" : ("estoresettledev501", "/apps/dev5/deploy/app/estore-settle.war"),
  },
  
  "email" : {
    "DEV4" : ("estoreemaildev401", "/apps/dev4/deploy/app/estore-email.war"),
    "DEV5" : ("estoreemaildev501", "/apps/dev5/deploy/app/estore-email.war"),
  },
  
  "cmserver" : {
    "DEV4" : ("cmdev401", "/apps/dev4/deploy/app/cmserver.war"),
    "DEV5" : ("cmdev501", "/apps/dev5/deploy/app/cmserver.war"),
  },
  
  "csr" : {
    "DEV4" : ("csrdev401", "/apps/dev4/deploy/app/csr.war"),
    "DEV5" : ("csrdev501", "/apps/dev5/deploy/app/csr.war"),
  },
  
  "ecommercecloud" : {
    "DEV4" : ("webservicesdev401", "/apps/dev4/deploy/app/ecommercecloud.war"),
    "DEV5" : ("webservicesdev501", "/apps/dev5/deploy/app/ecommercecloud.war"),
  },
  
  "timetravel" : {
    "DEV4" : ("timetraveldev401", "/apps/dev4/deploy/app/timetravel.war"),
    "DEV5" : ("timetraveldev501", "/apps/dev5/deploy/app/timetravel.war"),
  },
  
  "symRuleEngineService" : {
    "DEV4" : ("rulesenginedev401", "/apps/dev4/deploy/app/symRuleEngineService.war"),
    "DEV5" : ("rulesenginedev501", "/apps/dev5/deploy/app/symRuleEngineService.war"),
  },
  
  "ep-webservices" : {
    "DEV4" : ("epwebservicesdev401", "/apps/dev4/deploy/app/ep-webservices.ear"),
    "DEV5" : ("epwebservicesdev501", "/apps/dev5/deploy/app/ep-webservices.ear"),
  },
  
  "csrtstore" : {
    "DEV4" : ("csrtstoredev401", "/apps/dev4/deploy/app/csrtstore.war"),
    "DEV5" : ("csrtstoredev501", "/apps/dev5/deploy/app/csrtstore.war"),
  },
}


svc_names = []
env       = None
server_names = None
app_names = None


def usage():
  script_name = sys.argv[0]
  usage_text = """
    %s -e <env_name> [ -n <service_name or names_separated_by_comma> ]  <status | deploy | restart>
  
  E.g. 
    
    [0] Get status of service
    %s -e DEV4  status
    %s -e DEV4  -n searchserver  status
    
    %s -e DEV5  status
    %s -e DEV5  -n searchserver  status
        

    [1] Deploy
    %s -e DEV4  -n searchserver  deploy 
    %s -e DEV4  -n searchserver:master  deploy
    %s -e DEV4  -n searchserver:slave   deploy
    
    %s -e DEV5  -n searchserver  deploy 
    %s -e DEV5  -n searchserver:master  deploy
    %s -e DEV5  -n searchserver:slave   deploy
        
    
    [2] Force Restart Server
    %s -e DEV4  -n searchserver  restart 
    %s -e DEV4  -n searchserver:master  restart 
    %s -e DEV4  -n searchserver:slave   restart 
    
    %s -e DEV5  -n searchserver  restart 
    %s -e DEV5  -n searchserver:master  restart 
    %s -e DEV5  -n searchserver:slave   restart    
    

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


def _deploy_():
  print " @@@@@ DEPLOY: @@@@@  "  

  if not svc_names:
    print "XXX service name(s) need to be specified! XXX"
    sys.exit(1)
  
  role = None  
  for svc_name in svc_names:  
    if svc_name.find(':') != -1:
      svc_name,role = svc_name.split(':')
      
    if svc_name in APPS.keys():
      serverConfig()
      redeploy(svc_name)
      startApplication(svc_name)
    else:
      print "WARN: [%s] does not exist. This could be a typo!" % svc_name

  _status_()  


def _status_():
  print " %%%%% STATUS: %%%%% "

  if svc_names: 
    # enumerate / list only user-specified servers/services
    for svc_name in svc_names:
      if svc_name.find(':') != -1:
        svc_name = svc_name.split(':')[0]
        
      if svc_name in APPS.keys():
        if isinstance(APPS[svc_name][env], dict):
          [ state(v[0]) for _,v in APPS[svc_name][env].iteritems() ]
        else:    
          [ state(APPS[svc_name][env][0]) ]

    domainRuntime()
    cd('/AppRuntimeStateRuntime/AppRuntimeStateRuntime')
    
    states = []
    for svc_name in svc_names: 
      if svc_name.find(':') != -1:
        svc_name = svc_name.split(':')[0]
      states.append(cmo.getIntendedState(svc_name))  
    
    for _ in zip(svc_names, states):
      print _ 
  else:
    # enumerate / list all servers/services
    [ state(APPS[_][env][0]) for _ in svc_names if _ in APPS.keys() and _ in app_names ]

    domainRuntime()
    cd('/AppRuntimeStateRuntime/AppRuntimeStateRuntime')
    for _ in zip(app_names, [cmo.getIntendedState(_) for _ in app_names]): 
      print _
      
  print "\n"


def _restart_():
  print " ^^^^^ RESTART: ^^^^^ "
  
  if not svc_names: 
    print "XXX service name(s) need to be specified! XXX"
    sys.exit(1)

  role = None
  for svc_name in svc_names:
    if svc_name.find(':') != -1:
      svc_name,role = svc_name.split(':')

    if svc_name in APPS.keys():
      if role:
        if isinstance(APPS[svc_name][env],dict) and role in APPS[svc_name][env]:
          try:
            shutdown(APPS[svc_name][env][role][0], 'Server', force='true', block='true')
          except:
            pass
          start(APPS[svc_name][env][role][0], 'Server', block='true')
        else:
          print "WARN: [%s] role does not exist. Probably a typo!" % role
      else:
        # no role subfield 
        try:
          shutdown(APPS[svc_name][env][0], 'Server', force='true', block='true')
        except:
          pass
        start(APPS[svc_name][env][0], 'Server', block='true')
    else:
      print "WARN: [%s] does not exist. This could be a typo!" % svc_name

  _status_()  




try:
  opts, args = getopt.getopt(sys.argv[1:], "e:n:h")
except getopt.GetoptError, (err):
  print str(err)
  sys.exit(1)

for o,a in opts:
  if o in ('-h', '--help'):
    usage()
  elif o in ('-n', '--name'):
    svc_names.extend(a.split(','))
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

print "Enumerating all servers & services: "
cd(SERVERS)
servers = ls(SERVERS)
  
domainConfig()
app_names = [_.name for _ in cmo.getAppDeployments()]
server_names = [ re.split("\s+", _)[1] for _ in [ i for i in servers.split('\n') if i!='' ] ]

print "Server states: "
[ state(server) for server in server_names ]
print "Deployed Apps: ==>\n%s\n<==" % app_names

if svc_names: 
  if [ app for app in svc_names if app not in app_names ]:
    print "WARN: Specified service does not exist! Service names should generally be from: %s" % app_names


func_map = {
  "deploy"        : elapsed_time(_restart_),
  "status"        : elapsed_time(_status_),
  "restart"       : elapsed_time(_restart_),
}
func_map.get(dict(enumerate(args)).get(0), func_map['status'])()

disconnect()
exit()

sys.exit(0)
