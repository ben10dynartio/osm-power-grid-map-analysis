import sys

print(sys.path)

from qgis.core import QgsApplication


# Supply path to qgis install location
QgsApplication.setPrefixPath("/usr/bin/qgis", True)


# Create a reference to the QgsApplication.  Setting the

# second argument to False disables the GUI.

qgs = QgsApplication([], False)


# Load providers

qgs.initQgis()


# Write your code here to load some layers, use processing

# algorithms, etc.


# Finally, exitQgis() is called to remove the

# provider and layer registries from memory

qgs.exitQgis()