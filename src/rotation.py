# -*- coding: utf-8 -*-
import dbus
from dbus.mainloop.qt import DBusQtMainLoop

try:
  import osso
  OSSO = True
except ImportError:
  OSSO = False


"""
Classe adaptada da original utilizada no gPodder.
"""
class FremantleRotation(object):
    """thp's screen rotation for Maemo 5

    Simply instantiate an object of this class and let it auto-rotate
    your StackableWindows depending on the device orientation.

    If you need to relayout a window, connect to its "configure-event"
    signal and measure the ratio of width/height and relayout for that.

    You can set the mode for rotation to AUTOMATIC (default), NEVER or
    ALWAYS with the set_mode() method.
    """
    AUTOMATIC, NEVER, ALWAYS = range(3)

    # Privately-used constants
    _PORTRAIT, _LANDSCAPE = ('portrait', 'landscape')
    _ENABLE_ACCEL = 'req_accelerometer_enable'
    _DISABLE_ACCEL = 'req_accelerometer_disable'

    # Defined in mce/dbus-names.h
    _MCE_SERVICE = 'com.nokia.mce'
    _MCE_REQUEST_PATH = '/com/nokia/mce/request'
    _MCE_REQUEST_IF = 'com.nokia.mce.request'

    def __init__(self, system_bus, app_name, version='1.0', mode=0, cb = None):
        """Create a new rotation manager

        app_name    ... The name of your application (for osso.Context)
        main_window ... The root window (optional, hildon.StackableWindow)
        version     ... The version of your application (optional, string)
        mode        ... Initial mode for this manager (default: AUTOMATIC)
        """
        self._callback = cb
        self._orientation = None
        self._mode = -1
        self._last_dbus_orientation = None
        app_id = '-'.join((app_name, self.__class__.__name__))
        if OSSO:
          self._osso_context = osso.Context(app_id, version, False)

        #loop = DBusQtMainLoop(set_as_default=True)
        #system_bus = dbus.SystemBus(mainloop=loop)
        system_bus.add_signal_receiver(self._on_orientation_signal, \
                signal_name='sig_device_orientation_ind', \
                dbus_interface='com.nokia.mce.signal', \
                path='/com/nokia/mce/signal')
        self.set_mode(mode)

    def get_orientation(self):
        """Get the rotation
        """
        return self._orientation

    def get_mode(self):
        """Get the currently-set rotation mode

        This will return one of three values: AUTOMATIC, ALWAYS or NEVER.
        """
        return self._mode

    def set_mode(self, new_mode):
        """Set the rotation mode

        You can set the rotation mode to AUTOMATIC (use hardware rotation
        info), ALWAYS (force portrait) and NEVER (force landscape).
        """
        if new_mode not in (self.AUTOMATIC, self.ALWAYS, self.NEVER):
            raise ValueError('Unknown rotation mode')

        if self._mode != new_mode:
            if self._mode == self.AUTOMATIC:
                # Remember the current "automatic" orientation for later
                self._last_dbus_orientation = self._orientation
                # Tell MCE that we don't need the accelerometer anymore
                self._send_mce_request(self._DISABLE_ACCEL)

            if new_mode == self.NEVER:
                self._orientation_changed(self._LANDSCAPE)
            elif new_mode == self.ALWAYS:
                self._orientation_changed(self._PORTRAIT)
            elif new_mode == self.AUTOMATIC:
                # Restore the last-known "automatic" orientation
                self._orientation_changed(self._last_dbus_orientation)
                # Tell MCE that we need the accelerometer again
                self._send_mce_request(self._ENABLE_ACCEL)

            self._mode = new_mode

    def _send_mce_request(self, request):
        if OSSO:
          rpc = osso.Rpc(self._osso_context)
          rpc.rpc_run(self._MCE_SERVICE, \
                      self._MCE_REQUEST_PATH, \
                      self._MCE_REQUEST_IF, \
                      request, \
                      use_system_bus=True)

    def _orientation_changed(self, orientation):
        if self._orientation == orientation:
            # Ignore repeated requests
            return

        self._orientation = orientation
        self._callback(self._orientation)

    def _on_orientation_signal(self, orientation, stand, face, x, y, z):
        if orientation in (self._PORTRAIT, self._LANDSCAPE):
            if self._mode == self.AUTOMATIC:
                # Automatically set the rotation based on hardware orientation
                self._orientation_changed(orientation)
            else:
                # Ignore orientation changes for non-automatic modes, but save
                # the current orientation for "automatic" mode later on
                self._last_dbus_orientation = orientation
