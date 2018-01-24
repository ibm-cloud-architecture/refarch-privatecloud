##################################################################################################
# Licensed Material - Property of IBM
# 5724-I63, 5724-H88, (C) Copyright IBM Corp. 2010,2012 - All Rights Reserved.
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
##################################################################################################

##################################################################################################
#
# File Name:    Trace.py 
# Description:  This file contains a trace class developed for use with WebSphere Application 
# Server wsadmin scripting.  However, there is nothing in this module implementation that
# is specific to wsadmin or WebSphere Application Server.  The module code is straight Jython
# and fully self contained, i.e., it relies on no other script modules.
#  
# Author:	Peter Van Sickel pvs@us.ibm.com
#
# History:
#    This Trace implementation has been around in various forms for some time as indicated
#    by the history.  There were significant enhancements to it in 2011 and 2012.
#
#        19 SEP 2009 - pvs - Pulling this together from previous work.
#
#        05 NOV 2009 - pvs
#           Added the source line number as part of standard trace output.  
#           Added a "module" parameter to the trace constructor.  
#           The new approach to using the Trace class is to now have a 
#           TR instance in each module instead of one global instance.
#           Added entry and exit methods.  I didn't realize I hadn't defined
#           an entry and exit method.
#
#        05 JAN 2011 - pvs
#           Added additional levels and corresponding methods to conform to 
#           java.util.logging.Level trace levels.  This makes this trace class 
#           intuitive for Java programmers.
#           
#           Also introduced the _log() method to consolidate the actual trace
#           emitting code into one method.
#
#        12 MAY 2011 - pvs
#           Added the option to send trace to a file both in the constructor
#           as a logFile parameter and using a setter method.
#           The logFile parameter is a string that is a fully qualified path.
#           The logFile is opened and the file descriptor stored in a class
#           attribute named logFile so all trace for all instances will be sent 
#           to that file.
#
#        21 SEP 2011 - pvs
#           Moved traceLevels out of the instance for each Trace and into
#           the Trace class.  The traceLevels dictionary certainly doesn't
#           need to be created for each Trace instance.  Modified the 
#           references to traceLevels accordingly.
#
#        16 JAN 2012 - pvs
#           Added an eventType to the output to provide a 1 character visual
#           cue regarding the "type" of the particular trace that is emitted.
#           The event type code is the same used in the WAS runtime tracing.
#
#        25 JAN 2012 - pvs
#           Added an isLoggable(Level) method to support the ability
#           to do a quick query on the log level before actually invoking
#           a trace method to cut down on overhead of the trace method
#           invocation building its arg strings, etc.  Similar to Java
#           logging framework.
#
#           Also did some refactoring that led to adding a couple of helper
#           methods: _coerceLevel, _isTraceLevel.  This is part of an effort
#           to move to using the Level class constants rather than the string
#           names for the trace levels.  However, both are transparently
#           supported.
#
#        28 JAN 2012 - pvs
#           Added the optional "exc" (exception) argument to severe() and 
#           error() and as an optional argument to _log().  When exc is passed
#           to _log() the exception message and a stack dump is included in the 
#           trace string.  Including the stack dump for error() and severe()
#           conforms to WAS tracing conventions.  See the Jython/Python doc
#           on the traceback module.  This exception stack trace code is based
#           on work from John Martinek.
#
#        16 FEB 2012 - pvs
#           Moved the methods to open and close the trace file into the Trace 
#           class. Now those methods are available in the Trace module namespace 
#           and the Trace class namespace.  This is intended to be a convenience
#           modification only.  The trace file is still a class level object
#           used by all instances.
#
#        26 APR 2012 - pvs
#           Replaced Trace methods entry() with entering() and exit() with exiting().  
#           The exit() method name uses a Jython/Python keyword.  The method names 
#           entering() and exiting() are preferred for conformance with Java Logger.  
#           Also cleaned up some other indentation warnings and unused variable warn-
#           ings. In _sourceFrame() method, replaced a deprecated use of sys.exc_traceback 
#           with a call to sys.exc_info()[2]
#
#        01 MAY 2012 - pvs
#           Added the use of a lock in the Trace._log() method to synchronize the
#           file IO statements (write, flush).  I discovered through use of Trace
#           in notification handlers (which execute on separate threads) that 
#           things can get messed up in the trace log depending on when different
#           threads jump in to do output.
#
#        06 SEP 2012 - pvs
#           John Martinek added a thread ID to the trace string.  This becomes 
#           useful for scenarios where multiple threads are emitting trace.  
#           John had also made some code corrections to keep the error message
#           with the stack dump for exception traces in multi-threaded trace
#           scenarios.  The original code emitted the error message in one
#           place and the stack dump in a second place.  Also made the exc
#           argument for error() and severe() optional and set to None by
#           default.
#
#        07 - 14 SEP 2012 - pvs
#           Made a number of changes to clean up the Trace implementation in 
#           preparation for releasing it as part of a dW article.  I simplified
#           the API here and there.  Renamed the exception classes to follow
#           a better naming convention that included the word Exception as the
#           last word of the class name.
#
#           The  most important addition was to add the ability to control trace 
#           using trace strings as is done with WebSphere Application Server. I 
#           had been wanting to implement that sort of thing for a good while 
#           and finally did it.
#
#           Modified the Trace constructor to require an "entity" name which 
#           is the name of a module or class being traced.  An exception is 
#           thrown if the entity name is empty or None.  The entity argument
#           to the constructor is required.  This moved the Trace class from
#           a focus on tracing modules to a focus on tracing modules and classes.
#           The original module focus had its roots in Java in that each file
#           holds only one class definition.  But in Jython a file (module) may
#           hold multiple class definitions so there may be a Trace instance for
#           each class defined in that module.
#
#           Modified the Trace constructor to remove the log file as a keyword
#           parameter.  It turns out it is much more common and "natural" to open 
#           a log file based on a command line input parameter and then use the 
#           a Trace instance method or the Trace module method to open the log 
#           file for writing (truncate existing) or appending.
#
#           Modified the Trace constructor to take only an integer constant for
#           the level keyword argument.  The level keyword argument also defaults
#           to Level.INFO.  Removed support in the constructor for a string form
#           of a trace level.  (Using the Trace constructor to set the trace level
#           for a given entity is not recommended except in "quick-and-dirty" 
#           scenarios.  See elsewhere in the comments for the recommended approach.)
#
#      19 APR 2013
#           PVS - Added an option varable to the class that controls whether stack 
#           traces are provided from "top-to-bottom" (TTB) or "bottom to top" (BTT).
#           The default is TTB which is a Java style stack trace. The BTT option is
#           Python/Jython style of stack trace.  There is a method that is used to
#           create the stack representation from TTB as well as a method to create
#           the stack BTT.
#  NOTES:
#     In the trace methods, integer constants as defined in the Level class are used to 
#     avoid the overhead of using the dictionary with the named trace levels in it.
#  
#  Trace levels are ordered from "lower" to "higher" with lower trace levels being 
#  considered more important to emit such as for errors, warnings and "info" and higher 
#  trace levels reserved for debugging, such as config, fine, finer, finest.
# 
#  If no log file has been defined, then all trace levels are emitted to stdout which 
#  usually means it shows up in the command window where the script was launched.
#  (Obviously, it could be redirected to a file.)
#
#  If a log file has been configured, then all trace goes to the log file.  And only 
#  trace at INFO level and "lower" goes to stdout, i.e., error, warning and info.
#
# The format of the trace line is:
# [<datetimestamp>] <threadid> T <entityname>(<linenumber>) <methodname> : <message>
#   where T is a one character event type
#   <entityname> is the module or class being traced (see more on this below)
#
# NOTE: <entityname> does not get truncated as in WAS trace.  We opted to emit the 
# entire name to make it easy to determine which module or class is emitting the
# the trace.
#
#  Usage example:
#  Somewhere at the top of module put the import statement:
#
#     from was.admin.utilities.Trace import Trace,Level
#
#  Note: The import statement shown above assumes the package and library directory 
#  structure of a library of modules that includes the Trace module.  Your import 
#  statement should reflect your specific runtime and library structure.  If the 
#  Trace module is in the same directory as the module using it, the import will 
#  look like:
#
#     from Trace import Trace,Level
#
#  Trace constructor signature: __init__(self,entity,level=Level.INFO)
#  Note: An entity name (module or class name) is required.
#        level must be one of the constants defined by the Level class.
#
#  When creating a Trace instance for a module, initialize a Trace instance for the 
#  module.
#
#     TR = Trace(__name__)
#
#  When creating an instance of Trace for a class within a module it is recommended
#  that the module name be incorporated into the entity name provided to the Trace
#  constructor.  If a class level variable is preferred:
#     class MyClass:
#       TR = Trace("%s.MyClass" % __name__)
#
#  If an instance variable is preferred, then in the body of the __init__ method for
#  the class:
#     class MyClass:
#       def __init__(self, ...):
#         self.TR = Trace("%s.MyClass" % __name__)
#         ...
#       #endDef
#       ...
#     #endClass
#
#  For a class level variable the Trace instance will be referenced using the class name
#  as a qualifier.  For an instance level variable the Trace instance will be referenced 
#  using "self" as the qualifier.
#
#  Using the module name (__name__) as part of the entity name argument for the Trace
#  constructor helps greatly to avoid name collisions when each trace instance registers 
#  itself in the "tracedEntities" class variable that is ultimately used to enable trace 
#  levels using trace strings.  In short, the "entity name" (module or class name) for each 
#  Trace instance needs to be unique.  (Jython packages also help to ensure module and class
#  name uniqueness.)
#
#  Always use the module __name__ builtin rather than an explicit module name
#  string to avoid issues if the module name is changed or if you end up using a
#  module in a library organized in Jython packages and the package names get
#  refactored or the module gets exported out to a flat collection of files.
#
#  <Thoughts_on_how_to_define_Trace_instances>
#
#  If there is only one traced class definition in a given module, then a module level
#  Trace instance is likely sufficient.  However, if you define multiple classes in 
#  a module, and more than one class needs to use Trace, then it is recommended that a 
#  separate Trace instance be created for each class.
#
#  It is recommended that each "major" class (that would use Trace) be defined in its 
#  own file and thus always use module level instances of Trace.  This makes it easy to 
#  reference the Trace instance variable without a qualifier when invoking a Trace method,
#  e.g., TR.info(). Minor supporting classes that might be in the same file don't usually 
#  get traced because they are simple.  If a supporting class is or becomes complex enough 
#  that Trace is needed then that class likely deserves its own module.  Refactor the 
#  original module into multiple modules, one for each "complex" class and continue to 
#  use a module level Trace instance for each class.
#
#  If you want to define a Trace instance for a class, recommend using a class level 
#  Trace instance over an instance level, as it seems unnecessary to incur the overhead 
#  of instantiating a Trace instance for each instance of a class.
#
#  If the class name is annoyingly long for descriptive purposes, either refactor the name 
#  into something shorter (that hopefully does not sacrifice its descriptiveness), or assign
#  the class to a variable with a short name, e.g., 
#      thisClass = MyClassWithADescriptiveName
#  Or even shorter:
#      tC = MyClassWithADescriptiveName
#  Then you can reference the Trace instance as:
#      thisClass.TR.info(...)
#  Or
#      tC.TR.info(...)
#  
#  </Thoughts_on_how_to_define_Trace_instances>
#
#  In the bodies of methods where you want trace, define a variable named
#  methodName at the top of the method and assign the method name to it:
#    def myMethod(...):
#      """documentation string for the method..."""
#      methodName = "myMethod"
#
#      TR.entering(methodName)
#      ... 
#      TR.info(methodName,"My trace message.")
#      ...
#      TR.exiting(methodName)
#    #endDef
#  If you change a method name, be sure to remember to change the static string
#  value assigned to methodName.
#
# For traces that are at levels above "info" it is typical to use the isLoggable()
# method to avoid even the overhead of making the call to the Trace method, e.g.,
#
#    if (TR.isLoggable(Level.FINEST)):
#      TR.finest(methodName,"trace message that likely involves string construction")
#    #endIf
#
# It is often the case that you want trace to go to a log file.  To always append
# trace to a log file use:
#         TR.appendTraceLog(logPath)
#         where logPath is a string that is the path to the file.
#
# There is also a method to open the logfile and truncate any existing content
# from previous uses of the log file:
#         TR.openTraceLog(logPath)
#
# NOTE: The logFile is a Trace class level variable and thus all instances of Trace
# write to the same log file.  You can open a log file with instance methods or 
# module methods.  Usually the instance methods are the most convenient. Opening a 
# log file is something you want to control based on command line arguments to a top 
# level "main" class for your script, for example, using -logfile <file_path> as a
# command line parameter.
#
# There are a couple of different ways to set the trace level for a given Trace 
# instance. The Trace class constructor has a keyword parameter named "level" that 
# can be used when the module trace class is instantiated.  The trace class also
# has a method to set trace to a specific level:
#
#         TR.setTraceLevel(level)
#
#         where level is either a string that is one of the valid trace levels
#         or level is one of the levels defined in the Level class, e.g.,
#
#         TR.setTraceLevel(Level.FINER)
#
# You can set the trace level in other modules (for example from a top level
# script), by importing that module and then using the trace global variable
# in that module.  For example, assume TR is the global variable that implements
# the Trace instance in a module named ServerCluster. An import of 
# the ServerCluster module is included in your script that is using it:
#
#       import was.admin.clusters.ServerCluster as ServerCluster
#
# Setting the trace level in that module is done as follows:
#
#       ServerCluster.TR.setTraceLevel(Level.FINEST)
#
# The above methods are relatively awkward and not recommended except in "quick and 
# dirty" scenarios.  The above methods tend to require code modifications to get a 
# different trace level or to enable trace in a different module that you decide you 
# need to trace. In other words the above methods don't readily support a dynamic 
# method of enabling trace across a wide range of modules that may be in use for a 
# given script.  The above methods were all that was available until the Trace
# class was enhanced to support the use of a trace specification string, which is 
# described next.
#
# The recommended approach for enabling trace for a collection of modules is to use 
# a command line argument to your main script that has a trace string specification 
# as its value.  Then use the module or Trace instance method configureTrace(traceString) 
# to set trace levels based on the given traceString.  So for example your main program 
# can support a
#     -trace <trace_string> 
# command line argument. Your command line processing code will parse through
# the "argv" array (sys.argv) and if it encounters the -trace keyword then it 
# takes the next element of argv to be the trace string.  Assume the value of 
# the trace string is stored in a variable named traceString.  Then traceString 
# can be passed into either the Trace instance instantiated for your main 
# module, e.g., 
#      TR.configureTrace(traceString)
# or the module level Trace method could be invoked assuming an import
# of the trace module as follows:
#      import Trace as TraceModule
#      ...
#      TraceModule.configureTrace(traceString)      
#
# See the module comments below near the definition of traceSpec and traceString
# in the Trace class for specifics on the syntax of the trace string.  In short 
# the trace string syntax is the same as that used by WebSphere Application Server
# without the "state" part.  (The state part is the "=enabled" or "=disabled" which
# fell out of favor along about version 7 of WAS.)
#
##################################################################################################
#
# List of module level methods:
#    openTraceLog(logPath)   - opens for write, the trace log file with the 
#                              given path; truncates the existing file
#    appendTraceLog(logPath) - opens for append, the trace log file with the 
#                              given path
#    closeTraceLog()         - closes the trace log file
#
#    parseTraceString(traceString) - parse the given trace string into a list 
#                                    of TraceSpecification instances
#                                    This method is not likely to be commonly
#                                    used. This method is used by other module
#                                    level methods and could be used to explore
#                                    the trace string parsing.
#
#   setTraceSpec(traceString) - Set Trace.traceSpec based on the given traceString.
#                               This is not intended for common use.
#
#   getTraceSpec()            - Get the value of Trace.traceSpec.
#
#   configureTrace(traceString) - Use this method to configure trace levels in all 
#                                 registered Trace instances based on the given traceString.
#                                 Assuming the usage pattern of instantiating a Trace instance
#                                 as a global in a module, the module Trace instances are 
#                                 instantiated and the module is "registered" when a module is 
#                                 imported. Trace levels will be set based on the given traceString
#                                 for all registered trace instances at the time configureTrace()
#                                 is invoked. Trace instances that are instantiated at some later
#                                 run time will also check the traceSpec as part of the Trace
#                                 instantiation.
#
# NOTE: The above trace log methods are implemented as Trace class methods as
# well.  It is usually convenient to use the instance level methods for opening 
# and closing the trace log file.
#
##################################################################################################
#
# List of Classes
#   EntityNameException
#   TraceLevelException
#   TraceSpecificationException
#   Level
#   TraceSpecification
#   Trace
#
##################################################################################################
#
# Imports
#
# Import Python module for dealing with dates and time and time zone names
import datetime
import time


