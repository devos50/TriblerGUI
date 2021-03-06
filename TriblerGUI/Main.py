import os
import sys
from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QListView, QListWidget, QLineEdit, QListWidgetItem, QApplication, QToolButton, \
    QWidget, QLabel, QTreeWidget, QTreeWidgetItem, QStackedWidget
from TriblerGUI.channel_activity_list_item import ChannelActivityListItem
from TriblerGUI.channel_comment_list_item import ChannelCommentListItem

from TriblerGUI.channel_list_item import ChannelListItem
from TriblerGUI.channel_torrent_list_item import ChannelTorrentListItem
from TriblerGUI.defs import PAGE_SEARCH_RESULTS, PAGE_CHANNEL_CONTENT, PAGE_CHANNEL_COMMENTS, PAGE_CHANNEL_ACTIVITY, \
    PAGE_HOME, PAGE_MY_CHANNEL, PAGE_VIDEO_PLAYER, PAGE_DOWNLOADS, PAGE_SETTINGS, PAGE_SUBSCRIBED_CHANNELS, \
    PAGE_CHANNEL_DETAILS
from TriblerGUI.event_request_manager import EventRequestManager
from TriblerGUI.tribler_request_manager import TriblerRequestManager

# TODO martijn: temporary solution to convince VLC to find the plugin path
os.environ['VLC_PLUGIN_PATH'] = '/Applications/VLC.app/Contents/MacOS/plugins'


