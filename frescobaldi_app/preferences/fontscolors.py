# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008, 2009, 2010 by Wilbert Berendsen
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# See http://www.gnu.org/licenses/ for more information.

from __future__ import unicode_literals

"""
Fonts and Colors preferences page.
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *


from .. import (
    app,
    icons,
    preferences,
    textformats,
)

from ..widgets import ClearButton
from ..widgets.schemeselector import SchemeSelector
from ..widgets.colorbutton import ColorButton


class FontsColors(preferences.Page):
    def __init__(self, dialog):
        super(FontsColors, self).__init__(dialog)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        self.scheme = SchemeSelector(self)
        layout.addWidget(self.scheme)
        
        hbox = QHBoxLayout()
        self.tree = QTreeWidget(self)
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.stack = QStackedWidget(self)
        hbox.addWidget(self.tree)
        hbox.addWidget(self.stack)
        layout.addLayout(hbox)
        
        self.fontButton = QPushButton(_("Change Font..."))
        layout.addWidget(self.fontButton)
        
        # add the items to our list
        self.baseColorsItem = i = QTreeWidgetItem()
        self.tree.addTopLevelItem(i)
        self.defaultStylesItem = i = QTreeWidgetItem()
        self.tree.addTopLevelItem(i)
        
        self.defaultStyles = {}
        for name in textformats.defaultStyles:
            self.defaultStyles[name] = i = QTreeWidgetItem()
            self.defaultStylesItem.addChild(i)
            i.name = name
        self.defaultStylesItem.setExpanded(True)
        
        self.allStyles = {}
        for group, title, styles in textformats.allStyles():
            i = QTreeWidgetItem()
            children = {}
            self.allStyles[group] = (i, children)
            self.tree.addTopLevelItem(i)
            i.group = group
            for name, title in styles:
                j = QTreeWidgetItem()
                j.name = name
                i.addChild(j)
                children[name] = j
        
        self.baseColorsWidget = BaseColors(self)
        self.customAttributesWidget = CustomAttributes(self)
        self.emptyWidget = QWidget(self)
        self.stack.addWidget(self.baseColorsWidget)
        self.stack.addWidget(self.customAttributesWidget)
        self.stack.addWidget(self.emptyWidget)
        
        self.tree.currentItemChanged.connect(self.currentItemChanged)
        self.tree.setCurrentItem(self.baseColorsItem)
        self.scheme.currentChanged.connect(self.currentSchemeChanged)
        self.scheme.changed.connect(self.changed)
        self.baseColorsWidget.changed.connect(self.baseColorsChanged)
        self.customAttributesWidget.changed.connect(self.customAttributesChanged)
        
        app.translateUI(self)
        
    def translateUI(self):
        self.baseColorsItem.setText(0, _("Base Colors"))
        self.defaultStylesItem.setText(0, _("Default Styles"))
        for name in textformats.defaultStyles:
            self.defaultStyles[name].setText(0, textformats.defaultStyleNames[name]())
        for group, title, styles in textformats.allStyles():
            self.allStyles[group][0].setText(0, title)
            for name, title in styles:
                self.allStyles[group][1][name].setText(0, title)
            
    def currentItemChanged(self, item, previous):
        if item is self.baseColorsItem:
            self.stack.setCurrentWidget(self.baseColorsWidget)
        elif not item.parent():
            self.stack.setCurrentWidget(self.emptyWidget)
        else:
            data = self.data[self.scheme.currentScheme()]
            w = self.customAttributesWidget
            self.stack.setCurrentWidget(w)
            if item.parent() is self.defaultStylesItem:
                # default style
                w.setTitle(item.text(0))
                w.setTristate(False)
                w.setTextFormat(data.defaultStyles[item.name])
            else:
                # specific style of specific group
                w.setTitle("{0}: {1}".format(item.parent().text(0), item.text(0)))
                w.setTristate(True)
                
    def currentSchemeChanged(self):
        scheme = self.scheme.currentScheme()
        if scheme not in self.data:
            self.data[scheme] = textformats.TextFormatData(scheme)
        self.updateDisplay()
        
    def updateDisplay(self):
        data = self.data[self.scheme.currentScheme()]
        # update base colors
        for name in textformats.baseColors:
            self.baseColorsWidget.color[name].setColor(data.baseColors[name])
        # update base colors for whole treewidget
        p = QApplication.palette()
        p.setColor(QPalette.Base, data.baseColors['background'])
        p.setColor(QPalette.Text, data.baseColors['text'])
        p.setColor(QPalette.Highlight, data.baseColors['selectionbackground'])
        p.setColor(QPalette.HighlightedText, data.baseColors['selectiontext'])
        self.tree.setPalette(p)
        
        baseFont = self.tree.font() # TEMP
        
        # update looks of default styles
        for name in textformats.defaultStyles:
            item = self.defaultStyles[name]
            f = data.defaultStyles[name]
            font = QFont(baseFont)
            if f.hasProperty(QTextFormat.ForegroundBrush):
                item.setForeground(0, f.foreground().color())
            else:
                item.setForeground(0, data.baseColors['text'])
            if f.hasProperty(QTextFormat.BackgroundBrush):
                item.setBackground(0, f.background().color())
            else:
                item.setBackground(0, QBrush())
            font.setWeight(f.fontWeight())
            font.setItalic(f.fontItalic())
            font.setUnderline(f.fontUnderline())
            item.setFont(0, font)
        
    def baseColorsChanged(self, name):
        # keep data up to date with base colors
        data = self.data[self.scheme.currentScheme()]
        data.baseColors[name] = self.baseColorsWidget.color[name].color()
        self.updateDisplay()
        self.changed()
    
    def customAttributesChanged(self):
        item = self.tree.currentItem()
        if not item or not item.parent():
            return
        data = self.data[self.scheme.currentScheme()]
        if item.parent() is self.defaultStylesItem:
            # a default style has been changed
            data.defaultStyles[item.name] = self.customAttributesWidget.textFormat()
        else:
            pass # a custum style has been changed
        self.updateDisplay()
        self.changed()
        
    def loadSettings(self):
        self.data = {} # holds all data with scheme as key
        self.scheme.loadSettings("editor_scheme", "editor_schemes")
        
    def saveSettings(self):
        self.scheme.saveSettings("editor_scheme", "editor_schemes", "fontscolors")
        for scheme in self.data:
            self.data[scheme].save(scheme)


class BaseColors(QGroupBox):
    
    changed = pyqtSignal(unicode)
    
    def __init__(self, parent=None):
        super(BaseColors, self).__init__(parent)
        
        grid = QGridLayout()
        self.setLayout(grid)
        
        self.color = {}
        self.labels = {}
        for name in textformats.baseColors:
            c = self.color[name] = ColorButton(self)
            c.colorChanged.connect((lambda name: lambda: self.changed.emit(name))(name))
            l = self.labels[name] = QLabel()
            l.setBuddy(c)
            row = grid.rowCount()
            grid.addWidget(l, row, 0)
            grid.addWidget(c, row, 1)
        
        grid.setRowStretch(grid.rowCount(), 2)
        app.translateUI(self)
        
    def translateUI(self):
        self.setTitle(_("Base Colors"))
        for name in textformats.baseColors:
            self.labels[name].setText(textformats.baseColorNames[name]())
        

class CustomAttributes(QGroupBox):
    
    changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super(CustomAttributes, self).__init__(parent)
        grid = QGridLayout()
        self.setLayout(grid)
        
        self.toplabel = QLabel()
        grid.addWidget(self.toplabel, 0, 0, 1, 3)
        
        self.textColor = ColorButton()
        l = self.textLabel = QLabel()
        l.setBuddy(self.textColor)
        grid.addWidget(l, 1, 0)
        grid.addWidget(self.textColor, 1, 1)
        c = ClearButton()
        c.clicked.connect(self.textColor.clear)
        grid.addWidget(c, 1, 2)
        
        self.backgroundColor = ColorButton()
        l = self.backgroundLabel = QLabel()
        l.setBuddy(self.backgroundColor)
        grid.addWidget(l, 2, 0)
        grid.addWidget(self.backgroundColor, 2, 1)
        c = ClearButton()
        c.clicked.connect(self.backgroundColor.clear)
        grid.addWidget(c, 2, 2)
        
        self.bold = QCheckBox()
        self.italic = QCheckBox()
        self.underline = QCheckBox()
        grid.addWidget(self.bold, 3, 0)
        grid.addWidget(self.italic, 4, 0)
        grid.addWidget(self.underline, 5, 0)
        
        self.underlineColor = ColorButton()
        grid.addWidget(self.underlineColor, 5, 1)
        c = ClearButton()
        c.clicked.connect(self.underlineColor.clear)
        grid.addWidget(c, 5, 2)
        grid.setRowStretch(6, 2)
        
        self.textColor.colorChanged.connect(self.changed)
        self.backgroundColor.colorChanged.connect(self.changed)
        self.underlineColor.colorChanged.connect(self.changed)
        self.bold.stateChanged.connect(self.changed)
        self.italic.stateChanged.connect(self.changed)
        self.underline.stateChanged.connect(self.changed)
        
        app.translateUI(self)
        
    def translateUI(self):
        self.textLabel.setText(_("Text"))
        self.backgroundLabel.setText(_("Background"))
        self.bold.setText(_("Bold"))
        self.italic.setText(_("Italic"))
        self.underline.setText(_("Underline"))
    
    def setTristate(self, enable):
        self._tristate = enable
        self.bold.setTristate(enable)
        self.italic.setTristate(enable)
        self.underline.setTristate(enable)
    
    def textFormat(self):
        """Returns our settings as a QTextCharFormat object."""
        f = QTextCharFormat()
        if self._tristate:
            value = lambda checkbox: [False, None, True][checkbox.checkState()]
        else:
            value = lambda checkbox: checkbox.isChecked()
        res = value(self.bold)
        if res is not None:
            f.setFontWeight(QFont.Bold if res else QFont.Normal)
        res = value(self.italic)
        if res is not None:
            f.setFontItalic(res)
        res = value(self.underline)
        if res is not None:
            f.setFontUnderline(res)
        if self.textColor.color().isValid():
            f.setForeground(self.textColor.color())
        if self.backgroundColor.color().isValid():
            f.setBackground(self.backgroundColor.color())
        if self.underlineColor.color().isValid():
            f.setUnderlineColor(self.underlineColor.color())
        return f

    def setTextFormat(self, f):
        """Sets our widget to the QTextCharFormat settings."""
        block = self.blockSignals(True)
        absent = Qt.PartiallyChecked if self._tristate else Qt.Unchecked
        if f.hasProperty(QTextFormat.FontWeight):
            self.bold.setChecked(f.fontWeight() >= QFont.Bold)
        else:
            self.bold.setCheckState(absent)
        if f.hasProperty(QTextFormat.FontItalic):
            self.italic.setChecked(f.fontItalic())
        else:
            self.italic.setCheckState(absent)
        if f.hasProperty(QTextFormat.TextUnderlineStyle):
            self.underline.setChecked(f.fontUnderline())
        else:
            self.underline.setCheckState(absent)
        
        if f.hasProperty(QTextFormat.ForegroundBrush):
            self.textColor.setColor(f.foreground().color())
        else:
            self.textColor.setColor(QColor())
        if f.hasProperty(QTextFormat.BackgroundBrush):
            self.backgroundColor.setColor(f.background().color())
        else:
            self.backgroundColor.setColor(QColor())
        if f.hasProperty(QTextFormat.TextUnderlineColor):
            self.underlineColor.setColor(f.underlineColor())
        else:
            self.underlineColor.setColor(QColor())
        self.blockSignals(block)


