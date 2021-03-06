# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ThermalAnomalyDialog
                                 A QGIS plugin
 This plugin shows thermal anomalies
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2020-04-15
        git sha              : $Format:%H$
        copyright            : (C) 2020 by GIS
        email                : gis@gis.by
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

import os
from enum import Enum

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import Qt, QDateTime, QTime
from qgis._gui import QgsMapToolPan

from .drawtools import DrawPolygon
from qgis.core import QgsFeature, QgsFeatureRequest, QgsProject, QgsGeometry, \
    QgsCoordinateTransform, QgsCoordinateTransformContext, \
    QgsVectorLayer, QgsLayerTreeGroup, QgsRenderContext, \
    QgsCoordinateReferenceSystem, QgsSimpleMarkerSymbolLayerBase, QgsSymbol, QgsSvgMarkerSymbolLayer, QgsPointXY, \
    QgsRasterMarkerSymbolLayer, QgsRuleBasedRenderer
from PyQt5.QtWidgets import QMessageBox, QApplication
from qgis.PyQt.QtGui import QIcon, QColor
from .data_request import DataRequest

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'thermal_anomaly_dialog_base.ui'))


class StatusMessageType(Enum):
    EMPTY = 0
    LOAD_STARTED = 4
    LOAD_FINISHED = 5
    POLYGON_ON = 6


class SatellitesTypes(Enum):
    TERRA = 1
    AQUA = 2
    METOP = 3
    NOAA = 4
    METOP_A = 5
    METOP_B = 6
    METOP_C = 7
    SUOMI = 9
    NOAA20 = 10


class TAStatuses(Enum):
    VERIFICATION_NEED = 1
    VERIFIED = 2
    NOT_VERIFIED = 3
    VERIFICATION_IN_PROCESS = 4


