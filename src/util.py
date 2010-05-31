# -*- coding: utf-8 -*-
import sys
import os
from PyQt4.QtGui import *


def getIcon(icon):
  return QIcon(os.path.join(sys.path[0], "icons", icon))
