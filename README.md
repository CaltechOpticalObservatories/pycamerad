# pycamerad

**pycamerad** is a Python interface to detector controllers using the camera-interface server. Originally adapted from CESL (**C**amera **E**xternal **S**cripting **L**anguage), it was initially developed for the Zwicky Transient Facility (ZTF). This library retains many of ZTF's unique features to ensure compatibility with existing scripts.

## Reporting Issues
If you encounter any problems or have questions about this project, please open an issue on the [GitHub Issues page](https://github.com/CaltechOpticalObservatories/pycamerad/issues). Your feedback helps us improve the project!

## Usage
To use pycamerad, start Python (or iPython) and import the interface as shown below:

```python
import pycamerad.interface as cam
```
Note: The alias cam is used here for demonstration purposes and can be replaced with any name of your choice.

## Example
Here is a brief example demonstrating how to use the pycamerad interface:

```python
import pycamerad.interface as cam

# Display help information for the module
help(cam)

# Example output:
# Help on module pycamerad.interface in pycamerad:
#
# NAME
#    pycamerad.interface
#
# FILE
#    /path/to/pycamerad/interface.py
#
# FUNCTIONS
#    close()
#        Close connection to camera

```

## Contributing
We welcome contributions to the pycamerad project. If you would like to contribute, please fork the repository and submit a pull request with your changes. For major changes, please open an issue first to discuss what you would like to change.

## Acknowledgements
pycamerad was adapted from CESL, which was initially developed for ZTF. We would like to thank the ZTF team for their contributions.