class ThermalAnomalyDialog(QtWidgets.QDialog, FORM_CLASS):
    groupName = "ThermalAnomaly"
    resultsLayerName = "results"
    searchAreaLayerName = "search_area"

    status_message = [
        "",
        "??????????????????????...",
        "?????????????????????? ??????????????????",
        "???????????? ??????????????????????",
        "???????????????? ????????????...",
        "?????????????? ???????????? ??????????????????",
        "???????????? ???????????? ???????????????? ???????? ?????????????????? ????????"
    ]

    combo_box_items = [
        ["??????", -1],
        ["????????????????", 1000],
        ["??????????????????", 58],
        ["??????????????????", 1],
        ["????????????????????", 74],
        ["??????????????????????", 20],
        ["??????????????", 13],
        ["??????????????????????", 31]
    ]

    def __init__(self, iface, parent=None):
        """Constructor."""
        super(ThermalAnomalyDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.iface = iface
        # self.sb = self.iface.statusBarIface()
        self.tool = None
        # default color
        self.color = QColor(60, 151, 255, 125)

        self.polygonButton.setIcon(QIcon(":/plugins/thermal_anomaly/polygon_icon.png"))
        self.polygonButton.clicked.connect(self.polygon_button_toggle)

        self.getDataButton.clicked.connect(self.getdata_button_clicked)

        self.lastStatusMessage = StatusMessageType.EMPTY

        self.cbStatusAll.clicked.connect(self.__check_status_all)
        self.cbStatusVerificationNeed.clicked.connect(self.__checked_status_changed)
        self.cbStatusVerified.clicked.connect(self.__checked_status_changed)
        self.cbStatusNotVerified.clicked.connect(self.__checked_status_changed)
        self.cbStatusVerificating.clicked.connect(self.__checked_status_changed)

        self.cbSatAll.clicked.connect(self.__checked_satellite_all)
        self.cbSatNoaa.clicked.connect(self.__checked_satellite_changed)
        self.cbSatMetop.clicked.connect(self.__checked_satellite_changed)
        self.cbSatTerra.clicked.connect(self.__checked_satellite_changed)
        self.cbSatAqua.clicked.connect(self.__checked_satellite_changed)
        self.cbSatSuomi.clicked.connect(self.__checked_satellite_changed)
        self.cbSatNoaa20.clicked.connect(self.__checked_satellite_changed)
        self.cbSatMetopC.clicked.connect(self.__checked_satellite_changed)
        self.cbSatMetopB.clicked.connect(self.__checked_satellite_changed)
        self.cbSatMetopA.clicked.connect(self.__checked_satellite_changed)

        self.cbBelarus.clear()
        for item in self.combo_box_items:
            self.cbBelarus.addItem(item[0], item[1])
        self.cbBelarus.setCurrentIndex(1)

        self.dataRequest = DataRequest()
        self.dataRequest.requestFinished.connect(self.show_request_result)
        self.init_dialog()

    def init_dialog(self):
        date_time = QDateTime.currentDateTime()
        date = date_time.date()
        min_date_time = QDateTime(date, QTime(0, 0)).addYears(-1)
        max_date_time = QDateTime(date, QTime(23, 59))

        self.dateTimeEditFrom.setDateTime(QDateTime(date, QTime(0, 0)))
        self.dateTimeEditFrom.setDateTimeRange(min_date_time, max_date_time)
        self.dateTimeEditTo.setDateTime(max_date_time)
        self.dateTimeEditTo.setDateTimeRange(min_date_time, max_date_time)

        self.__toggle(False, True)

        self.__check_status_all(True)
        self.__checked_satellite_all(True)
        if self.dataRequest is not None:
            self.__show_status_label(StatusMessageType.EMPTY)
        else:
            self.__show_status_label(self.lastStatusMessage)

    def __check_status_all(self, checked):
        if checked:
            new_state = Qt.Checked
        else:
            new_state = Qt.Unchecked
        self.cbStatusAll.setCheckState(new_state)
        self.cbStatusVerificationNeed.setCheckState(new_state)
        self.cbStatusVerified.setCheckState(new_state)
        self.cbStatusNotVerified.setCheckState(new_state)
        self.cbStatusVerificating.setCheckState(new_state)

    def __checked_status_changed(self, checked):
        if not checked:
            self.cbStatusAll.setCheckState(Qt.Unchecked)

    def __checked_satellite_changed(self, checked):
        if not checked:
            self.cbSatAll.setCheckState(Qt.Unchecked)

    def __checked_satellite_all(self, checked):
        if checked:
            new_state = Qt.Checked
        else:
            new_state = Qt.Unchecked
        self.cbSatAll.setCheckState(new_state)
        self.cbSatNoaa.setCheckState(new_state)
        self.cbSatMetop.setCheckState(new_state)
        self.cbSatTerra.setCheckState(new_state)
        self.cbSatAqua.setCheckState(new_state)
        self.cbSatSuomi.setCheckState(new_state)
        self.cbSatNoaa20.setCheckState(new_state)
        self.cbSatMetopC.setCheckState(new_state)
        self.cbSatMetopB.setCheckState(new_state)
        self.cbSatMetopA.setCheckState(new_state)

    def polygon_button_toggle(self):
        checked = self.polygonButton.isChecked()
        self.__toggle(checked)
        if not checked:
            return

        # print("toggle")
        self.tool = DrawPolygon(self.iface, self.color)

        self.tool.selectionDone.connect(self.draw)
        self.iface.mapCanvas().setMapTool(self.tool)

    def __toggle(self, polygon_on, manage_button=False):
        if polygon_on:
            self.__show_status_label(StatusMessageType.POLYGON_ON)
            if isinstance(self.tool, DrawPolygon):
                self.tool.reset()
        else:
            self.__show_status_label(StatusMessageType.EMPTY)
            self.tool = QgsMapToolPan(self.iface.mapCanvas())
            self.iface.mapCanvas().setMapTool(self.tool)
        if manage_button:
            self.polygonButton.setChecked(polygon_on)

    def draw(self):
        # print("draw")
        rb = self.tool.rb
        g = rb.asGeometry()

        layer = QgsVectorLayer(
            "Polygon?crs=" + self.iface.mapCanvas().mapSettings().destinationCrs().authid() + "&field=" + self.tr(
                'Drawings') + ":string(255)", self.searchAreaLayerName, "memory")
        layer.startEditing()
        symbols = layer.renderer().symbols(QgsRenderContext())
        symbols[0].setColor(self.color)
        feature = QgsFeature()
        feature.setGeometry(g)
        feature.setAttributes([self.searchAreaLayerName])
        layer.dataProvider().addFeatures([feature])
        layer.commitChanges()

        pjt = QgsProject.instance()
        layers_list = pjt.mapLayersByName(self.searchAreaLayerName)
        if layers_list is not None and len(layers_list) > 0:
            pjt.removeMapLayer(layers_list[0])

        pjt.addMapLayer(layer, False)
        if pjt.layerTreeRoot().findGroup(self.tr(self.groupName)) is None:
            pjt.layerTreeRoot().insertChildNode(0, QgsLayerTreeGroup(self.tr(self.groupName)))
        group = pjt.layerTreeRoot().findGroup(self.tr(self.groupName))
        group.insertLayer(0, layer)
        self.iface.layerTreeView().refreshLayerSymbology(layer.id())
        self.iface.mapCanvas().refresh()

        self.tool.reset()

    def geom_transform(self, geom, crs_orig, crs_dest):
        g = QgsGeometry(geom)
        crs_transform = QgsCoordinateTransform(
            crs_orig, crs_dest, QgsCoordinateTransformContext())  # which context ?
        g.transform(crs_transform)
        return g

    def _show_message(self, title, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)

        msg.setWindowTitle(title)
        msg.setText(message)

        msg.addButton('????', QMessageBox.AcceptRole)
        msg.exec()

    def __get_checked_statuses(self):
        res = []

        if self.cbStatusVerificationNeed.isChecked():
            res.append(TAStatuses.VERIFICATION_NEED.value)
        if self.cbStatusVerified.isChecked():
            res.append(TAStatuses.VERIFIED.value)
        if self.cbStatusNotVerified.isChecked():
            res.append(TAStatuses.NOT_VERIFIED.value)
        if self.cbStatusVerificating.isChecked():
            res.append(TAStatuses.VERIFICATION_IN_PROCESS.value)

        return res

    def __get_checked_satellites(self):
        res = []

        if self.cbSatNoaa.isChecked():
            res.append(SatellitesTypes.NOAA.value)
        if self.cbSatMetop.isChecked():
            res.append(SatellitesTypes.METOP.value)
        if self.cbSatTerra.isChecked():
            res.append(SatellitesTypes.TERRA.value)
        if self.cbSatAqua.isChecked():
            res.append(SatellitesTypes.AQUA.value)
        if self.cbSatSuomi.isChecked():
            res.append(SatellitesTypes.SUOMI.value)
        if self.cbSatNoaa20.isChecked():
            res.append(SatellitesTypes.NOAA20.value)
        if self.cbSatMetopC.isChecked():
            res.append(SatellitesTypes.METOP_C.value)
        if self.cbSatMetopB.isChecked():
            res.append(SatellitesTypes.METOP_B.value)
        if self.cbSatMetopA.isChecked():
            res.append(SatellitesTypes.METOP_A.value)

        return res

    def getdata_button_clicked(self):
        date_time_from = self.dateTimeEditFrom.dateTime()
        date_time_to = self.dateTimeEditTo.dateTime()
        if date_time_from >= date_time_to:
            self._show_message("???????????????????????? ????????????", "???????? '????' ???????????? ???????? ????????????, ?????? ???????? '??'")
            return

        statuses = self.__get_checked_statuses()
        if len(statuses) == 0:
            self._show_message("???????????????????????? ????????????", "???????????????????? ?????????????? ???????? ???? ???????? ????????????")
            return
        sats = self.__get_checked_satellites()

        if len(sats) == 0:
            self._show_message("???????????????????????? ????????????", "???????????????????? ?????????????? ???????? ???? ???????? ??????????????")
            return

        belarus = self.cbBelarus.currentData()

        pjt = QgsProject.instance()
        # clear results
        layers_list = pjt.mapLayersByName(self.resultsLayerName)
        if layers_list is not None and len(layers_list) > 0:
            pjt.removeMapLayer(layers_list[0])
            self.iface.mapCanvas().refresh()

        layers_list = pjt.mapLayersByName(self.searchAreaLayerName)

        polygon_geometry = None
        if layers_list is not None and len(layers_list) > 0:
            feat = list(layers_list[0].getFeatures())[0]
            if feat.hasGeometry():
                polygon_geometry = self.geom_transform(
                    feat.geometry(),
                    self.iface.mapCanvas().mapSettings().destinationCrs(),
                    QgsCoordinateReferenceSystem(4326))

        polygon = None
        if polygon_geometry is not None:
            available_area_name = "available_area"
            shp_layer = QgsVectorLayer(os.path.dirname(__file__) + "/roi/ZRV.shp", available_area_name, "ogr")
            if not shp_layer.isValid():
                self._show_message("???????????????????????? ????????????", "???????????????????????? ???????? ?? ?????????? ????????????")
                return
            intersection_geom = None
            for feature in shp_layer.getFeatures():
                if feature.geometry().intersects(polygon_geometry):
                    intersection_geom = feature.geometry().intersection(polygon_geometry)

            if intersection_geom is None:
                layers_list = pjt.mapLayersByName(available_area_name)
                if layers_list is not None and len(layers_list) > 0:
                    pjt.removeMapLayer(layers_list[0])

                symbols = shp_layer.renderer().symbols(QgsRenderContext())
                symbols[0].setColor(QColor(76, 205, 53, 84))
                pjt.addMapLayer(shp_layer, False)
                if pjt.layerTreeRoot().findGroup(self.tr(self.groupName)) is None:
                    pjt.layerTreeRoot().insertChildNode(0, QgsLayerTreeGroup(self.tr(self.groupName)))
                group = pjt.layerTreeRoot().findGroup(self.tr(self.groupName))
                group.addLayer(shp_layer)
                self.iface.layerTreeView().refreshLayerSymbology(shp_layer.id())
                geom = self.geom_transform(
                    list(shp_layer.getFeatures())[0].geometry(),
                    QgsCoordinateReferenceSystem(4326),
                    self.iface.mapCanvas().mapSettings().destinationCrs())
                self.iface.mapCanvas().setExtent(geom.boundingBox())
                self.iface.mapCanvas().refresh()

                self._show_message("???????????????????????? ????????????", "?????????????? ???????????? ?????????? ???? ?????????????????? ???????? ????????????")
                return

            polygon = intersection_geom.asWkt()
            open_brkt = polygon.find("((") + 2
            close_brkt = polygon.find("))") - len(polygon)
            polygon = polygon[open_brkt:close_brkt]

        self.__toggle(False, True)
        self.getDataButton.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.__show_status_label(StatusMessageType.LOAD_STARTED)

        self.dataRequest.dataRequest(statuses, sats, belarus, date_time_from, date_time_to, polygon)

    def show_request_result(self, items, message):
        # print("showRequestResult")
        # print(items)

        if items is None or len(items) == 0:
            QApplication.restoreOverrideCursor()
            self.__show_status_label(StatusMessageType.LOAD_FINISHED)
            self.getDataButton.setEnabled(True)

            if message is None or len(message) == 0:
                message = "???? ?????????????????? ???????????????????? ???????????? ???? ??????????????"
            self._show_message("?????????????? ??????????????????", message)
            return

        pjt = QgsProject.instance()
        layers_list = pjt.mapLayersByName(self.resultsLayerName)

        if layers_list is not None and len(layers_list) > 0:
            pjt.removeMapLayer(layers_list[0])
            # print("remove results")
        layers_list.clear()
        if layers_list is None or len(layers_list) == 0:
            # print("create layer")
            layer = QgsVectorLayer("Point?crs=EPSG:4326"
                                   "&field=area:string(11)&field=comment:string(255)"
                                   "&field=satellite:string(25)&field=shooting:string(255)"
                                   "&field=state:integer(5)&field=temperature:double(7)"
                                   "&field=lat:double(11)&field=lon:double(11)",
                                   self.resultsLayerName, "memory")
            layer.setRenderer(self.__create_rule_based_renderer(layer.geometryType()))
        else:
            layer = layers_list[0]

        layer.startEditing()
        print("all items=", len(items))

        for point in items:
            feature = QgsFeature()
            coord = QgsGeometry.fromPointXY(QgsPointXY(float(point["lon"]), float(point["lat"])))
            feature.setGeometry(coord)
            feature.setAttributes([point["area"], point["comment"], point["satellite"],
                                   point["shooting"], point["state"], point["temperature"],
                                   float(point["lat"]), float(point["lon"])])
            layer.dataProvider().addFeatures([feature])

        layer.commitChanges()

        pjt.addMapLayer(layer, False)
        if pjt.layerTreeRoot().findGroup(self.tr(self.groupName)) is None:
            pjt.layerTreeRoot().insertChildNode(0, QgsLayerTreeGroup(self.tr(self.groupName)))
        group = pjt.layerTreeRoot().findGroup(self.tr(self.groupName))
        group.insertLayer(0, layer)
        self.iface.layerTreeView().refreshLayerSymbology(layer.id())
        self.iface.mapCanvas().refresh()

        QApplication.restoreOverrideCursor()
        self.__show_status_label(StatusMessageType.LOAD_FINISHED)
        self.getDataButton.setEnabled(True)

    def __create_rule_based_renderer(self, geometry_type):
        rules_list = [
            [":/plugins/thermal_anomaly/ta_1.png", "state 1", "state = 1"],
            [":/plugins/thermal_anomaly/ta_2.png", "state 2", "state = 2"],
            [":/plugins/thermal_anomaly/ta_21.png", "state 21", "state = 21"],
            [":/plugins/thermal_anomaly/ta_22.png", "state 22", "state = 22"],
            [":/plugins/thermal_anomaly/ta_23.png", "state 23", "state = 23"],
            [":/plugins/thermal_anomaly/ta_24.png", "state 24", "state = 24"],
            [":/plugins/thermal_anomaly/ta_3.png", "state 3", "state = 3"],
            [":/plugins/thermal_anomaly/ta_31.png", "state 31", "state = 31"],
            [":/plugins/thermal_anomaly/ta_32.png", "state 32", "state = 32"],
            [":/plugins/thermal_anomaly/ta_33.png", "state 33", "state = 33"],
            [":/plugins/thermal_anomaly/ta_4.png", "state 4", "state = 4"],
        ]

        symbol = QgsSymbol.defaultSymbol(geometry_type)
        svg_marker = QgsRasterMarkerSymbolLayer(":/plugins/thermal_anomaly/ta_1.png")
        svg_marker.setSize(6.0)
        symbol.changeSymbolLayer(0, svg_marker)

        rule_based_renderer = QgsRuleBasedRenderer(symbol)
        root_rule = rule_based_renderer.rootRule()

        for i in range(0, len(rules_list)):
            raster_marker = QgsRasterMarkerSymbolLayer(rules_list[i][0])
            raster_marker.setSize(6.0)
            # create a clone (i.e. a copy) of the default rule
            rule = root_rule.children()[0].clone()
            # set the label, expression and color
            rule.setLabel(rules_list[i][1])
            rule.setFilterExpression(rules_list[i][2])
            rule.symbol().changeSymbolLayer(0, raster_marker)
            # append the rule to the list of rules
            root_rule.appendChild(rule)

        root_rule.removeChildAt(0)

        return rule_based_renderer

    def __show_status_label(self, status_type, msg=None):
        self.lastStatusMessage = status_type
        if msg is None:
            self.statusLabel.setText(self.status_message[self.lastStatusMessage.value])
        else:
            self.statusLabel.setText(self.status_message[self.lastStatusMessage.value] + " " + msg)
