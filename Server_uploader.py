from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon, QPixmap
from qgis.PyQt.QtWidgets import QAction, QPushButton, QTextEdit, QHBoxLayout, QLabel, QVBoxLayout, QWidget
from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsGeometry, QgsProject, QgsCoordinateReferenceSystem, \
    QgsCoordinateTransformContext, QgsWkbTypes, QgsVectorFileWriter, QgsSymbol, QgsSingleSymbolRenderer
from PyQt5.QtGui import QColor
from qgis.PyQt.QtCore import QVariant
from PyQt5.QtCore import QVariant
from shapely.geometry import shape, mapping
from shapely import wkt
import os
from qgis.PyQt.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox, QApplication
import requests
import json
import tempfile
import shutil
import sys
from datetime import datetime
# from typing import Dict, List, Union
from shapely.wkt import loads as wkt_loads
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
from supabase import create_client, Client
# from dataclasses import dataclass


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
        super().__init__()
        self.layout = None
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
        self.supabase_url = "https://vckjtooglwrxxmwcyyeo.supabase.co"
        self.service_role_api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZja2p0b29nbHdyeHhtd2N5eWVvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcxNTc2Nzg3MiwiZXhwIjoyMDMxMzQzODcyfQ.sa090Kgdfn357eTGO1kLIwoJj4zQ1cEuwCdjVP1CzN8"
        self.supabase = create_client(self.supabase_url, self.service_role_api_key)

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
            upload_button.clicked.connect(self.upload_to_landing_table_button_clicked)

            self.textbox1 = self.dlg.findChild(QTextEdit, "TextBox1")
            self.textbox2 = self.dlg.findChild(QTextEdit, "TextBox2")

            self.textbox1.setReadOnly(True)
            self.textbox2.setReadOnly(True)

            settings_button = self.dlg.findChild(QPushButton, "Settings")
            settings_button.clicked.connect(self.settings_button_clicked)

            savesettings_button = self.dlg.findChild(QPushButton, "SaveSettings")
            savesettings_button.clicked.connect(self.savesettings_button_clicked)

            returnsettings_button = self.dlg.findChild(QPushButton, "ReturnSettings")
            returnsettings_button.clicked.connect(self.returnsettings_button_clicked)

            self.dlg.SettingsBox.setVisible(False)

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

    def check_unique_ids(self, layer, field_name):
        """Check that all specified field values are unique."""
        errors = []
        idx = layer.fields().indexFromName(field_name)
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

    def check_non_null_ids(self, layer, field_name):
        """Check that all specified field values are not NULL."""
        errors = []
        idx = layer.fields().indexFromName(field_name)

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
        feeder_layer_name = QSettings().value('Server_uploader/FeederLayerName', '')
        switch_layer_name = QSettings().value('Server_uploader/SwitchLayerName', '')

        if feeder_layer_name:
            feeder_layer = QgsProject.instance().mapLayersByName(feeder_layer_name)
            if feeder_layer:
                feeder_layer = feeder_layer[0]
                feeder_field_name = "feeder_id"  # Field name for the feeder layer

                feeder_unique_errors = self.check_unique_ids(feeder_layer, feeder_field_name)
                feeder_null_errors = self.check_non_null_ids(feeder_layer, feeder_field_name)

                self.dlg.TextBox1.clear()
                if feeder_unique_errors:
                    feeder_unique_check_result = "❌ Unique ID Check (Feeder): Failed"
                else:
                    feeder_unique_check_result = "✔️ Unique ID Check (Feeder): Passed"

                if feeder_null_errors:
                    feeder_non_null_check_result = "❌ Non-NULL ID Check (Feeder): Failed"
                else:
                    feeder_non_null_check_result = "✔️ Non-NULL ID Check (Feeder): Passed"

                self.dlg.TextBox1.append(feeder_unique_check_result)
                self.dlg.TextBox1.append(feeder_non_null_check_result)

                if feeder_unique_errors:
                    self.create_error_layer("No unique ID's (Feeder)", feeder_layer, feeder_unique_errors)
                if feeder_null_errors:
                    self.create_error_layer("ID's with null values (Feeder)", feeder_layer, feeder_null_errors)
            else:
                self.show_error_message(f"Feeder layer '{feeder_layer_name}' not found.")
                return True
        else:
            QMessageBox.warning(None, "Check", "No feeder layer name provided")

        if switch_layer_name:
            switch_layer = QgsProject.instance().mapLayersByName(switch_layer_name)
            if switch_layer:
                switch_layer = switch_layer[0]
                switch_field_name = "switch_id"  # Field name for the switch layer

                switch_unique_errors = self.check_unique_ids(switch_layer, switch_field_name)
                switch_null_errors = self.check_non_null_ids(switch_layer, switch_field_name)

                if switch_unique_errors:
                    switch_unique_check_result = "❌ Unique ID Check (Switch): Failed"
                else:
                    switch_unique_check_result = "✔️ Unique ID Check (Switch): Passed"

                if switch_null_errors:
                    switch_non_null_check_result = "❌ Non-NULL ID Check (Switch): Failed"
                else:
                    switch_non_null_check_result = "✔️ Non-NULL ID Check (Switch): Passed"

                self.dlg.TextBox1.append(switch_unique_check_result)
                self.dlg.TextBox1.append(switch_non_null_check_result)

                if switch_unique_errors:
                    self.create_error_layer("No unique ID's (Switch)", switch_layer, switch_unique_errors)
                if switch_null_errors:
                    self.create_error_layer("ID's with null values (Switch)", switch_layer, switch_null_errors)
            else:
                self.show_error_message(f"Switch layer '{switch_layer_name}' not found.")
                return True
        else:
            QMessageBox.warning(None, "Check", "No switch layer name provided")

        if not feeder_unique_errors and not feeder_null_errors and not switch_unique_errors and not switch_null_errors:
            self.show_information_message("No errors detected in layers.")
            return False
        else:
            self.show_error_message("Errors detected, check Errors layer group.")
            return True

    def perform_upload_to_landing_table(self, geojson_features, table_name):
        supabase_url = "https://vckjtooglwrxxmwcyyeo.supabase.co"
        service_role_api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZja2p0b29nbHdyeHhtd2N5eWVvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcxNTc2Nzg3MiwiZXhwIjoyMDMxMzQzODcyfQ.sa090Kgdfn357eTGO1kLIwoJj4zQ1cEuwCdjVP1CzN8"
        headers = {
            "apikey": service_role_api_key,
            "Authorization": f"Bearer {service_role_api_key}",
            "Content-Type": "application/json"
        }

        # Delete existing records from the landing table
        delete_url = f"{supabase_url}/rest/v1/{table_name}?id=neq.0"
        delete_response = requests.delete(delete_url, headers=headers)
        if delete_response.status_code != 204:
            print(f"Error deleting existing records: {delete_response.status_code} - {delete_response.text}")
            self.show_error_message("Error deleting existing records from landing table.")
            return False

        # Upload new geojson features
        upload_success = self.perform_upload(geojson_features, supabase_url, headers, table_name)
        return upload_success

    def perform_upload_to_final_table(self, landing_table_name, final_table_name):
        headers = {
            "apikey": self.service_role_api_key,
            "Authorization": f"Bearer {self.service_role_api_key}",
            "Content-Type": "application/json"
        }

        # Fetch data from the landing table
        landing_response = requests.get(f"{self.supabase_url}/rest/v1/{landing_table_name}", headers=headers)
        if landing_response.status_code == 200:
            landing_data = landing_response.json()
        else:
            print("Error fetching records from landing table.")
            return False

        # Fetch data from the final table
        final_response = requests.get(f"{self.supabase_url}/rest/v1/{final_table_name}", headers=headers)
        if final_response.status_code == 200:
            final_data = final_response.json()
        else:
            print("Error fetching records from final table.")
            return False

        # Determine field name based on table name
        if 'switch' in landing_table_name:
            field_name = 'switch_id'
        else:
            field_name = 'feeder_id'

        final_data_dict = {record[field_name]: record for record in final_data}
        upload_success = True

        for landing_record in landing_data:
            record_id = landing_record[field_name]
            if record_id in final_data_dict:
                final_record = final_data_dict[record_id]
                if not self.records_are_equal(landing_record, final_record):
                    # Identify changed fields
                    changed_fields = {k: v for k, v in landing_record.items() if
                                      k not in {'id'} and final_record.get(k) != v}
                    if changed_fields:
                        update_url = f"{self.supabase_url}/rest/v1/{final_table_name}?{field_name}=eq.{record_id}"
                        response = requests.patch(update_url, json=changed_fields, headers=headers)
                        if response.status_code != 204:
                            print(
                                f"Error updating record {record_id} in final table. Status code: {response.status_code}, Response: {response.text}")
                            upload_success = False
            else:
                # Insert new record
                insert_data = {k: v for k, v in landing_record.items() if k not in {'id'}}
                insert_url = f"{self.supabase_url}/rest/v1/{final_table_name}"
                response = requests.post(insert_url, json=insert_data, headers=headers)
                if response.status_code != 201:
                    print(
                        f"Error inserting new record {record_id} in final table. Status code: {response.status_code}, Response: {response.text}")
                    upload_success = False

        # Mark records as deleted in the final table if they are not in the landing table
        landing_ids = {record[field_name] for record in landing_data}
        for final_record in final_data:
            if final_record[field_name] not in landing_ids and not final_record.get('deleted', False):
                update_url = f"{self.supabase_url}/rest/v1/{final_table_name}?{field_name}=eq.{final_record[field_name]}"
                response = requests.patch(update_url, json={"deleted": True}, headers=headers)
                if response.status_code != 204:
                    print(
                        f"Error marking record {final_record[field_name]} as deleted in final table. Status code: {response.status_code}, Response: {response.text}")
                    upload_success = False

        return upload_success

    def perform_upload(self, geojson_features, supabase_url, headers, table_name):
        # Determine the field name based on the table name
        if 'switch' in table_name:
            field_name = 'switch_id'
        else:
            field_name = 'feeder_id'

        # Fetch existing IDs
        response = requests.get(f"{supabase_url}/rest/v1/{table_name}?select={field_name}", headers=headers)
        if response.status_code == 200:
            try:
                existing_ids = {item[field_name] for item in response.json()}
            except ValueError as e:
                print(f"Error parsing JSON response: {e}")
                self.show_error_message("Error parsing existing IDs response.")
                return False
        else:
            print(f"Error fetching existing IDs: {response.status_code} - {response.text}")
            self.show_error_message("Error fetching existing IDs.")
            return False

        upload_success = True
        for geojson_feature in geojson_features:
            # Check if 'properties' key exists
            if 'properties' in geojson_feature:
                properties = geojson_feature["properties"]
                insert_data = {prop_name: prop_value for prop_name, prop_value in properties.items()}
                insert_data["geometry"] = geojson_feature["geometry"]
            else:
                # If 'properties' key does not exist, use the flat structure
                insert_data = geojson_feature

            insert_data_str = json.dumps(insert_data)
            feature_id = insert_data.get(field_name)

            if feature_id in existing_ids:
                url = f"{supabase_url}/rest/v1/{table_name}?{field_name}=eq.{feature_id}"
                response = requests.patch(url, data=insert_data_str, headers=headers)
                if response.status_code != 204:
                    print(
                        f"Error updating GeoJSON data for {field_name} {feature_id}. Status code: {response.status_code}, Response: {response.text}")
                    upload_success = False
            else:
                url = f"{supabase_url}/rest/v1/{table_name}"
                response = requests.post(url, data=insert_data_str, headers=headers)
                if response.status_code != 201:
                    print(
                        f"Error uploading GeoJSON data. Status code: {response.status_code}, Response: {response.text}")
                    upload_success = False

        return upload_success

    def upload_to_landing_table_button_clicked(self):
        self.textbox2.setText("Upload in progress")
        feeder_layer_name = QSettings().value('Server_uploader/FeederLayerName', '')
        switch_layer_name = QSettings().value('Server_uploader/SwitchLayerName', '')
        QApplication.processEvents()

        upload_results = []
        all_changes_summary = []
        changes_summary = []  # Initialize changes_summary

        if feeder_layer_name:
            feeder_layer = QgsProject.instance().mapLayersByName(feeder_layer_name)
            if feeder_layer:
                layer = feeder_layer[0]
                field_name = "feeder_id"
                landing_table_name = "landing_geojson_files"
                final_table_name = "geojson_files"

                unique_errors = self.check_unique_ids(layer, field_name)
                null_errors = self.check_non_null_ids(layer, field_name)

                if unique_errors or null_errors:
                    self.show_error_message("Errors detected in the feeder layer. Upload cannot proceed.")
                    return

                geojson_features = self.convert_layer_features_to_geojson(layer)

                upload_success = self.perform_upload_to_landing_table(geojson_features, landing_table_name)
                upload_results.append((landing_table_name, final_table_name, upload_success))

                if upload_success:
                    added, deleted, changed, details_message = self.compare_landing_and_final_tables(landing_table_name,
                                                                                                     final_table_name)
                    all_changes_summary.append(details_message)
                    changes_summary.append(('Feeder Layer', (added, deleted, changed)))

        if switch_layer_name:
            switch_layer = QgsProject.instance().mapLayersByName(switch_layer_name)
            if switch_layer:
                layer = switch_layer[0]
                field_name = "switch_id"
                landing_table_name = "switches_landing_table"
                final_table_name = "switches_final_table"

                unique_errors = self.check_unique_ids(layer, field_name)
                null_errors = self.check_non_null_ids(layer, field_name)

                if unique_errors or null_errors:
                    self.show_error_message("Errors detected in the switch layer. Upload cannot proceed.")
                    return

                geojson_features = self.convert_layer_features_to_geojson(layer)

                upload_success = self.perform_upload_to_landing_table(geojson_features, landing_table_name)
                upload_results.append((landing_table_name, final_table_name, upload_success))

                if upload_success:
                    added, deleted, changed, details_message = self.compare_landing_and_final_tables(landing_table_name,
                                                                                                     final_table_name)
                    all_changes_summary.append(details_message)
                    changes_summary.append(('Switch Layer', (added, deleted, changed)))

        overall_success = all(result[2] for result in upload_results)

        if overall_success:
            high_level_overview = "\n"
            for layer_name, summary in changes_summary:
                added, deleted, changed = summary
                high_level_overview += f"{layer_name}: Added: {added}, Deleted: {deleted}, Changed: {changed}\n"

            self.textbox2.setText(high_level_overview)

            self.display_changes(all_changes_summary)

            self.create_accept_cancel_buttons()
        else:
            self.show_error_message("Some errors occurred during upload.")

    def upload_shapefiles_to_storage(self, layer_name, shapefile_paths):
        bucket_name = "shapefiles"
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        for file_path in shapefile_paths:
            file_name = os.path.basename(file_path)
            file_key = f"{layer_name}_{timestamp}/{file_name}_{timestamp}"

            with open(file_path, "rb") as file:
                response = self.supabase.storage.from_(bucket_name).upload(file_key, file)

            if response.status_code != 200:
                print(f"Error uploading {file_name}: {response.text}")
                return False

        return True

    def convert_layer_features_to_geojson(self, layer):
        geojson_features = []
        feeder_layer_name = QSettings().value('Server_uploader/FeederLayerName', '')
        switch_layer_name = QSettings().value('Server_uploader/SwitchLayerName', '')

        for feature in layer.getFeatures():
            properties = {}
            for field in feature.fields():
                value = feature[field.name()]
                if isinstance(value, QVariant):
                    value = None if value.isNull() else value.value()
                properties[field.name()] = value

            wkt_geometry = feature.geometry().asWkt()
            try:
                if feeder_layer_name:
                    shapely_geometry = wkt_loads(wkt_geometry)
                elif switch_layer_name:
                    shapely_geometry = wkt_loads(wkt_geometry.replace('POINT Z', 'POINT'))
                else:
                    print(f"No layer for geometry processing.")
                    continue
            except Exception as e:
                print(f"Error converting geometry to Shapely: {e}")
                continue

            geojson_geometry = mapping(shapely_geometry)

            geojson_feature = {
                "type": "Feature",
                "properties": properties,
                "geometry": geojson_geometry
            }
            geojson_features.append(geojson_feature)

        return geojson_features

    def compare_landing_and_final_tables(self, landing_table_name, final_table_name):
        supabase_url = "https://vckjtooglwrxxmwcyyeo.supabase.co"
        service_role_api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZja2p0b29nbHdyeHhtd2N5eWVvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcxNTc2Nzg3MiwiZXhwIjoyMDMxMzQzODcyfQ.sa090Kgdfn357eTGO1kLIwoJj4zQ1cEuwCdjVP1CzN8"
        headers = {
            "apikey": service_role_api_key,
            "Authorization": f"Bearer {service_role_api_key}",
            "Content-Type": "application/json"
        }

        landing_response = requests.get(f"{supabase_url}/rest/v1/{landing_table_name}", headers=headers)
        if landing_response.status_code == 200:
            landing_records = landing_response.json()
        else:
            print("Error fetching records from landing table.")
            return

        final_response = requests.get(f"{supabase_url}/rest/v1/{final_table_name}", headers=headers)
        if final_response.status_code == 200:
            final_records = final_response.json()
        else:
            print("Error fetching records from final table.")
            return

        # Determine field name based on table name
        if 'switch' in landing_table_name:
            field_name = 'switch_id'
        else:
            field_name = 'feeder_id'

        # Filter out records marked as deleted
        final_records = [record for record in final_records if not record.get('deleted', False)]

        landing_ids = {record[field_name] for record in landing_records}
        final_ids = {record[field_name] for record in final_records}

        added_ids = landing_ids - final_ids
        deleted_ids = final_ids - landing_ids

        changed_records = []
        for landing_record in landing_records:
            record_id = landing_record[field_name]
            if record_id in final_ids:
                final_record = next(record for record in final_records if record[field_name] == record_id)
                if not self.records_are_equal(landing_record, final_record):
                    changed_records.append((landing_record, final_record))

        details_message = self.collect_changes(added_ids, deleted_ids, changed_records, landing_records, final_records,
                                               field_name)
        return len(added_ids), len(deleted_ids), len(changed_records), details_message

    def collect_changes(self, added_ids, deleted_ids, changed_records, landing_records, final_records, field_name):
        details_message = f"<h2>Changes for table: {field_name}</h2>"

        added_records = [record for record in landing_records if record[field_name] in added_ids]
        deleted_records = [record for record in final_records if record[field_name] in deleted_ids]

        details_message += "<h3>Added Records:</h3>"
        for record in added_records:
            details_message += f"<pre>{self.format_record(record)}</pre>"

        details_message += "<h3>Deleted Records:</h3>"
        for record in deleted_records:
            details_message += f"<pre>{self.format_record(record)}</pre>"

        details_message += "<h3>Changed Records:</h3>"
        for before, after in changed_records:
            details_message += f"<h4>Before:</h4><pre>{self.format_record(before)}</pre>"
            details_message += f"<h4>After:</h4><pre>{self.format_record(after)}</pre>"

        return details_message

    def display_changes(self, all_changes_summary):
        overall_message = ""
        for summary in all_changes_summary:
            overall_message += summary

        # Combine and store details message
        self.details_message = overall_message

    def create_accept_cancel_buttons(self):
        self.remove_accept_cancel_buttons()

        self.layout = QVBoxLayout()

        self.show_changes_button = QPushButton("Show Changes")
        self.show_changes_button.clicked.connect(self.show_details_in_qgis)
        self.layout.addWidget(self.show_changes_button)

        self.accept_button = QPushButton("Accept Changes")
        self.accept_button.clicked.connect(self.accept_changes)
        self.layout.addWidget(self.accept_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_changes)
        self.layout.addWidget(self.cancel_button)

        self.textbox2.setLayout(self.layout)

    def show_details_in_qgis(self):
        details_dialog = QDialog()
        details_dialog.setWindowTitle("Change Details")

        layout = QVBoxLayout()
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(self.details_message)  # Use HTML for better formatting
        layout.addWidget(text_edit)

        # Increase the size of the dialog box
        details_dialog.resize(800, 600)  # Adjust size as per your requirement

        close_button = QPushButton("Close")
        close_button.clicked.connect(details_dialog.accept)
        layout.addWidget(close_button)

        details_dialog.setLayout(layout)
        details_dialog.exec_()

    def format_record(self, record):
        formatted = "<br>".join(f"{key}: {value}" for key, value in record.items())
        return formatted

    def remove_accept_cancel_buttons(self):
        print("Removing existing buttons...")
        if hasattr(self, 'layout') and self.layout is not None:
            while self.layout.count():
                child = self.layout.takeAt(0)
                if child.widget():
                    child.widget().setParent(None)
            self.layout.deleteLater()
            self.layout = None
        print("Existing buttons removed.")

    def accept_changes(self):
        feeder_layer_name = QSettings().value('Server_uploader/FeederLayerName', '')
        switch_layer_name = QSettings().value('Server_uploader/SwitchLayerName', '')
        if feeder_layer_name:
            landing_table_name = "landing_geojson_files"
            final_table_name = "geojson_files"
            layers = QgsProject.instance().mapLayersByName(feeder_layer_name)
            if layers:
                layer = layers[0]
                shapefile_paths = [layer.source().replace(".shp", ext) for ext in [".shp", ".shx", ".dbf", ".prj"]]
                 # Upload shapefiles to Supabase Storage
                shapefile_upload_success = self.upload_shapefiles_to_storage(feeder_layer_name, shapefile_paths)
                if not shapefile_upload_success:
                     print("Error uploading shapefiles to storage.")
                     return False
            upload_success = self.perform_upload_to_final_table(landing_table_name, final_table_name)
            if upload_success:
                self.show_information_message("Upload to feeder final table completed successfully.")
            else:
                self.show_error_message("Some errors occurred during upload to switches final table.")
        if switch_layer_name:
            landing_table_name = "switches_landing_table"
            final_table_name = "switches_final_table"
            layers = QgsProject.instance().mapLayersByName(switch_layer_name)
            if layers:
                layer = layers[0]
                shapefile_paths = [layer.source().replace(".shp", ext) for ext in [".shp", ".shx", ".dbf", ".prj"]]
                # Upload shapefiles to Supabase Storage
                shapefile_upload_success = self.upload_shapefiles_to_storage(switch_layer_name, shapefile_paths)
                if not shapefile_upload_success:
                    print("Error uploading shapefiles to storage.")
                    return False
            upload_success = self.perform_upload_to_final_table(landing_table_name, final_table_name)
            if upload_success:
                self.show_information_message("Upload to switch final table completed successfully.")
            else:
                self.show_error_message("Some errors occurred during upload to switches final table.")

        self.remove_accept_cancel_buttons()
        self.textbox2.clear()

    def cancel_changes(self):
        print("Cancel changes clicked.")
        self.textbox2.setText("Changes have been canceled.")
        self.remove_accept_cancel_buttons()

    def records_are_equal(self, record1, record2):
        excluded_fields = {'feeder_id', 'switch_id', 'id', 'created_at', 'deleted'}
        record1_normalized = {k: v for k, v in record1.items() if k not in excluded_fields}
        record2_normalized = {k: v for k, v in record2.items() if k not in excluded_fields}
        return record1_normalized == record2_normalized

    def settings_button_clicked(self):
        """Functionality for Settings button."""
        # Load the saved layer names
        feeder_layer_name = QSettings().value('Server_uploader/FeederLayerName', '')
        switch_layer_name = QSettings().value('Server_uploader/SwitchLayerName', '')

        # Populate the combo boxes with current layer names in the project
        self.dlg.FeederLayerInput.clear()
        self.dlg.SwitchLayerInput.clear()
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            self.dlg.FeederLayerInput.addItem(layer.name())
            self.dlg.SwitchLayerInput.addItem(layer.name())

        # Set the current layer names in the combo boxes
        if feeder_layer_name:
            index = self.dlg.FeederLayerInput.findText(feeder_layer_name)
            if index != -1:
                self.dlg.FeederLayerInput.setCurrentIndex(index)

        if switch_layer_name:
            index = self.dlg.SwitchLayerInput.findText(switch_layer_name)
            if index != -1:
                self.dlg.SwitchLayerInput.setCurrentIndex(index)

        self.dlg.TextBox1.setVisible(False)
        self.dlg.TextBox2.setVisible(False)
        self.dlg.SettingsBox.setVisible(True)

    def savesettings_button_clicked(self):
        feeder_layer_name = self.dlg.FeederLayerInput.currentText()
        switch_layer_name = self.dlg.SwitchLayerInput.currentText()
        if feeder_layer_name and switch_layer_name:
            # Save the layer names to QSettings for persistence
            QSettings().setValue('Server_uploader/FeederLayerName', feeder_layer_name)
            QSettings().setValue('Server_uploader/SwitchLayerName', switch_layer_name)
            QMessageBox.information(None, "Save Settings",
                                    f"Feeder layer '{feeder_layer_name}' and switch layer '{switch_layer_name}' saved")
        else:
            QMessageBox.warning(None, "Save Settings", "Layer names cannot be empty")

    def returnsettings_button_clicked(self):
        """Functionality for Return button."""
        # Show the other text boxes and hide the settings box
        self.dlg.TextBox1.setVisible(True)
        self.dlg.TextBox2.setVisible(True)
        self.dlg.SettingsBox.setVisible(False)

    def show_error_message(self, message):
        """Displays an error message to the user"""
        QMessageBox.critical(None, "Error", message)

    def show_information_message(self, message):
        """Displays an information message to the user"""
        QMessageBox.information(None, "Information", message)
