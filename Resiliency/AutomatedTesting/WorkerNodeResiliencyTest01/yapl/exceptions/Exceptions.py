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

class NotImplementedException(Exception):
  """
    The NotImplementedException is intended for use in code blocks where some function is not implemented.
    This serves as a way to do something explicit where code could be written to implement some function
    or feature, but was not.  The reason for non-implementation could be simply lack of time or lack of a
    requirement for such code.  The script library is a constantly evolving body of code that is being 
    developed on an as-needed basis.  Hence there are occasions when something is not implemented but it 
    is desirable to fail explicitly in a particular code path rather than implicitly in some unexpected
    code path.
  """
#endClass


class ExitException(Exception):
  """
    ExitException is used to jump to the end of a method that wraps its body 
    in a try-except.  This is useful for cases where some condition arises 
    that is not necessarily an error, but the path of execution should jump
    to the exit of the method.
  """
#endClass


class FileNotFoundException(Exception):
  """
    FileNotFoundException is raised when a file that is expected to exist at 
    a given path does not actually exist.
  """
#endClass


class FileTransferException(Exception):
  """
    FileTransferException is raised when there is a problem transferring a file from
    some source to some destination.
  """
#endClass


class InvalidArgumentException(Exception):
  """
    InvalidArgumentException is raised when the value of an argument provided is not
    "valid" for some reason, e.g., it is out of range or an incorrect type.
  """
#endClass


class MissingArgumentException(Exception):
  """
    The MissingArgumentException is thrown when a "required" keyword argument is not provided 
    with a non-empty value.  The scripts in the library make heavy use of keyword arguments 
    rather than positional arguments, but those arguments are often still required to be provided
    with some value.  Usually the keyword argument default value is the empty string, but 
    occasionally None is also used as a default value.  The caller must provide a non-empty
    value on method invocation.
  """
#endClass

class AttributeValueException(Exception):
  """
    The AttributeValueException is raised when an attribute value of an object is None or has
    a value that is not of the proper type or within the proper range.  In short, this exception
    is intended to be raised for any issue discovered with an attribute value.  The built-in
    Python AttributeError exception is more low level than AttributeValueException in that 
    the object supports the given attribute in question, it's just that the value is not
    as expected. 
  """
#endClass

class JSONException(Exception):
  """
    JSONException is raised when there is some problem consuming a JSON document or 
    converting a Python object into its corresponding JSON document.
  """
#endClass

