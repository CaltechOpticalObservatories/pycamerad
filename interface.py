"""Main interface."""
import socket
import select
import os
from threading import Thread
from datetime import datetime, timezone
import time
from numpy import iterable
import numpy as np
# from IPython.core.debugger import Tracer
# import pdb # use with pdb.set_trace()

import hosts
from camera_info import CameraInfo
# Instantiate a global object of the CameraInfo class. This
# carries default and current camera settings (mode, type, etc.)
#
caminfo = CameraInfo()

# the default verbose level. Extremely verbose when True.
__VERBOSE = False


# --------------------------------------------------------------------------
# @fn     verbose
# --------------------------------------------------------------------------
def set_verbosity(verbosity):
    """
    Enable or disable verbose printing messages, mostly interactions
    between the host and the CCD controlers.

    Args:
        verbosity: True or False
    """
    global __VERBOSE
    __VERBOSE = verbosity
    if __VERBOSE:
        print("verbose is on")


# --------------------------------------------------------------------------
# @fn     print_settings
# @brief  print the observation settings
# --------------------------------------------------------------------------
def print_settings():
    """
    Print the current camera settings
    """
    print("  mode          = '%s'" % caminfo.get_mode())
    print("  basename      = '%s'" % caminfo.get_basename())
    print("  type          = '%s'" % caminfo.get_type())
    print("  exptime       = %d" % caminfo.get_exptime())
    print("  compression   = '%s'" % caminfo.get_compression_type())
    print("  noisebits     = %d  " % caminfo.get_compression_noisebits())


# --------------------------------------------------------------------------
# @fn     camerad_open
# --------------------------------------------------------------------------
def camerad_open(hostlist=None, do_load=True, do_power_on=True, do_setup=True,
                verbose=__VERBOSE):
    """
    Open connection to camera and initialize CCD controllers using the
    default parameters specified in the archon.cfg configuration
    file. This includes loading the ACF file, setting the mode to
    DEFAULT, the type to TEST, and powering on the controllers.  By
    default, this opens connections to all hosts (cameras 1-4).  To
    open only to the local host, use hostlist='local'
    """

    if hostlist is None:
        hostlist = [1]
    if hostlist == "local":
        hostlist = ["localhost",]

    if not iterable(hostlist):
        hostlist = [hostlist]

    # open sockets to camera servers indicated by hostlist
    for host in hosts.camhost:
        if verbose:
            print("connecting to %s: %s" % (hosts.camname[host],
                                            hosts.camport[host]))
        hosts.camsocket[host] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        hosts.camsocket[host].connect((hosts.camhost[host], hosts.camport[host]))

    error = __send_command("open")[0]

    try:
        if do_load:
            if error == 0:
                print("loading default acf file...")
                error = __send_command("load")[0]
            if do_power_on:
                if error == 0:
                    print("turning power on...")
                    error = __send_command("POWERON")[0]
            else:
                print("Skipping POWERON...")
            if do_setup:
                if error == 0:
                    caminfo.__init__()  # re-initializes the camera mode state
                    error = __setup_observation()
                if error == 0:
                    print("camera initialized")
                else:
                    print("ERROR: %d initializing camera" % error)
            else:
                print("Skipping setup...")
        else:
            print("Skipping load acf, power on and setup")
    except:
        error = 1
        print("ERROR: camerad_open() camera exception")

    return error


# --------------------------------------------------------------------------
# @fn     close
# --------------------------------------------------------------------------
def close(verbose=__VERBOSE):
    """
    close connection to camera
    """

    # send the camera close command to each host
    #
    error = __send_command("close")[0]

    # then close sockets to camera servers that were opened.
    #
    if not hosts.camsocket:  # but not if nothing is defined
        return
    for host in hosts.camhost:
        if verbose:
            print("closing connection to %s: %s" % (hosts.camname[host],
                                                    hosts.camhost[host]))
        hosts.camsocket[host].close()
        del hosts.camsocket[host]
    if error == 0:
        print("camera closed")

    return error


