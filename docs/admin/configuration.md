# Changing Application Settings

Each component of this application may have registered settings. To configure these settings, go to the `App Configuration Settings` page in the admin interface and click on the setting you wish to configure. Settings cannot be deleted, only reset to the default value using the `Reset to Default` button.

## Map Visualization

In order to enable the map visualization beyond the DB Node admin view, the following configuration may need to be performed:
* In the App Configuration Settings section, set the `GREN Map Visualization Enabled` setting to "True" in order to serve map data for rendering.  Set to "False" if this DB Node only supplies polled data to another Node in the GREN Map distributed database hierarchy.
* In the Visualization Map Allowed Origins section of the Admin, make sure the base URL you will use to access the map is listed, or add it.

### Cache Optimization

App Configuration Setting `GREN Map Visualization Data Caching Enabled` is a speed optimization to more quickly serve map data, and may be "True" or "False".

## Configuring the Initial Built-In Map Display

The GREN Map DB Node ships with a built-in visualization renderer.  The default starting position and the zoom of this map can be defined for all visitors by the user. To configure these settings go to the GREN Map Admin page and go to `BASE APP->App Configuration Settings`.

### Initial Map Position

From the GREEN MAP administration page, access `BASE APP->App Configuration Settings->GREN Map Initial Coordinates`.

The latitude and longitude value can be changed in the `Value` field. The first number refers to latitude and the second number refers to longitude.

The default value for latitude and longitude is (0, 0).  With this default value, the browser will ask for permission to access your location, and behave in one of the following ways.
1. If the user allows location tracking, the map will be centered in the position obtained by the navigator.
2. If the user denies location tracking, the map will be centered in the center of the map [at (0, 0)].

If a custom location is entered, browser location tracking is skipped; the map will be centered on the location entered.

### Initial Map Zoom

From the GREEN MAP administration page, access `BASE APP->App Configuration Settings->GREN Map Initial Zoom`.

The zoom value can be changed in the `Value` field.

The default zoom value is 3. This zoom value shows the entire map. You can enter decimal values between 2 and 18.

- NOTE: The decimal range is 0.25, meaning you can enter numbers like 5.25, 5.50, 5.75 and so on.

## Polling

The settings beginning with "GRENML Polling" relate to data communication between GREN Map DB Nodes.

For information about Polling, see the user manuals about [polling](../user/polling.md) and [collation](../user/collation.md).

### Enabled

`GRENML Polling Enabled`, if set to "True", will trigger a polling event on the schedule defined in `GRENML Polling Interval`.  To disable polling, set this to "False".

### Interval

`GRENML Polling Interval` defines the schedule on which polling will occur, using a crontab-like syntax.

### Live or Published Data

`GRENML Polling Data Supply Type` affects how this DB Node will supply data when polled.  If set to "Live", it will serve the [main Topology](../user/polling.md#main-root-topology) and all subtopologies.  If set to "Published", it will serve the latest published data set.