import thread

# Lock is needed for ensuring thread safe file IO when 
# using a log file.
from threading import Lock

# The re module is needed for dealing with trace specifications
# that might use a wild-card character.
import re

# sys is used for the inspection stuff, e.g., getting a caller's stack frame
import sys

# os is needed for the separator character in file path names.
import os

# traceback is used for an exception stack dump
import traceback

TimeZoneName = time.strftime('%Z')

##################################################################################################
#
# Exception classes
#
class EntityNameException(Exception):
  """
    EntityNameException is raised when the trace constructor provides an empty
    module name.  When a Trace class is instantiated a module name is a required
    argument and it cannot be the empty string or None.
  """
  pass
#endClass

class TraceLevelException(Exception):
  """
    TraceLevelException is raised in methods in the Trace class when a value or name of a 
    trace level is encountered that is not recognized.
  """
  pass
#endClass

class TraceSpecificationException(Exception):
  """
    TraceSpecificationException is raised if a given trace string is not of the  
    correct syntax or otherwise is not recognized as a valid trace specification string.
  """
  pass
#endClass

class TraceConfigurationException(Exception):
  """
    TraceConfigurationException when there is something incorrect about how the Trace
    class is configured.
  """
  pass
#endClass

##################################################################################################
#
# Level class
#
# The trace levels overlap to support early implementations.
# The trace levels mimic Java trace levels in the newer usage of Trace.
# The trace level is one of: none|off|
#                            error|severe|
#                            warn|warning|
#                            info|
#                            config|
#                            fine|
#                            finer|
#                            finest|debug|all
class Level:
  """
    The Level class is a container for the integer representations for the various
    trace levels.  Level makes it convenient to reference the integer representations
    by name.
  """
  NONE = 0
  OFF = 0
  ERROR = 1
  SEVERE = 1
  WARN = 2
  WARNING = 2
  INFO = 3
  CONFIG = 4
  FINE = 5
  FINER = 6
  FINEST = 7
  DEBUG = 7
  ALL = 7