# --------------------------------------------------------------------------
# @fn     load
# --------------------------------------------------------------------------
def load(acffile, mode="DEFAULT", basename="", imtype="TEST", power="ON"):
    """
    load ACF file
    """

    print("DEBUG: load() incomming mode=", mode)

    acffile = os.path.abspath(os.path.expanduser(acffile))

    # update caminfo with values passed in here
    caminfo.set_mode(mode)
    caminfo.set_basename(basename)
    caminfo.set_type(imtype)

    try:
        print("loading acf file...")
        error = __send_command("load", acffile)[0]
        if power == "ON":
            if error == 0:
                print("turning on power...")
                error = __send_command("POWERON")[0]
        elif power == "OFF":
            if error == 0:
                print("turning off power...")
                error = __send_command("POWEROFF")[0]
        else:
            print("unrecognized power argument", power)
            error = 1
        if error == 0:
            error = __setup_observation()
        if error == 0:
            print("camera initialized")
        else:
            print("ERROR: initializing camera")
    except:
        error = 1
        print("ERROR: load() camera exception")

    return error


# --------------------------------------------------------------------------
# @fn     readparam
# --------------------------------------------------------------------------
def readparam(paramname):
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
        error, retval = __send_command("getp", paramname)
    except:
        error = 1
        retval = None
        print("ERROR: readparam() camera exception")

    return error, retval


# --------------------------------------------------------------------------
# @fn     set_param
# --------------------------------------------------------------------------
def set_param(param, value, verbose=__VERBOSE):
    """
    set arbitrary parameter
    Args:
        param: parameter to set (in quotes)
        value: new value for parameter
    """
    error = __send_command("setp", param, value)[0]
    if error == 0:
        if not verbose:
            print("loaded parameter")
    else:
        print("error loading parameter (%s=%d)" % (param, value))
    return error


# --------------------------------------------------------------------------
# @fn     set_mode
# --------------------------------------------------------------------------
def set_mode(mode_in):
    """
    Set camera mode.
    -------------------------------------------------
    """
    old_mode = caminfo.get_mode()

    if old_mode != mode_in:
        error = __send_command("mode", mode_in)[0]
        if not error:
            print("MODE changed: %s -> %s" % (old_mode, mode_in))
            caminfo.set_mode(mode_in)
        else:
            print("ERROR setting mode to %s" % mode_in)
    else:
        print("using mode %s" % mode_in)
        error = 0
    return error


# --------------------------------------------------------------------------
# @fn     set_type
# --------------------------------------------------------------------------
def set_type(imtype):
    """
    Set image type.
    Here for backward-compatibility with ZTF scripts.
    This has no functionality.
    -------------------------------------------------
    """
    old_type = caminfo.get_type()
    if old_type != imtype:
        error = caminfo.set_type(imtype)
    #       if not error:
    #           error = __setup_observation(quiet=True)
    #       if not error:
    #           print "IMAGE TYPE changed: %s -> %s"%(old_type,imtype)
    else:
        error = 0
    return error


# --------------------------------------------------------------------------
# @fn     set_basename
# --------------------------------------------------------------------------
def set_basename(basename):
    """
    Set image name to be used for the next exposure.
    An empty string is NOT allowed.
    This is called "set_basename" for backwards-compatibility with ZTF scripts.
    """
    basenamechars = len(basename.split())
    if basenamechars < 1:
        print("error: basename cannot be empty")
        return 1
    old_basename = caminfo.get_basename()
    if old_basename != basename:
        error = caminfo.set_basename(basename)
        if not error:
            error = __send_command("basename", basename)[0]
        if not error:
            print("BASENAME changed: %s -> %s" % (old_basename, basename))
    else:
        error = 0
    return error


