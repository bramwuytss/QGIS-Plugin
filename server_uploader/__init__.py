# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Server_uploader
                                 A QGIS plugin
 Upload to a server
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2024-05-14
        copyright            : (C) 2024 by /
        email                : bram2605@hotmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load Server_uploader class from file Server_uploader.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .Server_uploader import Server_uploader
    return Server_uploader(iface)
