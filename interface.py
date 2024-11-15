"""Main interface."""
import socket
import select
import os
import json
from threading import Thread
import time
from numpy import iterable
import numpy as np

import version
from camera_info import CameraInfo
from exposure_info import ExposureInfo
# Instantiate a global object of the CameraInfo class. This
# carries default and current camera settings (mode, type, etc.)

default_interface_config = os.path.join(version.CONFIG_DIR, "interface.json")
default_host_config = os.path.join(version.CONFIG_DIR, "hosts.json")


class Interface:
    """Interface class"""

    def __init__(self, verbose=True,
                 interface_config_file=default_interface_config,
                 host_config_file=default_host_config):

        # read interface
        with open(interface_config_file) as icfgf:
            camera_interface = json.load(icfgf)
        self.interface = camera_interface["interface"]
        if "archon" in self.interface:
            self.archon = True
            self.device_list = []
        else:
            self.archon = False
            self.device_list = camera_interface["device_list"]

        # read hosts
        with open(host_config_file) as hcfgf:
            hosts = json.load(hcfgf)
        self.hosts = hosts

        self.caminfo = CameraInfo()
        self.expinfo = ExposureInfo()
        self.verbose = verbose
        self.number_of_connections = 0

        self.set_verbosity(verbose)

        if self.verbose:
            print("pycamerad version: ", version.__version__)
            print("interface:", self.interface)
            self.print_settings()


    # --------------------------------------------------------------------------
    # @fn     verbose
    # --------------------------------------------------------------------------
    def set_verbosity(self, verbosity):
        """
        Enable or disable verbose printing messages, mostly interactions
        between the host and the CCD controlers.

        Args:
            verbosity: True or False
        """
        self.verbose = verbosity
        if self.verbose:
            print("verbose is on")


    # --------------------------------------------------------------------------
    # @fn     print_settings
    # @brief  print the observation settings
    # --------------------------------------------------------------------------
    def print_settings(self):
        """
        Print the current camera settings
        """
        if self.archon:
            print("  mode          = '%s'" % self.caminfo.get_mode())
        print("  basename      = '%s'" % self.caminfo.get_basename())
        print("  type          = '%s'" % self.expinfo.get_type())
        print("  exptime       = %d" % self.expinfo.get_exptime())

    # --------------------------------------------------------------------------
    # @fn     camerad_open
    # --------------------------------------------------------------------------
    def camerad_open(self, hostlist=None):
        """
        Open connection to camera and initialize CCD controllers using the
        default parameters specified in the archon.cfg configuration
        file. This includes loading the ACF file, setting the mode to
        DEFAULT, the type to TEST, and powering on the controllers.  By
        default, this opens connections to all hosts (cameras 1-4).  To
        open only to the local host, use hostlist='local'
        """

        if hostlist is None:
            hostlist = list(self.hosts.keys())
        if hostlist == "local":
            hostlist = ["localhost"]

        if not iterable(hostlist):
            hostlist = [hostlist]

        # open sockets to camera servers indicated by hostlist
        for host in hostlist:
            if self.verbose:
                print("connecting to %s: %s %d" % (host, self.hosts[host]["ip"],
                                                   self.hosts[host]["port"]))
            self.hosts[host]["socket"] = socket.socket(socket.AF_INET,
                                                       socket.SOCK_STREAM)
            self.hosts[host]["socket"].connect((self.hosts[host]["ip"],
                                                self.hosts[host]["port"]))
            self.number_of_connections += 1

        # send open to all connections
        error = self.__send_command("open")[0]

        if error == 0:
            print("connected to camerad")
        else:
            print("Error opening connection to camerad")

        return error


    # --------------------------------------------------------------------------
    # @fn     close
    # --------------------------------------------------------------------------
    def close(self):
        """
        close connection to camera
        """

        # send the camera close command to each host
        #
        error = self.__send_command("close")[0]

        # then close sockets to camera servers that were opened.
        #
        for host in self.hosts:
            if self.verbose:
                print("closing connection to %s: %s" % (host,
                                                        self.hosts[host]["ip"]))
            self.hosts[host]["socket"].close()
            del self.hosts[host]["socket"]
            self.number_of_connections -= 1
        if error == 0:
            print("camera closed")

        return error


    # --------------------------------------------------------------------------
    # @fn     load
    # --------------------------------------------------------------------------
    def load(self, acffile=None):
        """
        load ACF file
        """
        print("loading default firmware file...")

        if acffile is None:
            print("loading default acf file...")
            error = self.__send_command("load")[0]
        else:
            acffile = os.path.abspath(os.path.expanduser(acffile))
            print("loading input acf file: %s" % acffile)
            error = self.__send_command("load", acffile)[0]

        if error == 0:
            self.caminfo.set_acf_file(acffile)
            print("acf file loaded")
        else:
            print("ERROR: load acf file failed")

        return error


    # --------------------------------------------------------------------------
    # @fn     readparam
    # --------------------------------------------------------------------------
    def get_param(self, paramname):
        """
        Read a parameter directly from Archon configuration memory.

        Args:
            paramname
        Returns:
            tuple of the form (error,returnvalue)

            where a non-zero value for error is an error (0=okay)
            and returnvalue is the value of the parameter, if successful.
        """
        try:
            error, retval = self.__send_command("getp", paramname)
        except:
            error = 1
            retval = None
            print("ERROR: get_param() camera exception")

        return error, retval


    # --------------------------------------------------------------------------
    # @fn     set_param
    # --------------------------------------------------------------------------
    def set_param(self, param, value):
        """
        set arbitrary parameter
        Args:
            param: parameter to set (in quotes)
            value: new value for parameter
        """
        error = self.__send_command("setp", param, value)[0]
        if error == 0:
            if self.verbose:
                print("loaded parameter")
        else:
            print("error loading parameter (%s=%d)" % (param, value))
        return error


    # --------------------------------------------------------------------------
    # @fn     set_mode
    # --------------------------------------------------------------------------
    def set_mode(self, mode_in):
        """
        Set camera mode.
        -------------------------------------------------
        """
        old_mode = self.caminfo.get_mode()

        if old_mode != mode_in:
            error = self.__send_command("mode", mode_in)[0]
            if not error:
                print("MODE changed: %s -> %s" % (old_mode, mode_in))
                self.caminfo.set_mode(mode_in)
            else:
                print("ERROR setting mode to %s" % mode_in)
        else:
            print("using mode %s" % mode_in)
            error = 0
        return error


    # --------------------------------------------------------------------------
    # @fn     set_type
    # --------------------------------------------------------------------------
    def set_type(self, imtype):
        """
        Set image type.
        Here for backward-compatibility with ZTF scripts.
        This has no functionality.
        -------------------------------------------------
        """
        old_type = self.expinfo.get_type()
        if old_type != imtype:
            error = self.__send_command("key",
                                        "IMTYPE=%s//Image type" % imtype)[0]
            if not error:
                error = self.expinfo.set_type(imtype)
                print("IMTYPE set to %s" % imtype)
            else:
                print("ERROR setting type to %s" % imtype)
        else:
            error = 0
        return error


    # --------------------------------------------------------------------------
    # @fn     set_basename
    # --------------------------------------------------------------------------
    def set_basename(self, basename):
        """
        Set image name to be used for the next exposure.
        An empty string is NOT allowed.
        This is called "set_basename" for backwards-compatibility with ZTF scripts.
        """
        if not basename:
            print("ERROR: basename cannot be empty")
            return 1
        old_basename = self.caminfo.get_basename()
        if old_basename != basename:
            error = self.__send_command("basename", basename)[0]
            if not error:
                error = self.caminfo.set_basename(basename)
                print("BASENAME changed: %s -> %s" % (old_basename, basename))
            else:
                print("ERROR setting basename to %s" % basename)
        else:
            error = 0
        return error


    # --------------------------------------------------------------------------
    # @fn     set_power
    # --------------------------------------------------------------------------
    def set_power(self, power):
        """
        Set Archon power (i.e. send POWERON or POWEROFF native command).
        Acceptable values are: "ON" or "OFF".
        """
        old_power_on = self.caminfo.get_power()

        if power == "ON" and not old_power_on:
            if self.archon:
                print("turning on Archon power...")
                error = self.__send_command("POWERON")[0]
            else:
                print("turning on ARC power...")
                error = self.__send_command("native", "PON")

        elif power == "OFF" and old_power_on:
            if self.archon:
                print("turning off Archon power...")
                error = self.__send_command("POWEROFF")[0]
            else:
                print("turning off ARC power...")
                error = self.__send_command("native","POF")
        else:
            print("unrecognized power argument", power)
            error = 1

        if error:
            print(
                f"ERROR setting {'Archon' if self.archon else 'ARC'} power "
                f"to {power}")
        else:
            print(f"set {'Archon' if self.archon else 'ARC'} power to {power}")
            self.caminfo.set_power_on(power == "ON")

        return error


    # --------------------------------------------------------------------------
    # @fn     expose
    # --------------------------------------------------------------------------
    def expose(self, exptime=0, iterations=1):
        """
        Take an exposure, or multiple exposures if "iterations" is specified.

        This is essentially a macro, calling the following functions on the server:
        expose(), readframe(), and writeframe()
        """
        self.expinfo.set_exptime(exptime)
        self.expinfo.set_iterations(iterations)

        print("starting %d exposures" % iterations)
        error = self.__send_command("expose", iterations)[0]

        return error


    # --------------------------------------------------------------------------
    # @fn     __send_threaded_command
    # @brief  formats and sends command to camera, called in a separate thread
    #
    # This is an internal package function, not meant to be called by the user.
    # --------------------------------------------------------------------------
    def __send_threaded_command(self, host, command):
        if self.verbose:
            print(
                'sending "%s" to %s (%s, %d)'
                % (command, host, self.hosts[host]["ip"],
                   self.hosts[host]["port"])
            )
        try:
            self.hosts[host]["socket"].sendall(command.encode())
        except:
            print("unable to send command. host may be down.")


    # --------------------------------------------------------------------------
    # @fn     __send_command
    # @brief  send a command
    #
    # This is an internal package function, not meant to be called by the user.
    # Function returns tuple: (error,returnvalue) for commands which may have
    # a return value. If calling where a returnvalue is not expected, then call
    # with error=__send_command(...)[0] (for example).
    # --------------------------------------------------------------------------
    def __send_command(self, *arg_list):
        # stopwatch = []
        # stopwatch.append(time.time())
        endchar='\n'
        numcams = 0  # number of cameras in the set
        numcomplete = 0  # number of cameras reported complete
        numokay = 0  # number of cameras reported without error
        errno = 0   # error number: 0 - no error
        threads = []
        sendsocket = []
        sendname = []
        returnlist = []

        command = []
        for arg in arg_list:
            command.append(str(arg))
        command = " ".join(command) + endchar

        if self.number_of_connections <= 0:
            print("ERROR: no connected sockets")
            return 1, ""

        # loop through the set of cameras,
        # send command to each in a separate thread
        for host in self.hosts:
            if "socket" not in self.hosts[host]:
                continue
            # create list by socket and name of cameras that are sent a command
            csock = self.hosts[host]["socket"]
            print(csock)
            sendsocket.append(csock)
            sendname.append(host)
            # count up the number of cameras that are sent a command
            numcams += 1
            thr = Thread(target=self.__send_threaded_command, args=(host, command))
            thr.start()
            threads.append(thr)

        # join threads
        for thr in threads:
            thr.join()

        # loop through the set of cameras to which a command was sent,
        # and read back the replies
        returnvalue = None
        for cam in range(0, numcams):
            dat = {}
            error = {}
            message = []

            # read the first 4 bytes which give the message length
            while True:
                try:
                    ready = select.select([sendsocket[cam]], [], [], 10)
                    print(numcams)
                except select.error:
                    print("select error")
                    break
                if ready[0]:
                    ret = sendsocket[cam].recv(1024).decode()
                else:
                    print("select timeout")
                    message.append("\n")
                    break
                if "DONE" in ret or "ERROR" in ret or "\n" in ret:
                    message.append(ret)
                    break

            # dat contains the entire message
            dat[cam] = message

            #       pdb.set_trace()
            returnvalue = dat[cam][0].split()[0]

            # Create a list of the return values from each camera
            returnlist.append(returnvalue)

            #       # pick apart the message to get just the error number
            #       # (sometimes the error value is empty, so catch ValueError)
            #       if (len(dat[ii][0].split()) >= 3):
            #           try:
            #               error[ii] = int( dat[ii][0].split()[2] )
            #           except ValueError:
            #               error[ii] = 1

            # is the word "DONE" somewhere in the response?
            complete = "".join(dat[cam]).find("DONE")
            #       pdb.set_trace()
            if complete >= 0:
                if self.verbose:
                    print("%s complete" % sendname[cam])
                # increment number reported complete
                numcomplete += 1
                # increment number reported without error
                numokay += 1
            else:
                if self.verbose:
                    print(
                        "%s not complete, error %d [%s]"
                        % (sendname[cam], error[cam], "error")
                    )

        # Check that each camera returned the same value.
        # If not, that is an error condition and return a list of the return values
        for i, ret in enumerate(returnlist):
            for j in range(i + 1, len(returnlist)):
                if ret != returnlist[j]:
                    numcams = -1

        # stopwatch.append(time.time())
        # stopwatch = np.diff(np.array(stopwatch))
        # print "dt = ",
        # for dt in stopwatch:
        #     print "%.2f, "%(dt*1e3),
        # print "\b\b\b ms"

        # number of completes-without-error must equal number of cameras
        if numcams == numokay:
            if self.verbose:
                print("OK")
            ret = returnvalue

        # return a list of the return values, if not all the same
        elif numcams == -1:
            print("error: different return values")
            errno = 1
            ret = returnlist

        # something went wrong
        else:
            print("error sending command")
            errno = 1
            ret = ""

        return errno, ret

    # Code after here is to make the magic board work.
    # That is, create and write bitstreams
    # -----------------------------------------------------------------------------
    # @fn     __write_bits(BITSTRING)
    # @brief  writes a bitstring to the magic board serial register where bitstring
    #           is a string
    #         of bits that will be written to the SR in right to left order
    # -----------------------------------------------------------------------------
    def __write_bits(self, bitstring):
        # '10111001010011010'
        if self.verbose:
            print("Writing bits:", end=" ")
        for bitlevel in reversed(bitstring):
            # set param is now in the same file
            self.set_param("BitLevel", int(bitlevel) + 1)
            if self.verbose:
                print("%d" % int(bitlevel), end=" ")
        if self.verbose:
            print("")

    # -----------------------------------------------------------------------------
    # @fn     __make_bitstring(identifier)
    # @brief  generate bitstring from identifier (NAME,chan) tuple or list.
    #         NAME in {'driver','dnl','hvlc','hvhc','adc'}
    #         ch in {0..n}
    # I believe this bitstream is created due to magic board layout
    # -----------------------------------------------------------------------------
    def __make_bitstring(self, identifier):

        (name, chan) = identifier
        ret = "0"

        if name.lower() == "driver":
            ret = "{0:06b}".format(np.mod(chan, 24))
        elif name.lower() == "dnl":
            ret = "{0:06b}".format(24)
        elif name.lower() == "hvlc":
            ret = "{0:06b}".format(32 + np.mod(chan, 24))
        elif name.lower() == "hvhc":
            ret = "{0:06b}".format(56 + np.mod(chan, 6))
        elif name.lower() == "adc":
            ret = "{0:016b}".format(2 ** np.mod(chan, 16))
        elif name.lower() == "null":
            if chan == 16:
                ret = "{0:016b}".format(0)
            else:
                ret = "{0:06b}".format(25)
        else:
            print("Unrecognized identifier name in __make_bitstring.  returning 0")

        return ret


    # -----------------------------------------------------------------------------
    # -----------------------------------------------------------------------------
    def magicboard(
        self,
        acf_file,
        p_in,
        n_in,
        p_out,
        n_out,
        iterations=1,
        read_cds=False,
        timeit=False,
        delay=0,
    ):
        """Write I/O setup for magic board, then run ACF file Inputs have the
        form ({'driver','dnl','hv[hl]c','adc'},{0..n}).  Channel #'s are
        mod-ed by the number of channels available. IN and OUT are from the
        board's perspective.

            delay: wait time [s] between load and first write bit.

            Note: use 'none' or any invalid file name for "acf_file" to circumvent
                    reloading of the acf.

        """
        # check number of iterations
        if iterations < 0:
            # error = 1
            print("iterations must be >=0")

        if read_cds:
            runthismode = "DEFAULT"
        else:
            runthismode = "RAW"

        error = 0

        if os.path.isfile(os.path.expanduser(acf_file)):
            error = self.load(acf_file)  # load in now in same file
        if error:
            print("load('%s') failed" % acf_file)
            return error
        error = self.set_mode(runthismode)
        if error:
            print("set_mode('%s') failed" % runthismode)
            return error
        error = self.set_type("TEST")
        if error:
            print("set_type('TEST') failed")
            return error
        error = self.set_basename("magic")
        if error:
            print("set_basename('magic') failed")
            return error
        # optional delay time for long startup sequences
        time.sleep(delay)

        # write to the magic board to configure I/O
        time_0 = time.time()
        self.__write_bits(self.__make_bitstring(p_in))  # +
        self.__write_bits(self.__make_bitstring(n_in))  # +
        self.__write_bits(self.__make_bitstring(p_out))  # +
        self.__write_bits(self.__make_bitstring(n_out))  # +
        self.__write_bits("0100")  # junk bits
        if timeit:
            print("Time to write 48 bits: %.3f sec" % (time.time() - time_0))

        self.expose(0, iterations)  # expose is now in same file

        return error
