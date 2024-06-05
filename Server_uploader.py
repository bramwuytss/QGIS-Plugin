# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Server_uploader
                                 A QGIS plugin
 Upload to a server
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-05-14
        git sha              : $Format:%H$
        copyright            : (C) 2024 by /
        email                : bram2605@hotmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon, QPixmap
from qgis.PyQt.QtWidgets import QAction, QPushButton, QTextEdit, QHBoxLayout, QLabel, QVBoxLayout, QWidget
from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsGeometry, QgsProject, QgsCoordinateReferenceSystem, QgsCoordinateTransformContext, QgsWkbTypes, QgsVectorFileWriter, QgsSymbol, QgsSingleSymbolRenderer
from PyQt5.QtGui import QColor
from qgis.PyQt.QtCore import QVariant
from PyQt5.QtCore import QVariant
from shapely.geometry import shape, mapping
from shapely import wkt
import os
from qgis.PyQt.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
import requests
import json
import tempfile
import shutil
import sys
#from typing import Dict, List, Union
from shapely.wkt import loads as wkt_loads

#from dataclasses import dataclass



# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .Server_uploader_dialog import Server_uploaderDialog
import os.path

# @dataclass
# class DataQualityError:
#     geom: str
#     error_message: str
#     severity: int
#
# @dataclass
# class DataQualityCheckResult:
#     name: str
#     status: str ##enum
#     errors: List[DataQualityError]

