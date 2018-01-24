#!/usr/bin/env python
'''
# Licensed Material - Property of IBM
# 5724-I63, 5724-H88, (C) Copyright IBM Corp. 2018 - All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or disclosure
# restricted by GSA ADP Schedule Contract with IBM Corp.
#
# DISCLAIMER:
# The following source code is sample code created by IBM Corporation.
# This sample code is provided to you solely for the purpose of assisting you
# in the  use of  the product. The code is provided 'AS IS', without warranty or
# condition of any kind. IBM shall not be liable for any damages arising out of 
# your use of the sample code, even if IBM has been advised of the possibility 
# of such damages.

Created on Jan 11, 2018

@author: petervansickel - pvs@us.ibm.com

Description:
  This module drives a test of ICP worker node resiliency.
  The test loops through the worker nodes of an ICP cluster, simulating a failure of
  each one and ensuring that a deployed test application continues to function correctly.  
  
History:
  11 JAN 2018 Peter Van Sickel - pvs@us.ibm.com
  Initial creation of the module.  Some utilities I've been using over the years with Jython
  are used in this module.  They are pulled in from a library referred to as Yet Another 
  Python Library, (aka yapl).

 
'''

import sys, os.path
from yapl.utilities.Trace import Trace, Level
import yapl.utilities.Utilities as Utilities
from yapl.exceptions.Exceptions import ExitException, InvalidArgumentException
from yapl.exceptions.Exceptions import MissingArgumentException
from yapl.exceptions.Exceptions import AttributeValueException

# imports needed for interaction with Ansible
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.executor.playbook_executor import PlaybookExecutor



HelpFile = "WorkerNodeResiliencyTest01Help.txt"

TR = Trace(__name__)


