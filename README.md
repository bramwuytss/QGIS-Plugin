# QGIS-Plugin
The goal of this Plugin is to upload shapefiles to a server. The shapefiles on the server are linked to the "schakelboekje" application.  
Before an upload to the server can be performed, certain checks should and will be performed. There are 3 checks: 1 to check whether the ID is unique (for both layers), 1 to check whether the ID is not null (for both layers) and 1 to check whether there is a switch between every feeder section. When the check buttons is pressed, all 3 checks will be performed at once.  
When the checks are not passed, error layers will be created, which will contain the errors that should be fixed before proceeding.  
When the checks are passed, an upload will be performed, first to the landing table. This will result in an overview of the changes that have been made. Afterwards, users will have the choice to cancel or to accept the changes. When the user accepts the changes, an upload to the final table will happen, which is also finally linked to the "schakelboekje" application.  
When making an upload to the final table, a copy of the shapefiles will also be uploaded to a bucket on the server. The goal is that the plugin also contains a button "Get shapfiles", which will download the shapefiles from the server, so the user can always work with the most recent version of the shapefiles. However, this functionality does not yet work.  
## How to use locally
### Plugin-code
Download the server_uploader.zip folder.  
Store it at the following path (as a zip-file): C:\Users\UserName\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins (The first part should be the download path of the QGIS installation).  
Open QGIS and click "Plugins" > "Manage and install Plugins" > "Install from ZIP" and navigate to the zip folder we just downloaded. Finally click "Install Plugin".  
The Plugin will now be installed to QGIS. An extracted folder will be created at the path we just navigated to (C:\Users\UserName\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins).  
We can now use the plugin, using the sample data provided below.  
When we want to change the functionality of the Plugin, we can navigate to the extracted folder and edit the "Server_uploader.py" or "Server_uploader_dialog.py" file.  
To view the changes made to the plugin, we need to reload the plugin. To do this, another plugin called "Plugin reloader" can be used.  

### Sample data
Download the sample data QGIS zip folder.  
Extract the ZIP-file.  
Open the QGIS file 'Sample Data' that is located in the extracted folder.  
QGIS will open and 2 layers will be loaded into QGIS.  
These 2 layers can be used to do the checks and make the upload to the server.  

