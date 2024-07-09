from pdb import set_trace

from PyQt5.QtCore import pyqtRemoveInputHook

def breakpoint():
  '''Set a tracepoint in the Python debugger that works with Qt'''

  pyqtRemoveInputHook()
  set_trace()