#endClass


##################################################################################################
#
# TraceSpecification class
#
class TraceSpecification:
  """
    TraceSpecification is used to implement a specific trace specification made up of an 
    entity "pattern" and a trace level.     
  """
  
  def __init__(self,pattern,level):
    if (not pattern):
      raise TraceSpecificationException("A trace specification must not be an empty string.")
    
    # pattern is retained for display
    self.pattern = pattern
    self.level = self._coerceLevel(level)
    # patternRegex is a Jython/Python regular expression of the given pattern
    self.patternRegex = self._patternToRegEx(pattern)
    # The compiledRegex is used to configure trace for active modules
    self.compiledRegex = re.compile(self.patternRegex)
  #endDef

   
  def __str__(self):
    return '<TraceSpecification pattern="%s" level="%s"/>' % (self.pattern,self.level)
  #endDef

  
  def __repr__(self):
    return '<TraceSpecification patternRegex="%s" level="%s"/>' % (self.patternRegex,self.level)
  #endDef

  
  def getPattern(self):
    """Return the pattern for this TraceSpecification instance."""
    return self.pattern
  #endDef

  
  def getLevel(self):
    """Return the trace level for this TraceSpecification instance."""
    return self.level
  #endDef


  def _coerceLevel(self,level):
    """
      Return an integer representation based on the given string representation. 
      The Trace.traceLevels hash table is used to do the translation.  The integer
      returned is one of the levels from the Level class.
  
      The incoming level is intended to be an integer or a Jython string.
    """
    if (type(level) == type(0)):
      if (level >= Level.NONE and level <= Level.FINEST):
        result = level
      else:
        raise TraceSpecificationException("Unknown integer trace level: %s  Valid integer trace levels: %s <= level <= %s" % (level, Level.NONE, Level.FINEST))
      #endIf
    elif (type(level) == type("") or type(level) == type(u"")):
      level = level.lower()
      # Need explicit test for None in the if condition because some valid trace
      # levels have a value of 0, e.g., none and off.
      if (Trace.traceLevels.get(level) == None):
        raise TraceSpecificationException("Unknown trace level: %s  Valid trace levels: %s" % (level,Trace.traceNames))
      else:
        result = Trace.traceLevels[level]
      #endIf
    else:
      raise TraceSpecificationException("Unexpected type of trace level, expected either a string or integer.")
    #endIf
    return result
  #endDef
  

  # The _patternToRegEx() takes an entity pattern string and converts it to a regular
  # expression string. The entity pattern may have explicit dots in it that are part 
  # of a Jython package name as well as a wildcard character at the end to indicate 
  # a collection of modules or classes in a given package.
  # The given pattern is transformed to the corresponding valid regular expression 
  # string, e.g.,  
  #   "was.admin.*" -> "was\.admin\..*?". 
  # 
  # The wildcard character is * and it can only terminate the trace string.
  # A trace string may have only a wildcard character, e.g., *=finer
  #
  # It is assumed the caller has checked that the trace string is not empty. 
  #
  # NOTE: For the simple case where the entity pattern string doesn't have a 
  # wildcard character in it, the result is merely the entity pattern string  
  # with a $ character pasted onto the end.  This forces exact matches of the 
  # pattern with a target string. For example re.match("foo","foobar") succeeds 
  # where re.match("foo$","foobar") does not.  
  #
  # See the Python doc on regular expressions for more RE info.  The use of .*? is 
  # explained there.  Putting the ? after .* keeps the RE from being "greedy" and 
  # matching more than intended.  The ? makes the RE "nongreedy".
  #
  #
  def _patternToRegEx(self,pattern):
    """
      Return a Python/Jython regular expression string that represents the given pattern.
    """
    if (pattern == "*"):
      # special case that matches anything
      regex = ".*?"
    else:
      regex = pattern
      if (regex.find(".") >= 0):
        regex = regex.replace(".", "\.")
      #endIf
      
      asteriskIndex = regex.find("*")
      if (asteriskIndex < 0):
        # no wildcard in pattern
        regex = "%s$" % regex
      elif (asteriskIndex + 1 != len(regex)):
        raise TraceSpecificationException("Invalid entity pattern: %s. A wildcard character may only be used to terminate a pattern." % pattern)
      else:
        # remove * and add ".*?"
        regex = "%s.*?" % regex[:-1]
      #endIf
    #endIf
    return regex
  #endDef
