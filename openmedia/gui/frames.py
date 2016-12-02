# -*- coding: utf-8 -*-

import gi
from gi.repository import Gtk, Gio, GObject
from openmedia.player import mixer
from openmedia.observable.observable import Observer
from openmedia.tools.timeformatter import hms_format

class InvalidWidgetStateException(Exception):
    pass

class PlayerFrame(Gtk.Window, Observer):
    def __init__(self):
        Gtk.Window.__init__(self, title="open-media")
        Observer.__init__(self)
        self.skipping = False
        self.connect("delete-event", self.halt)
        mixer.add_observer(self)
        self._create_control_widgets()
        self._create_playlist()
        self.progress = Gtk.Scale()
        self.progress.set_range(0, mixer.get_song_duration())
        self.progress.connect("button-press-event", self._start_skip)
        self.progress.connect("button-release-event", self._end_skip)
        self.progress.connect("format-value", _hms_format)
        self.progress.set_value(0)
        self.progress.set_vexpand(False)

        self.leftBox = Gtk.VBox()
        self.leftBox.pack_start(self.buttonsBox, True, False, 0)
        self.leftBox.pack_start(self.progress, False, False, 0)
        self.leftBox.set_vexpand(False)

        self.controlBox = Gtk.VBox()
        self.controlBox.set_border_width(10)
        self.controlBox.set_spacing(5)
        self.controlBox.pack_start(self.playlistBox, False, False, 0)
        self.controlBox.pack_start(self.leftBox, False, True, 0)
        self.controlBox.set_vexpand(False)

        self.mainVBox = Gtk.VBox();

        self.mainVBox.pack_start(self.controlBox, False, False, 0)
        self.mainVBox.set_vexpand(False)
        self.set_default_size(-1, 120)
        self._create_status_bar()
        self.mainVBox.pack_end(self.statusBar, False, False, 0)
        self.mainVBox.pack_end(Gtk.HSeparator(), False, False, 0)
        self.add(self.mainVBox)

    def _create_status_bar(self):
        self.statusBar = Gtk.Statusbar()
        self.lastContextId = None
        self._update_status("Stopped.")

    def _create_control_widgets(self):
        self.play_button = Gtk.Button(label=u'▶')
        self.play_button.connect("clicked", self._play_pause)
        self.play_button.set_vexpand(False)

        self.stop_button = Gtk.Button(label=u'■')
        self.stop_button.connect("clicked", self._stop)
        self.stop_button.set_vexpand(False)

        self.play_next_button = Gtk.Button(label=">>")
        self.play_next_button.connect("clicked", self._play_next)
        self.play_next_button.set_vexpand(False)

        self.volume_button = Gtk.VolumeButton()
        self.volume_button.set_value(0.5)
        self.volume_button.connect("value-changed", self._volume)
        self.volume_button.x_align = 1.0
        self.volume_button.set_vexpand(False)

        self.playlist_button = Gtk.ToggleButton(label="=")
        self.playlist_button.connect("clicked", self._toggle_playlist)
        self.playlist_button.set_vexpand(False)

        self.buttonsBox = Gtk.HBox(False)
        self.buttonsBox.set_spacing(5)
        self.buttonsBox.pack_start(self.play_button, False, False, 0)
        self.buttonsBox.pack_start(self.stop_button, False, False, 0)
        self.buttonsBox.pack_start(self.play_next_button, False, False, 0)
        self.volumeBox = Gtk.HBox()
        self.volumeBox.pack_end(self.volume_button, False, True, 0)
        self.buttonsBox.pack_start(self.playlist_button, False, False, 0)
        self.buttonsBox.pack_end(self.volumeBox, True, True, 0)
        self.buttonsBox.set_vexpand(False)

    def _create_playlist(self):
        self.model = Gio.ListStore.new(ModelItem)
        self.playlist = Gtk.ListBox()
        self.playlist.bind_model(self.model, self._create_list_item, None)
        self.playlist.connect("row_activated", self._play_item)
        for track in mixer.track_list:
            item = ModelItem(track.metadata.track_name, track.duration)
            self.model.append(item)
        self.playlist.select_row(self.playlist.get_row_at_index(0))
        self.add_track = Gtk.Button(label="+")
        self.add_track.connect("clicked", self._add_track)

        self.playlistBox = Gtk.VBox()
        self.playlistBox.set_spacing(5)
        self.playlistBox.pack_start(self.playlist, False, False, 0)
        self.playlistBox.pack_start(self.add_track, False, False, 0)
        self.playlistBox.set_vexpand(False)

    def _create_list_item(self, item, data):
        hbox = Gtk.HBox(5)
        title_label = Gtk.Label(item.title)
        duration_label = Gtk.Label(hms_format(item.duration))
        title_label.show()
        duration_label.show()
        hbox.pack_start(title_label, False, False, 0)
        hbox.pack_start(duration_label, False, False, 0)
        return hbox

    def _play_item(self, list_box, row):
        mixer.play(mixer.track_list[row.get_index()].file_path)

    def _add_track(self, widget):
        dialog = Gtk.FileChooserDialog(Gtk.FileChooserAction.OPEN)
        dialog.set_transient_for(self)
        dialog.set_title("Add tracks to your playlist")
        dialog.add_button("_Open", Gtk.ResponseType.OK)
        dialog.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        dialog.set_default_response(Gtk.ResponseType.OK)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            mixer.add(dialog.get_filename())
            self.model.append(ModelItem(mixer.track_list[-1].metadata.track_name,\
                              mixer.track_list[-1].duration))
            self.show_all()
        dialog.destroy()

    def _start_skip(self, widget, value):
        self.skipping = True

    def _end_skip(self, widget, value):
        mixer.skip(widget.get_value())
        self.skipping = False

    def show(self):
        self.show_all()
        self.playlistBox.hide()

    def update(self, event, event_type):
        if event_type == mixer.PLAY_EVENT or event_type == mixer.NEXT_EVENT:
            self.progress.set_range(0, mixer.get_song_duration())
            self.play_button.get_children()[0].set_text(u'▌▌')
            row = self.playlist.get_row_at_index(mixer.curr_track_index)
            self.playlist.select_row(row)
            self._update_status("Playing '" + str(mixer.current_track.name) + "'.")
        elif event_type == mixer.PAUSE_EVENT or event_type == mixer.STOP_EVENT:
            self.play_button.get_children()[0].set_text('▶')
            if event_type == mixer.PAUSE_EVENT:
                self._update_status("Paused.")
            else:
                self._update_status("Stopped.")
        elif event_type == mixer.SLIDER_EVENT and not self.skipping:
            self.progress.set_value(mixer.get_pos()/1000)
            if mixer.is_playing():
                self._update_status("Playing '" + str(mixer.current_track.name) + "'.")
        return False

    def _play_pause(self, widget):
        if mixer.is_playing():
            mixer.pause()
        else:
            mixer.play()

    def _play_next(self, widget):
        mixer.play_next()
        if self.playlistBox.is_visible():
            self.playlistBox.show_all()

    def _stop(self, widget):
        mixer.stop()

    def _volume(self, widget, value):
        mixer.set_volume(value)

    def _toggle_playlist(self, widget):
        if self.playlistBox.is_visible():
            self.playlistBox.set_visible(False)
        else:
            self.playlistBox.set_visible(True)

    def _update_status(self, text="Nothing to show."):
        if self.lastContextId:
            self.statusBar.pop(self.lastContextId)
        self.lastContextId = self.statusBar.push(self.statusBar.get_context_id(text), text)


    def halt(self, window, event):
        mixer.stop()
        Gtk.main_quit()

def _hms_format(scale, value):
    return hms_format(value)

class ModelItem(GObject.Object):

    def __init__(self, title, duration):
        GObject.Object.__init__(self)
        self.title = title
        self.duration = duration