# --------------------------------------------------------------------------
# @fn     set_power
# --------------------------------------------------------------------------
def set_power(power):
    """
    Set Archon power (i.e. send POWERON or POWEROFF native command).
    Acceptable values are: "ON" or "OFF".
    """
    if power == "ON":
        print("turning on power...")
        error = __send_command("POWERON")[0]
    elif power == "OFF":
        print("turning off power...")
        error = __send_command("POWEROFF")[0]
    else:
        print("unrecognized power argument", power)
        error = None

    return error


# --------------------------------------------------------------------------
# @fn     set_compression
# --------------------------------------------------------------------------
def set_compression(ctype, *noisebits):
    """
    Here for backward-compatibility with ZTF scripts.
    This has no functionality.
    ---------------------------------------------------------------------
    Set FITS compression type and optionally noisebits. Acceptable types:
    NONE, RICE, GZIP, PLIO
    An optional second parameter may be given, specifying the noisebits
    for floating-point compression. If not specified then the last value
    is used. The default is 4.
    """
    if ctype:
        pass
    if noisebits:
        pass
    #   if noisebits:
    #       noisebits = int(noisebits[0])
    #   else:
    #       noisebits = caminfo.get_compression_noisebits()

    #   old_type      = caminfo.get_compression_type()
    #   old_noisebits = caminfo.get_compression_noisebits()

    #   if (old_type != ctype) or (old_noisebits != noisebits):
    #       error = caminfo.set_compression(ctype, noisebits)
    #       if not error:
    #           error = __send_command(commands.FITS_COMPRESSION,
    #                                  caminfo.compression,
    #                                  caminfo.noisebits)[0]
    #       if not error:
    #           print "COMPRESSION changed: %s,%s -> %s,%s" %
    #              (old_type, old_noisebits, ctype, noisebits)
    #   else:
    #       error = 0
    #   return error
    return 0


# --------------------------------------------------------------------------
# @fn     expose
# --------------------------------------------------------------------------
def expose(exptime=0, iterations=1):
    """
    Take an exposure, or multiple exposures if "iterations" is specified.
    "delay" specifies idle time between exposures in seconds.

    This is essentially a macro, calling the following functions on the server:
    expose(), readframe(), and writeframe()
    """
    # mode = caminfo.get_mode()

    caminfo.set_exptime(exptime)

    print("starting exposure")
    error = __send_command("expose", iterations)[0]

    return error


# --------------------------------------------------------------------------
# @fn     __send_threaded_command
# @brief  formats and sends command to camera, called in a separate thread
#
# This is an internal package function, not meant to be called by the user.
# --------------------------------------------------------------------------
def __send_threaded_command(hostnum, command, verbose=__VERBOSE):
    if verbose:
        print(
            'sending "%s" to %s (%s, %d)'
            % (command, hosts.camname[hostnum], hosts.camhost[hostnum],
               hosts.camport[hostnum])
        )
    try:
        hosts.camsocket[hostnum].sendall(command.encode())
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
def __send_command(*arg_list, verbose=__VERBOSE):
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

    if not hosts.camsocket:
        print("ERROR: no connected sockets")
        return 1, ""

    # loop through the set of cameras,
    # send command to each in a separate thread
    for csock in hosts.camsocket:
        # create list by socket and name of cameras that are sent a command
        print(hosts.camsocket[csock])
        sendsocket.append(hosts.camsocket[csock])
        sendname.append(hosts.camname[csock])
        # count up the number of cameras that are sent a command
        numcams += 1
        thr = Thread(target=__send_threaded_command, args=(csock, command))
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
            if verbose:
                print("%s complete" % sendname[cam])
            # increment number reported complete
            numcomplete += 1
            # increment number reported without error
            numokay += 1
        else:
            if verbose:
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
        if verbose:
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