#endClass


##################################################################################################
#
# Trace class
#
# WARNING: All tracing methods must go through _log() and they can't call any intermediary 
# methods, otherwise the stack frame sequence gets out of wack and the line number will be
# incorrect in the log message.
#
# When a trace event is emitted one part of the emitted string just after the time stamp
# and thread ID is an 1 character string that represents the event type.  Each tracing 
# method includes its event type in the call to _log().
#
class Trace:
  """
    The Trace class, and its supporting classes, implements a WebSphere Application Server  
    style trace logger.
  """
  # Constructor signature: __init__(self,entity,level=Level.INFO)
  # Note: An entity name (module or class name) is required.
  #       level must be one of the constants defined by the Level class.
  # 
  # The tracedEntities dictionary keeps track of the modules that "register" themselves.
  # The tracedModule dictionary is keyed by a module name, i.e., the value of __name__
  # for a module when a Trace() instance is created for the module.
  # The value of each entry in tracedEntities is the instance of Trace for the module.
  tracedEntities = {}
    
  # The trace specification is used to control trace for all registered 
  # modules.  The traceSpec is a list of TraceSpecification instances.
  #
  traceSpec = None
  
  # The traceSpec is set using a trace string that has a format similar to what is
  # used for WAS trace strings.  The traceString holds the actual full trace string 
  # for reference purposes.  The traceString gets processed to create the traceSpec.
  #
  # For details on the syntax of the trace string, see the WAS InfoCenter section titled, 
  #       "Tracing and logging configuration"
  # The one thing not used from WAS trace string syntax is the "state", i.e., the trace
  # string doesn't need the enabled, disabled value, just a trace level.
  #
  # The BNF for a trace string looks like: 
  #     <trace_string> = <module_trace_string>[:<module_trace_string>]*
  #     <module_trace_string> = <module_pattern>=<level>
  #     <module_pattern> = <module_name>
  #                        | <module_package>.<module_name>
  #                        | <module_package>.*
  #                        | *
  #     <module_package> = <name>[.<name>]*
  #     <level> is one of the trace levels
  # 
  # Use a colon to separate multiple trace strings. An asterisk may be used to
  # terminate a trace string to enable trace for all the modules in a given family
  # as per the Jython package name, e.g., was.admin.*=all sets the trace level to 
  # "all" for all modules in the was.admin package and any of its sub-packages.
  # Another example of a trace string is:
  #     was.admin.clusters.ServerCluster=finer:was.admin.clusters.ClusterMember=fine
  # A wild-card could be used to set trace to fine for all modules in the 
  # was.admin.clusters package:  was.admin.clusters.*=fine
  #
  # NOTE: The default value of traceString is not actually processed.
  traceString = "*=info"

  traceFile = None

  traceFileLock = Lock()
  
  traceNames = ['none', 'off', 'error', 'severe', 'warn', 'warning', 
                'info', 'config', 'fine', 'finer', 'finest', 'debug', 'all']
  
  traceLevels = {'none': Level.NONE, 'off': Level.OFF, 
                        'error': Level.ERROR, 'severe': Level.SEVERE, 
                        'warn': Level.WARN, 'warning': Level.WARNING, 
                        'info': Level.INFO, 
                        'config': Level.CONFIG, 
                        'fine': Level.FINE,
                        'finer': Level.FINER,
                        'finest': Level.FINEST,
                        'debug': Level.FINEST,
                        'all': Level.FINEST }

  # Exception stacks may be printed "top-to-bottom" or "bottom-to-top".
  # TTB == top-to-bottom for stack trace which is Java style.
  TopToBottom = "TTB"
  # BTT == bottom-to-top for stack trace which is Python/Jython style.
  BottomToTop = "BTT"
  StackTraceStyle = TopToBottom
  StackTraceStyles = [TopToBottom, BottomToTop]

  # Source file output in exception stacks may be "name only" or "full path".
  # The default is NameOnly. (Usually module names alone are sufficient to differentiate
  # the source of a given line of code in the exception stack.)
  NameOnly = "NameOnly"
  FullPath = "FullPath"
  SourceFileStyle = NameOnly
  SourceFileStyles = [NameOnly, FullPath]
    
  def openTraceLog(self,logPath):
    if (Trace.traceFile != None):
      Trace.traceFile.close()
    #endIf
    Trace.traceFile = open(logPath,"w")
  #endDef


  def appendTraceLog(self,logPath):
    if (Trace.traceFile != None):
      Trace.traceFile.close()
    #endIf
    Trace.traceFile = open(logPath,"a")
  #endDef

  
  def closeTraceLog(self):
    if (Trace.traceFile != None):
      Trace.traceFile.close()
    #endIf
  #endDef


  def _coerceLevel(self,level):
    """
      Return an integer representation from the Level class for the given
      string representation of a trace level.
       
      The traceLevels hash table is used to do the translation.    
       
      The incoming level is intended to be a Jython string.  If it is not 
      a string then it is returned as is.
    """
    result = level
    if (type(level) == type("") or type(level) == type(u"")):
      level = level.lower()
      result = Trace.traceLevels.get(level)
      # Need an explicit test for None in the following if condition because
      # trace levels "none" and "off" map to a level with a value of 0
      if (result == None):
        raise TraceLevelException("Unknown trace level: %s  Valid trace levels: %s" % (level,Trace.traceNames))
      #endIf
    #endIf
    return result
  #endDef
  

  def _isTraceLevel(self,level):
    """
      Return "true" if the given trace level is a valid string or integer representation of a 
      trace level.
    """
       
    if (type(level) == type(0)):
      result = level >= Level.NONE and level <= Level.FINEST
    elif (type(level) == type("") or type(level) == type(u"")):
      level = level.lower()
      validLevel = Trace.traceLevels.get(level)
      # Keep in mind, trace level "none" maps to Level.NONE which has the value of 0
      result = validLevel != None
    else:
      # level can only be an int or str
      result = 0
    #endIf
    return result
  #endDef
  
  
  def configureThisTrace(self):
    """
      Set the trace level for this instance of the trace class based on the Trace class traceSpec.
      If there is no trace spec that has a module pattern that matches this trace instance 
      module name, then the trace level is not modified.
    """
    for spec in Trace.traceSpec:
      if (spec.compiledRegex.match(self.entityName)):
        self.traceLevel = spec.level
        break
      #endIf
    #endFor
  #endDef

  
  def __init__(self,entity,level=Level.INFO):
    """
      The Trace class has two instance variables that get initialized in the 
      constructor:
        entityName - (required) the name of the module or class being traced
        traceLevel - (optional) gets set to Level.INFO if optional keyword "level" 
                     parameter is not set on the Trace instantiation.
                     The level parameter must be an integer that is one of the 
                     constants in the Level class.
    """
    if (not entity):
      raise EntityNameException("A module or class name is required when instantiating a Trace instance.")
    #endIf
    
    if (type(level) != type(0) or level < Level.NONE or level > Level.FINEST):
      raise TraceLevelException("Invalid trace level: %s. Trace level must be an integer constant as defined by the Level class." % level)
    #endIf
    
    self.traceLevel = level
    
    # Register this trace instance
    Trace.tracedEntities[entity] = self
    self.entityName = entity

    # If the traceSpec has been set, check the traceSpec and configure this trace instance
    # trace level based on the traceSpec if there is a match on this Trace instance entity name.
    if (Trace.traceSpec):
      self.configureThisTrace()
    #endIf  
  #endDef


  # The _exceptionStack*() methods are based on a similar method that
  # John Martinek originally developed.  The Jython traceback module is 
  # used to get the method stack list, then appends each stack frame onto 
  # a new line.  It also gets the exception stack and does the same thing.  
  # The parts of the stack that belong to the Trace class are left out of 
  # the stack trace.
  #
  # For the TTB variation, the exception stack string is built by "pushing" 
  # each stack frame line onto the stack string. This causes the output to 
  # show up with the top of the stack as the first line in the output. (This 
  # is similar to how Java exception stacks are printed, however it is the 
  # reverse of how Python exception stacks are printed.)
  #
  # The "frame stack" shows the frames executed from the beginning of "main"
  # to the point where the  exception is handled.
  #
  # The "exception stack" shows up "above" the frame stack in the output.
  # The exception stack is the code tree from "main" to where the exception
  # was raised (thrown).  The exception stack is typically of most interest.
  #
  # When a stack frame is encountered where the file name ends in Trace.py
  # and the function name is either "error" or "severe" then execution
  # breaks out of the loop that is generating the stack dump string
  # to avoid showing the Trace module functions in the stack dump.
  # 
  # Trace.error() and Trace.severe() are the only two Trace methods that provide
  # a stack trace.
  # 
  def _exceptionStackTTB(self,methodName,exc,depth=10):
    """
      Return a string useable for output to stdout or a log file that provides a representation
      of the "exception stack" and the "frame stack" from "top to bottm" (TTB).
      The "exception stack" captures the code tree from main to where the exception was raised and 
      is usually the most interesting part of the stack.  The "frame stack" captures the code
      from the point to where the exception was caught. 
      
      Displaying the stack from top to bottom in an output log or stdout is the style in which
      Java displays the stack.
      
      There is another method named _exceptionStackBTT() that can be used to create a string that
      represents the execution stack from bottom to top, which is the style that Jython/Python
      uses by default.
    """
    stack = ""
    # Reconstruct the call stack from where the trace of the exception was initiated by invoking 
    # Trace.error() or Trace.severe().
    stackList = traceback.extract_stack()
    try:
      for stackData in stackList:
        sourcefile,line,function,text = stackData
        if (sourcefile.endswith("Trace.py") and (function == "error" or function == "severe")): break
        sepIndex = sourcefile.rfind(os.sep)
        if (sepIndex >=0 and Trace.SourceFileStyle == Trace.NameOnly):
          sourcefile = sourcefile[sepIndex+1:]
        #endIf
        if (text == None):
          if (not stack):
            # Leave out the newline for the bottom line on the stack
            stack = "\t%s(%s) [%s]" % (sourcefile,line,function)
          else:
            stack = "\t%s(%s) [%s]\n%s" % (sourcefile,line,function,stack)
          #endIf
        else:
          if (not stack):
            # Leave out the newline for the bottom line on the stack
            stack = "\t%s(%s) [%s] - %s" % (sourcefile,line,function,text)
          else:
            stack = "\t%s(%s) [%s] - %s\n%s" % (sourcefile,line,function,text,stack)
          #endIf
        #endIf
      #endFor
      stack = "\tFrame stack (most recent call first):\n%s" % stack
    except:
      # This shouldn't happen, but in case it does...
      exc_type,exc_value = sys.exc_info()[:2]
      stack = "\tException getting frame stack. Type: %s, Value: %s\n%s" % (exc_type,exc_value,stack)
    #endTry

    try:
      tb = sys.exc_info()[2]
      stackList = traceback.extract_tb(tb,depth)
      for stackData in stackList:
        sourcefile,line,function,text = stackData
        sepIndex = sourcefile.rfind(os.sep)
        if (sepIndex >=0 and Trace.SourceFileStyle == Trace.NameOnly):
          sourcefile = sourcefile[sepIndex+1:]
        #endIf
        if (text == None):
          stack = "\t%s(%s) [%s]\n%s" % (sourcefile,line,function,stack)
        else:
          stack = "\t%s(%s) [%s] - %s\n%s" % (sourcefile,line,function,text,stack)
        #endIf
      #endFor
      stack = "\tException stack (most recent call first):\n%s" % stack
    except:
      # This shouldn't happen, but in case it does...
      exc_type,exc_value = sys.exc_info()[:2]
      stack = "\tException getting exception stack. Type: %s, Value: %s\n%s" % (exc_type,exc_value,stack)
    #endTry
    
    # At the very top - put the exception string
    stack = "\t%s\n%s" % (exc,stack)
    
    return stack	
  #endDef

  
  def _exceptionStackBTT(self,methodName,exc,depth=10):
    """
      Return a string useable for output to stdout or a log file that provides a representation
      of the "exception stack" and the "frame stack" from "bottom to top" (BTT).
      The "exception stack" captures the code tree from main to where the exception was raised and 
      is usually the most interesting part of the stack.  The "frame stack" captures the code
      from the point to where the exception was caught. 
      
      Displaying the stack from bottom to top in an output log or stdout is the style in which
      Jython/Python displays the stack by default.
      
      There is another method named _exceptionStackTTB() that can be used to create a string that
      represents the execution stack from top to bottom, which is the style that Java uses.
    """
    stack = ""
    # Reconstruct the call stack from where the trace of the exception was initiated by invoking 
    # Trace.error() or Trace.severe().
    stackList = traceback.extract_stack()
    try:
      stack = "\tFrame stack (most recent call last):\n"
      for stackData in stackList:
        sourcefile,line,function,text = stackData
        if (sourcefile.endswith("Trace.py") and (function == "error" or function == "severe")): break
        sepIndex = sourcefile.rfind(os.sep)
        if (sepIndex >=0 and Trace.SourceFileStyle == Trace.NameOnly):
          sourcefile = sourcefile[sepIndex+1:]
        #endIf
        if (text == None):
          stack = "%s\t%s(%s) [%s]\n" % (stack,sourcefile,line,function)
        else:
          stack = "%s\t%s(%s) [%s] - %s\n" % (stack,sourcefile,line,function,text)
        #endIf
      #endFor
    except:
      # This shouldn't happen, but in case it does...
      exc_type,exc_value = sys.exc_info()[:2]
      stack = "%s\n\tException getting frame stack. Type: %s, Value: %s" % (stack,exc_type,exc_value)
    #endTry
    
    try:
      stack = "%s\tException stack (most recent call last):\n" % stack
      tb = sys.exc_info()[2]
      stackList = traceback.extract_tb(tb,depth)
      for stackData in stackList:
        sourcefile,line,function,text = stackData
        sepIndex = sourcefile.rfind(os.sep)
        if (sepIndex >=0 and Trace.SourceFileStyle == Trace.NameOnly):
          sourcefile = sourcefile[sepIndex+1:]
        #endIf
        if (text == None):
          stack = "%s\t%s(%s) [%s]\n" % (stack,sourcefile,line,function)
        else:        
          stack = "%s\t%s(%s) [%s] - %s\n" % (stack,sourcefile,line,function,text)
        #endIf
      #endFor
    except:
      # This shouldn't happen, but in case it does...
      exc_type,exc_value = sys.exc_info()[:2]
      stack = "%s\tException getting exception stack. Type: %s, Value: %s\n" % (stack,exc_type,exc_value)
    #endTry

    # At the very end - put the exception string
    stack = "%s\t%s" % (stack,exc)
    
    return stack  
  #endDef

  
  # The _log() method is the heart of the tracing mechanism. All of the public trace 
  # methods invoke _log().
  # 
  # If exc is not None, then the exception message and stack is included in the trace 
  # message.
  #
  # If a log file has been configured, then all trace goes to the log file.  Any trace 
  # with eventType Info or "lower" also goes to stdout.
  #
  # The format of the trace line is:
  # [<datetimestamp>] <threadid> T <modulename>(<linenumber>) <methodname> : <message>
  #   where T is a one character event type
  #
  # NOTE: <modulename> does not get truncated as in WAS trace.  We opted to emit the 
  # entire module name to make it easy to determine which script file is emitting the
  # the trace.
  #
  # NOTE: In oder to avoid message and stack dump getting split up, the output
  # operation is done in one call to print.  Otherwise in multi-threaded scenarios
  # another thread may jump in to do output.  John Martinek discovered this issue
  # when working with some multi-threaded Jython scripts.
  #
  def _log(self,methodName,eventType,msg,exc=None):
    """
      Emit the trace message to stdout and optionally to a trace file when a trace file 
      has been defined.
       
      All public Trace methods that emit trace messages go through _log() to actually 
      emit the trace in order to correctly unwind the call stack as well as to emit trace 
      in a thread safe manor.
    """    
    stackDump = None
    threadId = ("%x" % thread.get_ident()).rjust(12).replace(" ","0")
    traceString = "%s %s %s %s" % (self._getTimeStamp(),threadId,eventType,self.entityName)
    traceString = "%s(%s) %s" % (traceString,self._sourceLineNumber(),methodName)
    
    if (exc):
      # Get stack dump now to keep it with msg text
      if (Trace.StackTraceStyle == Trace.TopToBottom):
        stackDump = self._exceptionStackTTB(methodName,exc)
      elif (Trace.StackTraceStyle == Trace.BottomToTop):
        stackDump = self._exceptionStackBTT(methodName,exc)
      else:
        raise TraceConfigurationException("'%s', is not a valid stack trace style. Expected one of %s" % (Trace.StackTraceStyle,Trace.StackTraceStyles))
      #endIf
    #endIf
    
    # If a logFile was provided then send all trace to trace log
    if (Trace.traceFile):
      # file IO is not thread safe
      # The Jython 2.1 that comes with WAS doesn't support the "with" statement.
      try:
        Trace.traceFileLock.acquire()
        if (stackDump):
          Trace.traceFile.write("%s : %s\n%s\n" % (traceString, msg, stackDump))
        else:
          Trace.traceFile.write("%s : %s\n" % (traceString, msg))
        #endIf
        Trace.traceFile.flush()
      finally:
        Trace.traceFileLock.release()
      #endTry
    #endIf
    
    if (not Trace.traceFile or eventType in ["S", "E", "W", "I"]):
      # Send severe, error, warning and info trace to stdout
      if (stackDump):
        print "%s : %s\n%s" % (traceString, msg, stackDump)
      else:
        print "%s : %s" % (traceString, msg)
      #endIf
    #endIf
  #endDef
  
  
  def isLoggable(self,level):
    if (type(level) == type(0)):
      if (self._isTraceLevel(level)):
        result = level <= self.traceLevel
      else:
        # level is a number but not in the range of a trace level.
        raise TraceLevelException("Invalid trace level: %s  Valid trace levels range from 0 (none) to 7 (finest)" % level)
      #endIf
    elif (type(level) == type("") or type(level) == type(u"")):
      level = self._coerceLevel(level)
      result = level <= self.traceLevel
    else:
      # Odd case where level is unexpected type
      raise TraceLevelException("Trace level must be either an integer or a string.  Use levels defined by the Level class.")
    #endIf
    return result
  #endDef


  def entering(self,methodName):
    if (self.traceLevel >= Level.FINE):
      self._log(methodName,">","Entry")
    #endIf
  #endDef

  
  def exiting(self,methodName):
    if (self.traceLevel >= Level.FINE):
      self._log(methodName,"<","Exit")
    #endIf
  #endDef


  # severe() emits as long as trace is on
  # The event type is "S" for severe.
  def severe(self,methodName,msg,exc=None):
    if (self.traceLevel > Level.NONE):
      self._log(methodName,"S",msg,exc)
    #endIf
  #endDef


  # Synonym for severe() for backward compatibility with 
  # original Trace class.
  # The event type for error is "E".
  def error(self,methodName,msg,exc=None):
    if (self.traceLevel > Level.NONE):
      self._log(methodName,"E",msg,exc)
    #endIf
  #endDef

  
  def warn(self,methodName,msg):
    if (self.traceLevel > Level.SEVERE):
      self._log(methodName,"W",msg)
    #endIf
  #endDef


  # Synonym for warn() to conform to Java Logger
  def warning(self,methodName,msg):
    if (self.traceLevel > Level.SEVERE):
      self._log(methodName,"W",msg)
    #endIf
  #endDef

    
  def info(self,methodName,msg):    
    if (self.traceLevel > Level.WARN):
      self._log(methodName,"I",msg)
    #endIf
  #endDef


  def config(self,methodName,msg):
    if (self.traceLevel > Level.INFO):
      self._log(methodName,"C",msg)
    #endIf
  #endDef

  
  def fine(self,methodName,msg):
    if (self.traceLevel > Level.CONFIG):
      self._log(methodName,"1",msg)
    #endIf
  #endDef

  
  def finer(self,methodName,msg):
    if (self.traceLevel > Level.FINE):
      self._log(methodName,"2",msg)
    #endIf
  #endDef

  
  def finest(self,methodName,msg):
    if (self.traceLevel > Level.FINER):
      self._log(methodName,"3",msg)
    #endIf
  #endDef


  # debug() is a synonym for finest() to conform to Java Logger.
  def debug(self,methodName,msg):
    if (self.traceLevel > Level.FINER):
      self._log(methodName,"3",msg)
    #endIf
  #endDef
  
  
  def setTraceLevel (self,level):
    """
      Set the trace level for this instance of Trace to the given level.
    
      The given level may be a Jython string that is a valid trace level as determined
      by the _coerceLevel() method.  Or the given level may be an integer constant that 
      is one of the levels defined in the Level class.
    """
    if (type(level) == type("") or type(level) == type(u"")):
      if (level):
        level = self._coerceLevel(level)
        self.traceLevel = level
      #endIf
    elif (type(level) == type(0)):
      if (self._isTraceLevel(level)):
        self.traceLevel = level
      else:
        # level is a number but not in the range of a trace level.
        raise TraceLevelException("Invalid trace level: %s  Valid trace levels are defined by the Level class." % level)
      #endIf
    else:
      # Odd case where level is unexpected type
      raise TraceLevelException("Trace level must be either a string or an integer.  Use levels defined by the Level class.")
    #endIf
  #endDef  

  def getTraceLevel(self): 
    return self.traceLevel 
  #endDef
  
    
  def _getTimeStamp(self):
    now = datetime.datetime.now()
    return "[%s %s]" % (now.strftime("%y/%m/%d %H:%M:%S.%f"),TimeZoneName)
  #endDef
  
  # The stack frame has a method that returns the line number
  # The _sourceFrame() method steps back through the stack frames
  # to the frame that called the trace method, which is referred  
  # to as the "source" frame.  The trace method calls _log() which
  # calls _sourceLineNumber() so to get back to the source frame
  # you have to walk 4 frames back.
  #
  def _sourceFrame(self):
    """
      Return the frame object for the caller's stack frame.
    """
    try:
        raise Exception('catch me')  # forced exception to get stack traceback
    except:
        exc_traceback = sys.exc_info()[2]
        return exc_traceback.tb_frame.f_back.f_back.f_back.f_back
    #endTry
  #endDef
  
  def _sourceLineNumber(self):
    lineno = self._sourceFrame().f_lineno
    return str(lineno)
  #endDef
  
  def configureTrace(self,traceString):
    """
      The configureTrace() method defined for the Trace class is a convenience wrapper 
      around the configureTrace() method defined for the Trace module. It is often the
      case that a Trace class instance is readily available to use for "global" trace
      configuration.
    """
    configureTrace(traceString)
  #endDef
  