class Server_uploader:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'Server_uploader_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Server_uploader')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Server_uploader', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/Server_uploader/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Server_uploader'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Server_uploader'),
                action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = Server_uploaderDialog()

            # Connect the check_button_clicked method to the button's clicked signal
            check_button = self.dlg.findChild(QPushButton, "Check")  # Find the button by object name
            check_button.clicked.connect(self.check_button_clicked)

            # Connect the upload_to_server_button_clicked method to the button's clicked signal
            upload_button = self.dlg.findChild(QPushButton, "Upload_to_server")  # Find the button by object name
            upload_button.clicked.connect(self.upload_to_server_button_clicked)

            self.textbox1 = self.dlg.TextBox1

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass

    # def run_quality_checks(self) -> List[DataQualityCheckResult]:
    #     raise NotImplementedError("still to do")

    def check_unique_ids(self, layer):
        """Check that all 'feeder_id' values are unique."""
        errors = []
        idx = layer.fields().indexFromName('feeder_id')
        feeder_id_counts = {}

        for feature in layer.getFeatures():
            value = feature.attributes()[idx]
            if isinstance(value, QVariant):
                value = None
            if value is not None and value != '' and value != 'NULL':
                if value in feeder_id_counts:
                    feeder_id_counts[value].append(feature)
                else:
                    feeder_id_counts[value] = [feature]

        for features in feeder_id_counts.values():
            if len(features) > 1:
                errors.extend(features)

        return errors
    def check_non_null_ids(self, layer):
        """Check that all 'feeder_id' values are not NULL."""
        errors = []
        idx = layer.fields().indexFromName('feeder_id')

        for feature in layer.getFeatures():
            value = feature.attributes()[idx]
            if isinstance(value, QVariant):
                value = None
            if value is None or value == '' or value == 'NULL':
                errors.append(feature)

        return errors

    def create_error_layer(self, layer_name, original_layer, error_features):
        """Create a new error layer and add it to the Errors group."""
        if not error_features:
            print(f"No error features to add for {layer_name}")
            return

        error_layer = QgsVectorLayer(QgsWkbTypes.displayString(original_layer.wkbType()), layer_name, "memory")

        # Set CRS to match the original layer
        error_layer.setCrs(original_layer.crs())

        provider = error_layer.dataProvider()
        provider.addAttributes(original_layer.fields())
        error_layer.updateFields()

        # Add features to the error layer
        provider.addFeatures(error_features)

        # Define the red line style
        symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.LineGeometry)
        symbol.setColor(QColor("red"))
        renderer = QgsSingleSymbolRenderer(symbol)
        error_layer.setRenderer(renderer)

        # Add the error layer to the Errors group
        errors_group = QgsProject.instance().layerTreeRoot().findGroup("Errors")
        if not errors_group:
            errors_group = QgsProject.instance().layerTreeRoot().addGroup("Errors")

        QgsProject.instance().addMapLayer(error_layer, False)
        errors_group.addLayer(error_layer)

        # Force layer visibility
        layer_tree_layer = QgsProject.instance().layerTreeRoot().findLayer(error_layer.id())
        if layer_tree_layer is not None:
            layer_tree_layer.setItemVisibilityChecked(True)


    def check_button_clicked(self):
        layer_name = "Nieuwe voedingen-stadsplan"
        layer = QgsProject.instance().mapLayersByName(layer_name)

        if layer:
            layer = layer[0]
            unique_errors = self.check_unique_ids(layer)
            null_errors = self.check_non_null_ids(layer)

            # Display results in the text box
            self.textbox1.clear()
            if unique_errors:
                unique_check_result = "❌ Unique ID Check: Failed"
            else:
                unique_check_result = "✔️ Unique ID Check: Passed"

            if null_errors:
                non_null_check_result = "❌ Non-NULL ID Check: Failed"
            else:
                non_null_check_result = "✔️ Non-NULL ID Check: Passed"

            self.textbox1.append(unique_check_result)
            self.textbox1.append(non_null_check_result)

            # If there are any errors, create an error layer
            if unique_errors or null_errors:
                errors = unique_errors + null_errors

                # Create a new memory layer for errors
                error_layer = QgsVectorLayer(QgsWkbTypes.displayString(layer.wkbType()), "errors", "memory")

                # Set CRS to EPSG 31370
                crs = QgsCoordinateReferenceSystem('EPSG:31370')
                error_layer.setCrs(crs)

                provider = error_layer.dataProvider()

                # Add fields to the error layer
                provider.addAttributes(layer.fields())

                # Add features to the error layer with attributes copied from the original layer
                for error_feature in errors:
                    error_feature_geom = error_feature.geometry()
                    error_feature_attrs = error_feature.attributes()
                    new_feature = QgsFeature()
                    new_feature.setGeometry(error_feature_geom)
                    new_feature.setAttributes(error_feature_attrs)
                    provider.addFeature(new_feature)

                # Update the attribute table of the error layer
                error_layer.updateFields()

                # Add the error layer to the map
                QgsProject.instance().addMapLayer(error_layer)

                # Show message indicating errors were found
                self.show_error_message("Errors detected, check Errors layer.")
                return True
            else:
                # Show message indicating no errors were found
                self.show_information_message("No errors detected in layer.")
                return False

        else:
            # Print a message if the layer does not exist
            print(f"Layer '{layer_name}' not found.")
            self.show_error_message(f"Layer '{layer_name}' not found.")
            return True


    def perform_upload(self, geojson_features):
        supabase_url = "https://vckjtooglwrxxmwcyyeo.supabase.co"
        service_role_api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZja2p0b29nbHdyeHhtd2N5eWVvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcxNTc2Nzg3MiwiZXhwIjoyMDMxMzQzODcyfQ.sa090Kgdfn357eTGO1kLIwoJj4zQ1cEuwCdjVP1CzN8"
        headers = {
            "apikey": service_role_api_key,
            "Authorization": f"Bearer {service_role_api_key}",
            "Content-Type": "application/json"
        }

        # Fetch existing feeder_ids
        response = requests.get(f"{supabase_url}/rest/v1/geojson_files?select=feeder_id", headers=headers)
        if response.status_code == 200:
            try:
                existing_feeder_ids = {item['feeder_id'] for item in response.json()}
            except ValueError as e:
                print(f"Error parsing JSON response: {e}")
                self.show_error_message("Error parsing existing feeder_ids response.")
                return False
        else:
            print(f"Error fetching existing feeder_ids: {response.status_code} - {response.text}")
            self.show_error_message("Error fetching existing feeder_ids.")
            return False

        upload_success = True
        for geojson_feature in geojson_features:
            properties = geojson_feature["properties"]
            insert_data = {prop_name: prop_value for prop_name, prop_value in properties.items()}
            insert_data["geometry"] = geojson_feature["geometry"]
            insert_data_str = json.dumps(insert_data)
            feeder_id = properties.get("feeder_id")

            if feeder_id in existing_feeder_ids:
                url = f"{supabase_url}/rest/v1/geojson_files?feeder_id=eq.{feeder_id}"
                response = requests.patch(url, data=insert_data_str, headers=headers)
                if response.status_code != 204:
                    print(
                        f"Error updating GeoJSON data for feeder_id {feeder_id}. Status code: {response.status_code}, Response: {response.text}")
                    upload_success = False
            else:
                url = f"{supabase_url}/rest/v1/geojson_files"
                response = requests.post(url, data=insert_data_str, headers=headers)
                if response.status_code != 201:
                    print(
                        f"Error uploading GeoJSON data. Status code: {response.status_code}, Response: {response.text}")
                    upload_success = False

        return upload_success

    def upload_to_server_button_clicked(self):
        layer_name = "Nieuwe voedingen-stadsplan"
        layers = QgsProject.instance().mapLayersByName(layer_name)

        if layers:
            layer = layers[0]

            # Perform both checks
            unique_errors = self.check_unique_ids(layer)
            null_errors = self.check_non_null_ids(layer)

            if unique_errors or null_errors:
                self.show_error_message("Errors detected in the layer. Upload cannot proceed.")
                return

            # Convert layer features to GeoJSON features
            geojson_features = []
            for feature in layer.getFeatures():
                properties = {}
                for field in feature.fields():
                    value = feature[field.name()]
                    if isinstance(value, QVariant):
                        value = None if value.isNull() else value.value()
                    properties[field.name()] = value

                wkt_geometry = feature.geometry().asWkt()
                shapely_geometry = shape({"type": "Point", "coordinates": (0, 0)})
                try:
                    shapely_geometry = wkt.loads(wkt_geometry)
                except Exception as e:
                    print(f"Error converting geometry to Shapely: {e}")
                geojson_geometry = mapping(shapely_geometry)

                geojson_feature = {
                    "type": "Feature",
                    "properties": properties,
                    "geometry": geojson_geometry
                }
                geojson_features.append(geojson_feature)

            # Perform the upload
            upload_success = self.perform_upload(geojson_features)

            if upload_success:
                self.show_information_message("Upload completed successfully.")
            else:
                self.show_error_message("Some errors occurred during upload.")
        else:
            print(f"Layer '{layer_name}' not found.")
            self.show_error_message(f"Layer '{layer_name}' not found.")

    def show_error_message(self, message):
        """Displays an error message to the user"""
        QMessageBox.critical(None, "Error", message)

    def show_information_message(self, message):
        """Displays an information message to the user"""
        QMessageBox.information(None, "Information", message)
