###############################################################################
# Licensed Material - Property of IBM
# 5724-I63, 5724-H88, (C) Copyright IBM Corp. 2016 - All Rights Reserved.
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
###############################################################################

'''
Created on Dec 7, 2016

@author: Peter Van Sickel pvs@us.ibm.com
'''

import sys, re, os.path
import time
import shutil

'''
  StringSeparators is the default list of characters that are used to separate names
  in a string representation of a list of names. 
  The following list is comma,space,semi-colon,colon
'''
StringSeparators = ", ;:"

def stringType(x):
  """
    Return True if the given object x is a string type, i.e., unicode string or "regular" string.
  """
  isinstance(x, (str, unicode))
#endDef


# Found this on stackoverflow
currentTimeMillis = lambda: int(round(time.time() * 1000))


def toBoolean (arg):
  """
    Return True or False depending on the value of arg.
 
    Canonicalize all the ways you can think of representing a boolean into a 1 or 0.  
    This is convenient for use with values that ultimately originated from a user, e.g., 
    from a property file where the user may enter y, yes, n, no, t, f
    etc, to represent true or false.
 
  """
  if (not arg): return False
  if (arg == 1): return True
  if (isinstance(arg, (str, unicode))):
    if (re.match('^(true|t|yes|y|1)$', arg, flags=re.IGNORECASE)): return True
    if (re.match('^(false|f|no|n|0)$', arg, flags=re.IGNORECASE)): return False
  #endIf
  raise Exception("toBoolean: Unknown boolean value: %s" % arg)
#endDef


def getInputArgs(argsSignature,args=None):
  """
    Return a dictionary with the strings in sys.argv processed as name-value pairs or "switch" keyword args.
    
    NOTE: When running wsadmin, sys.argv[0] is the first actual argument, not the name of the script being invoked.
    However, when running with Jython directly, the first argument is the name of the Jython script.  An exception 
    will be raised because if the name of the script is not listed in the argsSignature dictionary.  The simplest 
    thing to do when running with Jython directly is to pass in sys.argv[1:].
              
    Input: An args "signature" dictionary with the keyword entries in it and the expected type of the argument value. 
    The recognized types are:
        string, integer, int, float, boolean and switch.
  
    A "switch" type argument is one that is a keyword only and doesn't have a value.  If it is present in the argv list, 
    a boolean true (1) is assigned to its corresponding arg name.

    The keywords in the arg signature are assumed to begin with a dash (-) or a double dash (--).  (The double dash is 
    occasionally necessary to avoid conflicts with the wsadmin command line args, e.g. --help to emit usage info. The
    dashes are stripped off to create an arg name when assigning key-value pairs in the output dictionary of actual args.

    If a string type keyword appears more than once in the argsv[] array, then a list of values for that keyword is created 
    for that entry in the output dictionary.  This is handy for writing scripts where you want to be able to allow the user 
    repeat a particular argument multiple times so as to provide a list.  The other approach to providing a list is to use a 
    comma or space separated string and then create the list with split.  We didn't provide this capability for the other 
    types of arguments since we couldn't come up with a realistic scenario for passing in a list of numbers or booleans 
    using multiple keyword args.  If we do, we'll modify the method.

    NOTE: If a script has all optional arguments then the args argument may end up being the empty list.  We explicitly check 
    for args == None to cover cases where no args at all are passed in and in that case sys.argv is used for args. Be careful 
    when using Jython directly, because sys.argv[0] holds the name of the Jython script.  It is recommended that the caller pass 
    in sys.argv[1:] when running with Jython directly.  When running with wsadmin, the first element in sys.argv is stripped off 
    by wsadmin.

  """
  if (args == None):
    # assume it is appropriate to default to sys.argv
    args = sys.argv
  #endIf
  
  argsDict = {}
  i = 0
  while (i < len(args)):
    keyword = args[i]

    if (not argsSignature.has_key(keyword)):
      raise Exception("Unknown command line argument: %s" % keyword)
    
    if (keyword.startswith("--")):
      argName = keyword[2:len(keyword)] # strip the leading dashes
    else:
      argName = keyword[1:len(keyword)] # strip single leading dash
    #endIf

    if (argsSignature[keyword] == 'string'):
      i += 1  # index of arg value
      argValue = args[i]
      # If argValue is enclosed in double-quotes, strip the double-quotes.
      # This handles cases where incoming args from a shell are quoted to
      # avoid evaluation of shell special characters, e.g., *
      if (argValue[0] == '"' and argValue[-1] == '"'):
        argValue = argValue[1:-1]
      #endIf
      currentValue = argsDict.get(argName)
      if (currentValue != None):
        if (type(currentValue) == type([])):
          # current value already a list
          argsDict[argName] = currentValue.append(argValue)
        else:
          # current value is a string, so make a list
          argsDict[argName] = [currentValue, argValue]
        #endIf
      else:
        argsDict[argName] = argValue
      #endIf
    elif (argsSignature[keyword] == 'integer' or argsSignature[keyword] == 'int'):
      i += 1
      argsDict[argName] = int(args[i])
    elif (argsSignature[keyword] == 'float'):
      i += 1
      argsDict[argName] = float(args[i])
    elif (argsSignature[keyword] == 'boolean'):
      i += 1
      argsDict[argName] = toBoolean(args[i])
    elif (argsSignature[keyword] == 'switch'):
      # for a "switch" type arg, the index doesn't get advanced
      argsDict[argName] = True
    else:
      raise Exception("Unknown argument type in command line argument signature: %s" % argsSignature[keyword])
    
    i += 1  # index of next keyword
  #endWhile

  return argsDict