#endClass

##################################################################################################
# Module Methods

def openTraceLog(logPath):
  if (Trace.traceFile != None):
    Trace.traceFile.close()
  #endIf
  Trace.traceFile = open(logPath,"w")
#endDef

def appendTraceLog(logPath):
  if (Trace.traceFile != None):
    Trace.traceFile.close()
  #endIf
  Trace.traceFile = open(logPath,"a")
#endDef


def closeTraceLog():
  if (Trace.traceFile != None):
    Trace.traceFile.close()
  #endIf
#endDef


def parseTraceString(traceString):
  """
    Return a list of TraceSpecification instances that represent a parsing of the given trace string.
    The returned list holds a TraceSpecifification instance for each trace specification in the given 
    trace string.
  """
  result = []
  # If the given traceString is enclosed in double-quotes,
  # then strip the double-quotes.
  if (traceString[0] == '"' and traceString[-1] == '"'):
    traceString = traceString[1:-1]
  #endIf
  traceStrings = traceString.split(":")
  for trace in traceStrings:
    traceParts = trace.split("=")
    if (len(traceParts) != 2):
      raise TraceSpecificationException("Encountered an invalid trace string: %s  A trace string looks like <module_pattern>=<level>." % trace)
    #endIf
    
    modulePattern = traceParts[0]
    level = traceParts[1]
    result.append(TraceSpecification(modulePattern,level))
  #endFor
  return result
#endDef


def setTraceSpec(traceString):
  """
    Given a trace specification string, set the module traceSpec used by all instances of Trace.
  """
  
  if (not traceString):
    raise Exception("The traceString argument must be a non-empty string.")
  #endIf
  
  Trace.traceSpec = parseTraceString(traceString)
  Trace.traceString = traceString
#endDef


def getTraceSpec():
  """
    Return the module traceSpec used by all instances of Trace.
  """
  return Trace.traceSpec
#endDef


def configureTrace(traceString):
  """
    Set the global trace specification based on the given trace string.
    Loop through all registered modules and set their trace class trace level based on 
    the given trace string if the module name matches one of the module patterns in the 
    given trace string.
  """
  
  setTraceSpec(traceString)
  registeredModules = Trace.tracedEntities.keys()
  for module in registeredModules:
    for spec in Trace.traceSpec:
      if (spec.compiledRegex.match(module)):
        trace = Trace.tracedEntities[module]
        trace.setTraceLevel(spec.level)
        break
      #endIf
    #endFor
  #endFor
#endDef