# --------------------------------------------------------------------------
# @fn     __setup_observation
# @brief  setup observation
#
# This is an internal package function, not meant to be called by the user.
# --------------------------------------------------------------------------
def __setup_observation(quiet=False):

    print("CAMERA_SETUP_OBSERVATION...")
    print("DEBUG: setup_observation incoming mode=", caminfo.get_mode())
    if not quiet:
        print_settings()

    # At minimum, always use YYYYMMDD_hhmmss as the image root name, even
    # if "basename" is empty (note that image_name can never be empty).
    # If basename is not empty then the timestamp is added to it.

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    if caminfo.get_basename() != "":
        image_name = caminfo.get_basename() + "_" + timestamp
    else:
        image_name = timestamp

    error = __send_command("basename", image_name)[0]
    if error == 0:
        error = __send_command("exptime", caminfo.exptime)[0]
    if error == 0:
        error = __send_command("mode", caminfo.get_mode())[0]
    return error


# Code after here is to make the magic board work.
# That is, create and write bitstreams


# -----------------------------------------------------------------------------
# @fn     __write_bits(BITSTRING)
# @brief  writes a bitstring to the magic board serial register where bitstring
#           is a string
#         of bits that will be written to the SR in right to left order
# -----------------------------------------------------------------------------
def __write_bits(bitstring, verbose=True):
    # '10111001010011010'
    if verbose:
        print("Writing bits:", end=" ")
    for bitlevel in reversed(bitstring):
        # set param is now in the same file
        set_param("BitLevel", int(bitlevel) + 1)
        if verbose:
            print("%d" % int(bitlevel), end=" ")
    if verbose:
        print("")

# -----------------------------------------------------------------------------
# @fn     __make_bitstring(identifier)
# @brief  generate bitstring from identifier (NAME,chan) tuple or list.
#         NAME in {'driver','dnl','hvlc','hvhc','adc'}
#         ch in {0..n}
# I believe this bitstream is created due to magic board layout
# -----------------------------------------------------------------------------
def __make_bitstring(identifier):

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
    set_compression("NONE")  # set_compression is now in the same file

    if os.path.isfile(os.path.expanduser(acf_file)):
        error = load(acf_file, mode=runthismode)  # load in now in same file
    if error:
        print("ztf.camera.load('%s') failed" % acf_file)
        return error
    if error == 0:
        error = set_type("TEST")
        print("Set type: ")
        print(error)
    if error == 0:
        error = set_basename("zzmagic")
        print("Set basename: ")
        print(error)
    # optional delay time for long startup sequences
    time.sleep(delay)

    # write to the magic board to configure I/O
    time_0 = time.time()
    __write_bits(__make_bitstring(p_in))  # +
    __write_bits(__make_bitstring(n_in))  # +
    __write_bits(__make_bitstring(p_out))  # +
    __write_bits(__make_bitstring(n_out))  # +
    __write_bits("0100")  # junk bits
    if timeit:
        print("Time to write 48 bits: %.3f sec" % (time.time() - time_0))

    expose(0, iterations)  # expose is now in same file

    return error


# -----------------------------------------------------------------------------
# @fn     run
# @brief  take an exposure
#
# specify the acf file name if you want it to load.
# -----------------------------------------------------------------------------
def run(
    acf_file="none",
    iterations=1,
    read_cds=False,
    exptime=0,
    timeit=False,
    basename="zztf",
):

    if iterations <= 0:  # check number of iterations
        # error = 1
        print("iterations must be >0")
    if read_cds:
        runthismode = "DEFAULT"
    else:
        runthismode = "RAW"

    error = 0
    set_compression("NONE")
    time_0 = time.time()
    # if the parameter acf_file is not set, don't load anything
    if os.path.isfile(os.path.expanduser(acf_file)):
        error = load(acf_file, mode=runthismode)
    if error == 0:
        error = set_type("TEST")
    if error == 0:
        error = set_basename(basename)

    # perform <iterations> of test "exposures."
    # all exposures go into the same fits file
    expose(exptime, iterations)

    if timeit:
        print("completed in %.2f" % (time.time() - time_0))

    return error
