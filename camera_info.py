# --------------------------------------------------------------------------
# @file:     camera_info.py
# @brief:    CameraInfo class
# @author:   David Hale <dhale@caltech.edu>
# @date:     2017-02-15
# @modified: 2017-02-22 DH allow basename=""
# @modified: 2017-03-22 DH  implement setting noisebits for FITS compression
# @modified: 2024-11-08 DN  update for py3 and rename project to pycamerad
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

    # codes for types
    #
    TYPE = {
        "OBJECT": 0,
        "BIAS": 1,
        "DARK": 2,
        "DOME_FLAT": 3,
        "TWILIGHT_FLAT": 4,
        "FOCUS": 5,
        "POINTING": 6,
        "TEST": 7,
        "ILLUMINATION": 8,
        "FRINGE": 9,
        "SEEING": 10,
        "OTHER": 11,
    }
    TYPE_NAME = {v: k for k, v in TYPE.items()}

    def __init__(
        self,
        interface="archon",
        mode="DEFAULT",
        imtype=TYPE["TEST"],
        basename="",
        iterations=1,
        exptime=0,
    ):
        """
        initialize the class
        """
        self.interface = interface
        self.mode = mode
        self.imtype = imtype
        self.basename = basename
        self.iterations = iterations
        self.exptime = exptime


    def get_basename(self):
        """
        Return the base name.
        """
        return self.basename

    def get_exptime(self):
        """
        Return the exposure time.
        """
        return self.exptime

    def get_iterations(self):
        """
        Return the iterations
        """
        return self.iterations

    def get_type(self):
        """
        Return the image type as a string.
        """
        return self.TYPE_NAME[self.imtype]

    def get_mode(self):
        """
        Return the camera mode as a string.
        """
        return self.mode

    def set_type(self, imtype):
        """
        Set the image type.
        """
        retval = 0
        if imtype in self.TYPE.keys():
            self.imtype = self.TYPE[imtype]
        else:
            print("  valid CameraInfo types:", end=" ")
            print(self.TYPE.keys())
            retval = 1

        return retval

    def set_mode(self, mode_in):
        """
        Set the camera mode.
        Allow any mode here. The server will do the error checking.
        """
        self.mode = mode_in
        return 0

    def set_exptime(self, exptime):
        """
        Set the exposure time.
        """
        retval = 0
        if exptime >= 0:
            self.exptime = exptime
        else:
            print("  exptime must be >= 0")
            retval = 1

        return retval

    def set_iterations(self, iterations):
        """
        Set the iterations
        """
        retval = 0
        if iterations > 0:
            self.iterations = iterations
        else:
            print("  iterations must be > 0")
            retval = 1

        return retval

    def set_basename(self, basename):
        """
        Set the basename.
        """
        self.basename = basename
        return 0