class WorkerNodeResiliencyTest01:
  """
    Main class for the WorkerNodeResiliencyTest.  The "main" method of this class is invoked when the script is run.
    This class is a top level class that drives all the work done by the script.
  """
  
  ArgsSignature = {
                    '--help': 'string',
                    '-worker_nodes': 'string',
                    '-worker_node': 'string',
                    '-proxy_vhost': 'string',
                    '-proxy_host': 'string',
                    '-inventory': 'string',
                    '-logFile': 'string',
                    '-logfile': 'string',
                    '-trace': 'string'
                   }
    

  def __init__(self):
    """
      Constructor
    """
    self.rc = 0
  #endDef

  
  def _getArg(self,synonyms,args,default=None):
    """
      Return the value from the args dictionary that may be specified with any of the
      argument names in the list of synonyms.
      
      The synonyms argument may be a list of strings or it may be a string representation
      of a list of names with a comma or space separating each name.
      
      The args is a dictionary with the keyword value pairs that are the arguments 
      that may have one of the names in the synonyms list.
      
      If the args dictionary does not include the option that may be named by any 
      of the given synonyms then the given default value is returned.
      
      NOTE: This method has to be careful to make explicit checks for value being None
      rather than something that is just logically false.  If value gets assigned 0 from 
      the get on the args (command line args) dictionary, that appears as false in a 
      condition expression.  However 0 may be a legitimate value for an input parameter
      in the args dictionary.  We need to break out of the loop that is checking synonyms
      as well as avoid assigning the default value if 0 is the value provided in the 
      args dictionary. 
    """
    value = None
    if (type(synonyms) != type([])):
      synonyms = Utilities.splitString(synonyms)
    #endIf
    
    for name in synonyms:
      value = args.get(name)
      if (value != None):
        break
      #endIf
    #endFor
    
    if (value == None and default != None):
      value = default
    #endIf
    
    return value
  #endDef


  def _usage(self):
    """
      Emit usage info to stdout.
      The _usage() method is invoked by the --help option.
    """
    methodName = '_usage'
    if (os.path.exists(HelpFile)):
      Utilities.showFile(HelpFile)
    else:
      TR.info(methodName,"There is no usage information for '%s'" % __name__)
    #endIf
  #endDef  


  def _configureTraceAndLogging(self,traceArgs):
    """
      Return a tuple with the trace spec and logFile if trace is set based on given traceArgs.
      
      traceArgs is a dictionary with the trace configuration specified.
         trace <tracespec>
         logFile|logfile <pathname>
         
      If trace is specified in the trace arguments then set up the trace.
      If a log file is specified, then set up the log file as well.
      If trace is specified and no log file is specified, then the log file is
      set to "trace.log" in the current working directory.
    """
    logFile = self._getArg(['logFile','logfile'], traceArgs)
    if (logFile):
      TR.appendTraceLog(logFile)
    #endIf

    trace = traceArgs.get('trace')
    
    if (trace):      
      if (not logFile):
        TR.appendTraceLog('trace.log')
      #endDef
      
      TR.configureTrace(trace)
    #endIf
    return (trace,logFile)
  #endDef


  def _get_hosts(self, pattern):
    """
      Wrapper for Ansible InventoryManager get_hosts().  
    """
    methodName = "_get_hosts"
    if (not self.inventory):
      raise AttributeValueException("Scripting Error: The inventory instance variable is expected to have a value.")
    #endIf
    
    hosts = self.inventory.get_hosts(pattern)
    if (TR.isLoggable(Level.FINE)):
      TR.fine(methodName,"For pattern: %s, hosts: %s" % (pattern, hosts))
    #endIf
    return hosts
  #endDef
    
  
  def _runPlaybook(self, playbook_path, worker_node, proxy_vhost):
    """
      Helper method to run the Ansible playbook for testing ICP worker node resiliency.    
    """
    
    self.variable_manager.extra_vars = {'worker_node': worker_node, 'proxy_vhost': proxy_vhost}
   
    # The constructor for PlaybookExecutor has all of the following parameters required.
    pbex = PlaybookExecutor(playbooks=[playbook_path], 
                            inventory=self.inventory, 
                            variable_manager=self.variable_manager,
                            loader=self.loader,
                            options=self.options,
                            passwords=self.passwords)

    pbex.run()
    
  #endDef


  def _runPlaybooks(self, pattern, proxy_vhost):
    """
      Expand the pattern to a list of nodes (hosts) and run the playbook for each node.
      
      This is a wrapper that iterates over the list of nodes represented by the pattern and 
      invokes _runPlaybook() for each node.
    """
    
    worker_nodes = self._get_hosts(pattern)
    if (not worker_nodes):
      raise InvalidArgumentException("The given pattern: %s, has resulted in no matching hosts in the inventory.")
    #endIf
    
    for node in worker_nodes:
      self._runPlaybook('icp_worker_node_failover_test_01.yml',node,proxy_vhost)
    #endFor
    
  #endDef
    
  
  def _configureAnsible(self, inventory_path):
    """
      Create instances if the various data structures needed to run an Ansible playbook.
    """
    
    if (not inventory_path):
      raise MissingArgumentException("An inventory path must he provided.")
    #endIf
    
    self.loader = DataLoader()

    # The Options tuple is a pain in the neck.  There is a boatload of possible options.  You would hope they would 
    # all default to something reasonable.  There is no documentation that I can find on the possible values for options.
    # There is no documentation on which options are required.  You have to run your code and see what breaks.  The 
    # examples show a lot of options that all seem to take on a "don't care" value, e.g., False, None.
    # NOTE: For every attribute listed in the Options namedtuple, an attribute value must be provided when the Options() 
    # constructor is instantiated.
    # NOTE: I tried using forks=0 which I was hoping would lead to some default being used, but intead I got a "list index
    # out of range" error in Ansible code: linear.py which is invoked out of task_queue_manager.py.
    # NOTE: listtags, listtasks, listhosts, syntax and diff are all required for sure.  Errors occur if they are not attributes
    # of the given options.
    Options = namedtuple('Options', ['listtags', 'listtasks', 'listhosts', 'syntax', 'connection','module_path', 'forks', 'remote_user', 'private_key_file', 'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args', 'scp_extra_args', 'become', 'become_method', 'become_user', 'verbosity', 'check', 'diff'])
    self.options = Options(listtags=False, listtasks=False, listhosts=False, syntax=False, connection='ssh', module_path=None, forks=5, remote_user=None, private_key_file=None, ssh_common_args=None, ssh_extra_args=None, sftp_extra_args=None, scp_extra_args=None, become=False, become_method=None, become_user=None, verbosity=None, check=False, diff=False)

    # Based on my skim of the InventoryManger code, sources is intended to be a list of paths.
    # It can also be a string that is one path or comma-separated string that is a list of paths.
    self.inventory = InventoryManager(loader=self.loader, sources=[inventory_path])

    # NOTE: VariableManager constructor doesn't require inventory, but if you don't provide one you get exceptions.
    self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)
    
    # For now, we don't need any passwords.  Future version of script could support provision of passwords.
    self.passwords = {}

  #endDef
  
  
  def main(self,argv):
    """
      Main does command line argument processing, sets up trace and then kicks off the methods to 
      do the work.
    """
    methodName = "main"
    
    self.rc = 0
    try:
      ####### Start command line processing    
      cmdLineArgs = Utilities.getInputArgs(self.ArgsSignature,argv[1:])
  
      # if trace is set from command line the trace variable holds the trace spec. 
      trace, logFile = self._configureTraceAndLogging(cmdLineArgs) 
      
      if (cmdLineArgs.get("help")):
        self._usage()
        raise ExitException("After emitting help, jump to the end of main.")
      #endIf
  
      beginTime = Utilities.currentTimeMillis()
      TR.info(methodName,"WNRT01-0101I BEGIN Worker Node Resiliency Test01 version 0.0.1.")
      
      if (trace):
        TR.info(methodName,"WNRT01-0102I Tracing with specification: '%s' to log file: '%s'" % (trace,logFile))
      #endIf
    
      inventory_path = self._getArg(['inventory'],cmdLineArgs,default='/etc/ansible/hosts')
      TR.info(methodName,"Using inventory path: %s" % inventory_path)
        
      self._configureAnsible(inventory_path)

     
      pattern = self._getArg(['worker_nodes','worker_node'],cmdLineArgs)
      if (not pattern):
        raise MissingArgumentException("A worker_nodes argument (host name or regex pattern) is required.")
      #endIf
      
      proxy_vhost  = self._getArg(['proxy_vhost','proxy_host'],cmdLineArgs)
      if (not proxy_vhost):
        raise MissingArgumentException("A proxy virtual host (proxy_vhost) argument is required.")
      #endIf

      self._runPlaybooks(pattern, proxy_vhost)              

      endTime = Utilities.currentTimeMillis()
      elapsedTime = (endTime - beginTime)/1000
      TR.info(methodName,"WNRT01-0103I END Worker Node Resiliency Test01.  Elapsed time (seconds): %d" % (elapsedTime))

    except ExitException:
      pass # ExitException is used as a "goto" end of program after emitting help info
    
    except Exception, e:
      TR.error(methodName,"Exception: %s" % e, e)
      self.rc = 1

    #endTry

    if (TR.traceFile):
      TR.closeTraceLog()
    #endIf

    sys.exit(self.rc)   
  #endDef
  
#endClass

if __name__ == '__main__':
  mainInstance = WorkerNodeResiliencyTest01()
  mainInstance.main(sys.argv)
#endIf