"""Information specific to the camera

    This includes:
        interface: either "archon" or "arc"
        device_list: a list of interger device numbers: for "arc" controllers only
        power_commands: list of power control strings (2) for "arc" controllers only
        basename: the base name of the file

"""
# --------------------------------------------------------------------------
# @file:     camera_info.py
# @brief:    CameraInfo class
# @author:   David Hale <dhale@caltech.edu>
# @date:     2017-02-15
# @modified: 2017-02-22 DH allow basename=""
# @modified: 2017-03-22 DH implement setting noisebits for FITS compression
# @modified: 2024-11-08 DN update for py3 and rename project to pycamerad
# @modified: 2024-11-14 DN remove functions not related to the camera
#
# The CameraInfo class stores and retrieves current settings for
# the camera module of the ztf package.
# --------------------------------------------------------------------------
class CameraInfo:
    """
    This is the CameraInfo class, which is used to store
    and retrieve current settings, in particular the
    camera mode, image type, basename, and exposure time.

    This is for internal use only by the camera module.
    The user should never need to look in here.
    """

    def __init__(
        self,
        interface="archon",
        mode="DEFAULT",
        basename="",
        power_on=False,
        acf_file="DEFAULT"
    ):
        """
        initialize the class
        """
        self.interface = interface
        self.mode = mode
        self.basename = basename
        self.power_on = power_on
        self.acf_file = acf_file

    def get_basename(self):
        """
        Return the base name.
        """
        return self.basename

    def get_mode(self):
        """
        Return the camera mode as a string.
        """
        return self.mode

    def get_power(self):
        """
        Returns: True if power on, otherwise False.
        """
        return self.power_on
    def get_acf_file(self):
        """
        Returns: acf file
        """
        return self.acf_file

    def set_basename(self, basename):
        """
        Set the basename.
        """
        self.basename = basename
        return 0

    def set_mode(self, mode_in):
        """
        Set the camera mode.
        Allow any mode here. The server will do the error checking.
        """
        self.mode = mode_in
        return 0

    def set_power_on(self, power_on):
        """
        Set the power on.
        Args:
            power_on: True or False
        """
        self.power_on = power_on
        return 0

    def set_acf_file(self, acf_file):
        """
        Set the acf file.
        Args:
            acf_file:
        """
        self.acf_file = acf_file
