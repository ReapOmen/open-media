# -*- coding: utf-8 -*-

from gi.repository import Gtk


button_icon_name = {"play"      : "media-playback-start-symbolic",
                    "pause"     : "media-playback-pause-symbolic",
                    "stop"      : "media-playback-stop-symbolic",
                    "skip"      : "media-skip-forward-symbolic",
                    "prev"      : "media-skip-backward-symbolic",
                    "add"       : "list-add-symbolic",
                    "shuffle"   : "media-playlist-shuffle-symbolic",
                    "menu"      : "open-menu-symbolic",
                    "inc-speed" : "media-seek-forward-symbolic",
                    "dec-speed" : "media-seek-forward-rtl-symbolic"}


def get_button_image(icon_name):
    button_image = Gtk.Image()
    button_image.set_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
    return button_image


def get_name(button_name):
    return button_icon_name[button_name]