#endDef


def getValue(args,synonyms,default=None):
  """
    Return the value from the given args dictionary for the attribute name in the list of given synonym names.
    
    args is a dictionary (A "rest args" argument dictionary can be passed in directly as well, e.g., **restArgs 
    may be passed in as restArgs.)
    
    synonyms is a Jython list of names (strings) that may be used to access entries in the args dictionary.
    synonyms may also be a string with separators as defined in NameSeparators.
    
    The getValue() method is a convenience for getting a value for a dictionary where there is more than one
    name that may be used for the entry in the dictionary.  In the case of the application definition dictionary
    there are several attributes that may be referred to with more than one name.  (The argument names used by  
    the wsadmin AdminApp methods are often inconsistent with respect to naming conventions. This module provides 
    more readable aliases for many of the AdminApp method argument names.)
  """
  value = None
  
  if (type(synonyms) != type([])):     
    synonyms = splitString(synonyms)
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


def splitString(string,separators=StringSeparators):
  """
    The splitString() method is used to create a Jython list from a string of whatever
    is passed in the string.  This could be a list of names or a list of numbers and names
    or whatever.  The string argument can be an string that contains an arbitrary set of 
    substrings separated by the given separators.  
    
    It is often convenient to use a string to represent a list, e.g., on the command line.  
    The separator within that string can be any of the characters provided in the separators 
    argument. The separators argument defaults to those defined in the NameSeparators global 
    for this module. 
    
    The splitString method originated as support for things coming in on the command
    line to a top level script or from a properties file where a multi-valued property
    is needed.
    
    The given string is split into a list based on the separators provided.  Separators 
    defaults to NameSeparators which is comma (,) or space ( ) or a plus (+) character 
    in that order of precedence. If the given string has a comma character in it, the 
    split is done on the comma character. If the given string has a space character in 
    it the split is done on the space character, etc.
    
    NOTE: If the items in the string list have space characters in them, then
    obviously + or , needs to be used to delimit the different items in the
    string.  
    
    With respect to WAS configuration objects we strongly advise against 
    using names that have space characters in the name. Using spaces in names leads 
    to nothing but headaches in scripting.
    
    NOTE: If the incoming string doesn't have any of the separator characters in it, 
    the result is a list with the incoming things string as the only member.  This is 
    behavior patterned after the way the Jython split() method works.
    
    NOTE: To avoid situations where extra space characters are included or somehow 
    an empty item resulted from the split operation, a "clean-up" step is done at the end 
    to filter out any empty values and to strip white space off the items in the result list.  
    This takes care of strings that look like "foo, bar, baz" which would result in 
    ['foo', ' bar', ' baz'] which isn't likely what is wanted.  It also takes care of something 
    that happens to have a double space in it such as "foo  bar baz" which would result in 
    ['foo', '', 'bar', 'baz'] which also isn't likely what is wanted.
  """
  result = []
  
  if (string):
    for char in separators:
      if (string.find(char) > 0):
        result = string.split(char)
        break
      #endIf
    #endFor
  
    if (not result):
      result = [string]
    #endIf
  
    # clean out empty items and any leading or trailing white space
    # on the items in the result list.
    result = [name.strip() for name in result if name]
    
  #endIf
  
  return result
#endDef


