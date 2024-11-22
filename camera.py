""" Camera class """
import os
import json
from interface import Interface
from exposure import Exposure
import version

default_host_config = os.path.join(version.CONFIG_DIR, "hosts.json")

class Camera(Interface, Exposure):

    verbose = False

    def __init__(self, verbose=True, host_config_file=default_host_config):

        super().__init__(verbose, host_config_file)

        self.verbose = verbose
        # read hosts
        with open(host_config_file) as hcfgf:
            hosts = json.load(hcfgf)
        self.hosts = hosts
