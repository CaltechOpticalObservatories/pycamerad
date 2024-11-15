"""Information specific to the exposure

    This includes:
        exptime:
        iterations:
        imtype:

"""
# --------------------------------------------------------------------------
# @file:     exposure_info.py
# @brief:    ExposureInfo class
# @author:   Don Neill <neill@astro.caltech.edu>
# @date:     2024-11-14
#
# The ExposureInfo class stores and retrieves current settings for
# the exposure.
# --------------------------------------------------------------------------
class ExposureInfo:
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
        imtype=TYPE["TEST"],
        iterations=1,
        exptime=0,
    ):
        """
        initialize the class
        """
        self.imtype = imtype
        self.iterations = iterations
        self.exptime = exptime


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