def replaceTextInFile(self, filePath, text, newText):
  """
    In the given file with path, filePath, replace text with newText.
  """
  try:
    tempPath = "%s.temp" % filePath
    backupPath = "%s.bak" % filePath
    shutil.copyfile(filePath,backupPath)
    with open(filePath,'r') as originalFile, open(tempPath,'w') as tempFile:
      for line in originalFile:
        tempFile.write(line.replace(text, newText))
      #endFor
    #endWith
    os.rename(tempPath,filePath)
    os.remove(backupPath)
  except Exception as e:
    if (os.path.exists(tempPath)): os.remove(tempPath)
    os.rename(backupPath,filePath)
    raise e
  #endTry

#endDef


def showFile(path):
  """
    The showFile() method opens the given file for reading and writes it out to stdout.  
    This is intended for use with help text files for scripts that want to show usage 
    information to the user.
  """
  if (not path):
    raise Exception("The given path for the file to show is empty or None.")
  #endIf
  
  try:
    fileToShow = open(path,"r")
    line = fileToShow.readline()
    while line:
      sys.stdout.write(line)
      sys.stdout.flush()
      line = fileToShow.readline()
    #endWhile
  except Exception, e:
    raise e
  #endTry
#endDef


def listFilesOfType(pathName,extension):
  """
    Return a Jython list that contains either a single full path to a file or a list of
    full paths to files.  If the given pathName is a file, then it is checked to confirm
    that the file has the given extension.  If the given pathName is a directory, then
    a listing of that directory is taken and a sorted list is returned with all the file  
    paths for all of the files in that directory with the given extension. 
    
    NOTE: extension may or may not include the the leading dot character, i.e., 
    it is ok to pass in .json or json.  If the dot is not present it will be added.
    The os.path.splitext() method includes the dot character.

    NOTE: If extension is None it is converted to the empty string and files with
    no extension are returned in a list.  Extension may also be passed in as the
    empty string to achieve the same effect.
    
    This method is convenient for use in a top level script where a given argument may
    represent a path a single file for for processing, or a directory with one or more 
    files for processing by that script.
    
    The listFilesOfType does not descend the directory tree rooted at pathName when 
    pathName is a directory.  It only looks at files in the top level of the directory 
    referenced by pathName. <TBD>Are there use cases for doing a recursive descent?
  """
  if (not pathName):
    raise Exception("The path name to a directory or file (pathName) cannot be empty or None.")
  #endIf
  
  if (extension == None): extension = ''

  if (extension):
    if (extension[0] != '.'):
      extension = ".%s" % extension
    #endIf
  #endIf
  
  filePaths = []
  if (os.path.isfile(pathName)):
    ext = os.path.splitext(pathName)[1]
    if (ext == extension):
      filePaths.append(pathName)
    #endIf
  elif (os.path.isdir(pathName)):
    # Note os.listdir() result is not sorted
    dirListing = os.listdir(pathName)
    for x in dirListing:
      xpath = os.path.join(pathName,x)
      if (os.path.isfile(xpath)):
        ext = os.path.splitext(xpath)[1]
        if (ext == extension):
          filePaths.append(xpath)
        #endIf
      #endIf
    #endFor
  else:
    raise Exception("Unexpected type for pathName: '%s'.  Expected file or directory." % pathName)
  #endIf
  filePaths.sort()
  return filePaths
#endDef


def hashFile(filePath, hasher, blocksize=65536):
  """
    Return a hex digest for the given file defined at filePath.
    The hasher argument is a hash function from the hashlib library.
    
    A call to hashFile() looks like:
      hashSum = hashFile("Some/file/path",hashlib.sha256())
      hashSum = hashFile("Some/other/file/path",hashlib.md5())
    
    This method is based on a method found in a Stack Overflow posting:
    http://stackoverflow.com/questions/3431825/generating-an-md5-checksum-of-a-file
    
    WARNING: Make sure you pass a new instance of a hasher on every call.  
    A hasher creates a hash based on the stream of bytes input to its update() method
    during the lifetime of the hasher instance.
    See: http://stackoverflow.com/questions/31778444/md5-hashing-with-hashlib-produces-inconsistencies
    Do not provide a default value for the hasher argument as the instance lives
    across method calls.  The hasher must be passed in from the caller.
  """
  if (not os.path.exists(filePath)):
    raise Exception("File: %s does not exist." % filePath)
  #endIf
  
  with open(filePath, 'rb') as afile:
    buf = afile.read(blocksize)
    while len(buf) > 0:
      hasher.update(buf)
      buf = afile.read(blocksize)
    #endWhile
  #endWith
  return hasher.hexdigest()
#endDef