class TriblerWindow(QMainWindow):

    resize_event = pyqtSignal()

    def __init__(self):
        super(TriblerWindow, self).__init__()

        self.navigation_stack = []

        uic.loadUi('qt_resources/mainwindow.ui', self)

        # Remove the focus rect on OS X
        [widget.setAttribute(Qt.WA_MacShowFocusRect, 0) for widget in self.findChildren(QLineEdit) +
         self.findChildren(QListView) + self.findChildren(QTreeWidget)]

        self.subscribed_channels_list = self.findChild(QWidget, "subscribed_channels_list")
        self.channel_torrents_list = self.findChild(QWidget, "channel_torrents_list")
        self.top_menu_button = self.findChild(QToolButton, "top_menu_button")
        self.top_search_bar = self.findChild(QLineEdit, "top_search_bar")
        self.top_search_button = self.findChild(QToolButton, "top_search_button")
        self.my_profile_button = self.findChild(QToolButton, "my_profile_button")
        self.video_player_page = self.findChild(QWidget, "video_player_page")
        self.search_results_page = self.findChild(QWidget, "search_results_page")
        self.downloads_page = self.findChild(QWidget, "downloads_page")
        self.settings_page = self.findChild(QWidget, "settings_page")
        self.my_channel_page = self.findChild(QWidget, "my_channel_page")
        self.left_menu = self.findChild(QWidget, "left_menu")

        self.top_search_bar.returnPressed.connect(self.on_top_search_button_click)
        self.top_search_button.clicked.connect(self.on_top_search_button_click)
        self.top_menu_button.clicked.connect(self.on_top_menu_button_click)
        self.search_results_list.itemClicked.connect(self.on_channel_item_click)
        self.subscribed_channels_list.itemClicked.connect(self.on_channel_item_click)

        self.left_menu_home_button = self.findChild(QWidget, "left_menu_home_button")
        self.left_menu_home_button.clicked_menu_button.connect(self.clicked_menu_button)
        self.left_menu_my_channel_button = self.findChild(QWidget, "left_menu_my_channel_button")
        self.left_menu_my_channel_button.clicked_menu_button.connect(self.clicked_menu_button)
        self.left_menu_subscribed_button = self.findChild(QWidget, "left_menu_subscribed_button")
        self.left_menu_subscribed_button.clicked_menu_button.connect(self.clicked_menu_button)
        self.left_menu_downloads_button = self.findChild(QWidget, "left_menu_downloads_button")
        self.left_menu_downloads_button.clicked_menu_button.connect(self.clicked_menu_button)
        self.left_menu_videoplayer_button = self.findChild(QWidget, "left_menu_videoplayer_button")
        self.left_menu_videoplayer_button.clicked_menu_button.connect(self.clicked_menu_button)
        self.left_menu_settings_button = self.findChild(QWidget, "left_menu_settings_button")
        self.left_menu_settings_button.clicked_menu_button.connect(self.clicked_menu_button)

        self.menu_buttons = [self.left_menu_home_button, self.left_menu_my_channel_button,
                             self.left_menu_subscribed_button, self.left_menu_videoplayer_button,
                             self.left_menu_settings_button, self.left_menu_downloads_button]

        channel_back_button = self.findChild(QToolButton, "channel_back_button")
        channel_back_button.clicked.connect(self.on_page_back_clicked)

        self.channel_tab = self.findChild(QWidget, "channel_tab")
        self.channel_tab.initialize()
        self.channel_tab.clicked_tab_button.connect(self.on_channel_tab_button_clicked)
        self.channel_stacked_widget = self.findChild(QStackedWidget, "channel_stacked_widget")

        self.channel_comments_list = self.findChild(QTreeWidget, "channel_comments_list")
        self.channel_activities_list = self.findChild(QListWidget, "channel_activities_list")

        # TODO Martijn: for now, fill the comments and activity items on the channel details page with some dummy data
        for i in range(0, 10):
            parent_item = QTreeWidgetItem(self.channel_comments_list)
            widget_item = ChannelCommentListItem(self.channel_comments_list, 0)
            self.channel_comments_list.setItemWidget(parent_item, 0, widget_item)

            child_item = QTreeWidgetItem(self.channel_comments_list)
            widget_item = ChannelCommentListItem(self.channel_comments_list, 1)
            self.channel_comments_list.setItemWidget(child_item, 0, widget_item)

        for i in range(0, 10):
            item = QListWidgetItem(self.channel_activities_list)
            widget_item = ChannelActivityListItem(self.channel_activities_list)
            item.setSizeHint(widget_item.sizeHint())
            self.channel_activities_list.setItemWidget(item, widget_item)

        # fetch the variables, needed for the video player port
        self.variables_request_mgr = TriblerRequestManager()
        self.variables_request_mgr.get_variables(self.received_variables)

        self.event_request_manager = EventRequestManager()
        self.event_request_manager.received_free_space.connect(self.received_free_space)
        self.event_request_manager.received_download_status.connect(self.downloads_page.received_download_status)

        self.video_player_page.initialize_player()
        self.search_results_page.initialize_search_results_page()
        self.settings_page.initialize_settings_page()
        self.my_channel_page.initialize_my_channel_page()
        self.downloads_page.initialize_downloads_page()

        self.stackedWidget.setCurrentIndex(PAGE_HOME)

        self.show()

    def received_free_space(self, free_space):
        self.statusBar.set_free_space(free_space)

    def received_subscribed_channels(self, results):
        items = []
        for result in results['subscribed']:
            items.append((ChannelListItem, result))
        self.subscribed_channels_list.set_data_items(items)

    def received_torrents_in_channel(self, results):
        items = []
        for result in results['torrents']:
            items.append((ChannelTorrentListItem, result))
        self.channel_torrents_list.set_data_items(items)

    def received_variables(self, variables):
        self.left_menu_home_button.selectMenuButton()
        self.video_player_page.video_player_port = variables["ports"]["video~port"]

    def on_top_search_button_click(self):
        self.clicked_menu_button("-")
        self.stackedWidget.setCurrentIndex(PAGE_SEARCH_RESULTS)
        self.search_results_page.perform_search(self.top_search_bar.text())
        self.search_request_mgr = TriblerRequestManager()
        self.search_request_mgr.search_channels(self.top_search_bar.text(),
                                                self.search_results_page.received_search_results)

    def on_top_menu_button_click(self):
        if self.left_menu.isHidden():
            self.left_menu.show()
        else:
            self.left_menu.hide()

    def on_channel_tab_button_clicked(self, button_name):
        if button_name == "channel_content_button":
            self.channel_stacked_widget.setCurrentIndex(PAGE_CHANNEL_CONTENT)
        elif button_name == "channel_comments_button":
            self.channel_stacked_widget.setCurrentIndex(PAGE_CHANNEL_COMMENTS)
        elif button_name == "channel_activity_button":
            self.channel_stacked_widget.setCurrentIndex(PAGE_CHANNEL_ACTIVITY)

    def clicked_menu_button(self, menu_button_name):
        # Deselect menu buttons
        for button in self.menu_buttons:
            button.unselectMenuButton()

        if menu_button_name == "left_menu_home_button":
            self.left_menu_home_button.selectMenuButton()
            self.stackedWidget.setCurrentIndex(PAGE_HOME)
        elif menu_button_name == "left_menu_my_channel_button":
            self.left_menu_my_channel_button.selectMenuButton()
            self.stackedWidget.setCurrentIndex(PAGE_MY_CHANNEL)
            self.my_channel_page.load_my_channel_overview()
        elif menu_button_name == "left_menu_videoplayer_button":
            self.left_menu_videoplayer_button.selectMenuButton()
            self.stackedWidget.setCurrentIndex(PAGE_VIDEO_PLAYER)
        elif menu_button_name == "left_menu_downloads_button":
            self.left_menu_downloads_button.selectMenuButton()
            self.stackedWidget.setCurrentIndex(PAGE_DOWNLOADS)
        elif menu_button_name == "left_menu_settings_button":
            self.left_menu_settings_button.selectMenuButton()
            self.stackedWidget.setCurrentIndex(PAGE_SETTINGS)
            self.settings_page.load_settings()
        elif menu_button_name == "left_menu_subscribed_button":
            self.left_menu_subscribed_button.selectMenuButton()
            self.subscribed_channels_request_manager = TriblerRequestManager()
            self.subscribed_channels_request_manager.get_subscribed_channels(self.received_subscribed_channels)
            self.stackedWidget.setCurrentIndex(PAGE_SUBSCRIBED_CHANNELS)
        self.navigation_stack = []

    def on_channel_item_click(self, channel_list_item):
        channel_info = channel_list_item.data(Qt.UserRole)
        self.get_torents_in_channel_manager = TriblerRequestManager()
        self.get_torents_in_channel_manager.get_torrents_in_channel(str(channel_info['id']), self.received_torrents_in_channel)
        self.navigation_stack.append(self.stackedWidget.currentIndex())
        self.stackedWidget.setCurrentIndex(PAGE_CHANNEL_DETAILS)

        # initialize the page about a channel
        channel_detail_pane = self.findChild(QWidget, "channel_details")
        channel_name_label = channel_detail_pane.findChild(QLabel, "channel_name_label")
        channel_num_subs_label = channel_detail_pane.findChild(QLabel, "channel_num_subs_label")

        channel_name_label.setText(channel_info['name'])
        channel_num_subs_label.setText(str(channel_info['votes']))

    def on_page_back_clicked(self):
        prev_page = self.navigation_stack.pop()
        self.stackedWidget.setCurrentIndex(prev_page)

    def resizeEvent(self, event):
        self.resize_event.emit()

app = QApplication(sys.argv)
window = TriblerWindow()
window.setWindowTitle("Tribler")
sys.exit(app.exec_())
