from Tools.Profile import profile
from Tools.BoundFunction import boundFunction
from enigma import eServiceReference

# workaround for required config entry dependencies.
import Screens.MovieSelection

from Screen import Screen
from Screens.MessageBox import MessageBox

profile("LOAD:enigma")
import enigma
#+++>
from enigma import iServiceInformation, iPlayableService
#+++<

profile("LOAD:InfoBarGenerics")
from Screens.InfoBarGenerics import InfoBarShowHide, \
	InfoBarNumberZap, InfoBarChannelSelection, InfoBarMenu, InfoBarRdsDecoder, \
	InfoBarEPG, InfoBarSeek, InfoBarInstantRecord, InfoBarRedButton, InfoBarTimerButton, InfoBarVmodeButton, \
	InfoBarAudioSelection, InfoBarAdditionalInfo, InfoBarNotifications, InfoBarDish, InfoBarUnhandledKey, \
	InfoBarSubserviceSelection, InfoBarShowMovies, InfoBarTimeshift,  \
	InfoBarServiceNotifications, InfoBarPVRState, InfoBarCueSheetSupport, InfoBarBuffer, \
	InfoBarSummarySupport, InfoBarMoviePlayerSummarySupport, InfoBarTimeshiftState, InfoBarTeletextPlugin, InfoBarExtensions, \
	InfoBarSubtitleSupport, InfoBarPiP, InfoBarPlugins, InfoBarServiceErrorPopupSupport, InfoBarJobman, InfoBarPowersaver, \
	InfoBarAspectSelection, InfoBarSleepTimer, \
	InfoBarHDMI, setResumePoint, delResumePoint
from Screens.Hotkey import InfoBarHotkey

profile("LOAD:InitBar_Components")
from Components.ActionMap import HelpableActionMap
from Components.config import config
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase

profile("LOAD:HelpableScreen")
from Screens.HelpMenu import HelpableScreen

class InfoBar(InfoBarBase, InfoBarShowHide,
	InfoBarNumberZap, InfoBarChannelSelection, InfoBarMenu, InfoBarEPG, InfoBarRdsDecoder,
	InfoBarInstantRecord, InfoBarAudioSelection, InfoBarRedButton, InfoBarTimerButton, InfoBarVmodeButton,
	HelpableScreen, InfoBarAdditionalInfo, InfoBarNotifications, InfoBarDish, InfoBarUnhandledKey,
	InfoBarSubserviceSelection, InfoBarTimeshift, InfoBarSeek, InfoBarCueSheetSupport, InfoBarBuffer,
	InfoBarSummarySupport, InfoBarTimeshiftState, InfoBarTeletextPlugin, InfoBarExtensions,
	InfoBarPiP, InfoBarPlugins, InfoBarSubtitleSupport, InfoBarServiceErrorPopupSupport, InfoBarJobman, InfoBarPowersaver,
	InfoBarAspectSelection, InfoBarSleepTimer,
	InfoBarHDMI, InfoBarHotkey, Screen):

	ALLOW_SUSPEND = True
	instance = None

	def __init__(self, session):
		Screen.__init__(self, session)
		self["actions"] = HelpableActionMap(self, "InfobarActions",
			{
				"showMovies": (self.showMovies, _("Play recorded movies...")),
				"showRadio": (self.showRadio, _("Show the radio player...")),
				"showTv": (self.showTv, _("Show the tv player...")),
				"toogleTvRadio": (self.toogleTvRadio, _("toggels betwenn tv and radio...")),
				"volumeUp": (self._volUp, _("Volume up")),
				"volumeDown": (self._volDown, _("Volume down")),
				"resolution": (self.resolution, _("Open resolution menu")),
				"aspect": (self.aspect, _("Open aspect ratio menu")),
				"showPlugins": (self.showPlugins, _("Open plugin browser")),
				"FreePlayer": (self.FreePlayer, _("Open FreePlayer plugin")),
				"BitrateViewer": (self.BitrateViewer, _("Open BitrateViewer plugin")),
				"ScartHdmi": (self.ScartHdmi, _("Switch betwen SCART and HDMI")),
				"restart_softcam": (self.restartSoftcam, _("Restart softcam")),
			}, prio=2)

		self.allowPiP = True

		for x in HelpableScreen, \
				InfoBarBase, InfoBarShowHide, \
				InfoBarNumberZap, InfoBarChannelSelection, InfoBarMenu, InfoBarEPG, InfoBarRdsDecoder, \
				InfoBarInstantRecord, InfoBarAudioSelection, InfoBarRedButton, InfoBarTimerButton, InfoBarUnhandledKey, InfoBarVmodeButton,\
				InfoBarAdditionalInfo, InfoBarNotifications, InfoBarDish, InfoBarSubserviceSelection, InfoBarBuffer, \
				InfoBarTimeshift, InfoBarSeek, InfoBarCueSheetSupport, InfoBarSummarySupport, InfoBarTimeshiftState, \
				InfoBarTeletextPlugin, InfoBarExtensions, InfoBarPiP, InfoBarSubtitleSupport, InfoBarJobman, InfoBarPowersaver, \
				InfoBarAspectSelection, InfoBarSleepTimer, \
				InfoBarPlugins, InfoBarServiceErrorPopupSupport, InfoBarHotkey:
			x.__init__(self)

		self.helpList.append((self["actions"], "InfobarActions", [("showMovies", _("Watch recordings..."))]))
		self.helpList.append((self["actions"], "InfobarActions", [("showRadio", _("Listen to the radio..."))]))

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				enigma.iPlayableService.evUpdatedEventInfo: self.__eventInfoChanged
			})

		self.current_begin_time=0
		assert InfoBar.instance is None, "class InfoBar is a singleton class and just one instance of this class is allowed!"
		InfoBar.instance = self

	def aspect(self):
		selection = 0
		tlist = []
		try:
			policy = open("/proc/stb/video/policy_choices").read()[:-1]
		except IOError:
			print "couldn't read available policymodes."
			policy_available = [ ]
			return
		policy_available = policy.split(' ')
		for x in policy_available:
			tlist.append((x[0].upper() + x[1:], _(x)))

		mode = open("/proc/stb/video/policy").read()[:-1]
		for x in range(len(tlist)):
			if tlist[x][1] == mode:
				selection = x

		keys = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9" ]
		from Screens.ChoiceBox import ChoiceBox
		self.session.openWithCallback(self.aspectSelect, ChoiceBox, title=_("Please select an aspect ratio..."), list = tlist, selection = selection, keys = keys)

	def aspectSelect(self, aspect):
		if not aspect is None:
			if isinstance(aspect[1], str):
				open("/proc/stb/video/policy", "w").write(aspect[1])
		return

	def resolution(self):
		xresString = open("/proc/stb/vmpeg/0/xres", "r").read()
		yresString = open("/proc/stb/vmpeg/0/yres", "r").read()
		fpsString = open("/proc/stb/vmpeg/0/framerate", "r").read()
		xres = int(xresString, 16)
		yres = int(yresString, 16)
		fps = int(fpsString, 16)
		fpsFloat = float(fps)
		fpsFloat = fpsFloat/1000

		selection = 0
		tlist = []
		tlist.append(("Video: " + str(xres) + "x" + str(yres) + "@" + str(fpsFloat) + "hz", ""))
		tlist.append(("--", ""))
		tlist.append(("576i", "576i50"))
		tlist.append(("576p", "576p50"))
		tlist.append(("720p@50hz", "720p50"))
		tlist.append(("720p@60hz", "720p60"))
		tlist.append(("1080i@50hz", "1080i50"))
		tlist.append(("1080i@60hz", "1080i60"))
		tlist.append(("1080p@23.976hz", "1080p23"))
		tlist.append(("1080p@24hz", "1080p24"))
		tlist.append(("1080p@25hz", "1080p25"))
		tlist.append(("1080p@30hz", "1080p30"))
		tlist.append(("1080p@50hz", "1080p50"))
		tlist.append(("1080p@59hz", "1080p59"))
		tlist.append(("1080p@60hz", "1080p60"))
		keys = ["green", "", "yellow", "blue", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9" ]

		mode = open("/proc/stb/video/videomode").read()[:-1]
		for x in range(len(tlist)):
			if tlist[x][1] == mode:
				selection = x
		from Screens.ChoiceBox import ChoiceBox
		self.session.openWithCallback(self.ResolutionSelect, ChoiceBox, title=_("Please select a resolution..."), list = tlist, selection = selection, keys = keys)

	def ResolutionSelect(self, Resolution):
		if not Resolution is None:
			if isinstance(Resolution[1], str):
				open("/proc/stb/video/videomode", "w").write(Resolution[1])
				from enigma import gMainDC
				gMainDC.getInstance().setResolution(-1, -1)
		return

	def _volUp(self):
		print "_volUp"
		from Components.VolumeControl import VolumeControl
		VolumeControl.instance.volUp()

	def _volDown(self):
		print "_volDown"
		from Components.VolumeControl import VolumeControl
		VolumeControl.instance.volDown()

	def __onClose(self):
		InfoBar.instance = None

	def __eventInfoChanged(self):
		if self.execing:
			service = self.session.nav.getCurrentService()
			old_begin_time = self.current_begin_time
			info = service and service.info()
			ptr = info and info.getEvent(0)
			self.current_begin_time = ptr and ptr.getBeginTime() or 0
			if config.usage.show_infobar_on_event_change.value:
				if old_begin_time and old_begin_time != self.current_begin_time:
					self.doShow()

	def __checkServiceStarted(self):
		self.__serviceStarted(True)
		self.onExecBegin.remove(self.__checkServiceStarted)

	def toogleTvRadio(self): 
		service = self.session.nav.getCurrentService()
		if service:
			info = service.info()
			if info:
				AudioPID = info.getInfo(iServiceInformation.sAudioPID)
				VideoPID = info.getInfo(iServiceInformation.sVideoPID)

				print "sAudioPID", AudioPID
				print "sVideoPID", VideoPID

				if VideoPID == -1:
					print "radio->tv"
					self.showTv2()
				else:
					print "tv->radio"
					self.showRadio2()

	def serviceStarted(self):  #override from InfoBarShowHide
		new = self.servicelist.newServicePlayed()
		if self.execing:
			InfoBarShowHide.serviceStarted(self)
			self.current_begin_time=0
		elif not self.__checkServiceStarted in self.onShown and new:
			self.onShown.append(self.__checkServiceStarted)

	def __checkServiceStarted(self):
		self.serviceStarted()
		self.onShown.remove(self.__checkServiceStarted)

	def showTv(self):
		self.showTvChannelList(True)

	def showRadio(self):
		if config.usage.e1like_radio_mode.value:
			self.showRadioChannelList(True)
		else:
			self.rds_display.hide() # in InfoBarRdsDecoder
			from Screens.ChannelSelection import ChannelSelectionRadio
			self.session.openWithCallback(self.ChannelSelectionRadioClosed, ChannelSelectionRadio, self)

	def showTv2(self):
		self.showTvChannelList(False)
		self.openServiceList()

	def showRadio2(self):
		if config.usage.e1like_radio_mode.value:
			self.showRadioChannelList(False)
			self.openServiceList()
		else:
			self.rds_display.hide() # in InfoBarRdsDecoder
			from Screens.ChannelSelection import ChannelSelectionRadio
			self.session.openWithCallback(self.ChannelSelectionRadioClosed, ChannelSelectionRadio, self)

	def ChannelSelectionRadioClosed(self, *arg):
		self.rds_display.show()  # in InfoBarRdsDecoder
		self.servicelist.correctChannelNumber()

	def showMovies(self, defaultRef=None):
		self.lastservice = self.session.nav.getCurrentlyPlayingServiceOrGroup()
		self.session.openWithCallback(self.movieSelected, Screens.MovieSelection.MovieSelection, defaultRef or eServiceReference(config.usage.last_movie_played.value), timeshiftEnabled = self.timeshiftEnabled())

	def movieSelected(self, service):
		ref = self.lastservice
		del self.lastservice
		if service is None:
			if ref and not self.session.nav.getCurrentlyPlayingServiceOrGroup():
				self.session.nav.playService(ref)
		else:
			from Components.ParentalControl import parentalControl
			if parentalControl.isServicePlayable(service, self.openMoviePlayer):
				self.openMoviePlayer(service)

	def openMoviePlayer(self, ref):
		self.session.open(MoviePlayer, ref, slist=self.servicelist, lastservice=self.session.nav.getCurrentlyPlayingServiceOrGroup(), infobar=self)

	def showPlugins(self):
		from Screens.PluginBrowser import PluginBrowser
		self.session.open(PluginBrowser)

	def FreePlayer(self):
		def FreePlayerPlugin():
			try:
				from Plugins.Extensions.FreePlayer.plugin import FreePlayer
			except ImportError:
				return False
			else:
				return True
				
		if FreePlayerPlugin():
			from Plugins.Extensions.FreePlayer.plugin import FreePlayer
			self.session.open(FreePlayer.FreePlayerStart)
		else:
			print "FreePlayer plugin not found!"

	def BitrateViewer(self):
		def BitrateViewerPlugin():
			try:
				from Plugins.Extensions.Bitrate.plugin import BitrateViewer
			except ImportError:
				return False
			else:
				return True
				
		if BitrateViewerPlugin():
			from Plugins.Extensions.Bitrate.plugin import BitrateViewer
			self.session.open(BitrateViewer)
		else:
			print "BitrateViewer plugin not found!"
			
	def startTeletext(self):
		self.teletext_plugin(session=self.session, service=self.session.nav.getCurrentService())

	def restartSoftcam(self):
		from Screens.Console import Console
		from Tools.Directories import fileExists
		if fileExists('/etc/init.d/softcam'):
			self.session.open(Console, 'Restart Softcam', ['/etc/init.d/softcam restart'], closeOnSuccess = True)
		else:
			print "Softcam startup screen not found!"

	def ScartHdmi(self):
		if isinstance(self, InfoBar):
			#print '****** videomode ******'
			port = config.av.videoport.value
			#print 'actual port = ', port
			from Plugins.SystemPlugins.Videomode.VideoHardware import video_hw
			if port == 'HDMI':
				port = 'Scart'
				mode = 'PAL'
				rate = '50Hz'
				config.av.videoport.value = port
				config.av.videomode[port].value = mode
				config.av.videorate[mode].value = rate
				config.av.save()
				video_hw.setMode(port, mode, rate)
			else:
				port = 'HDMI'
				mode = '720p'
				rate = '50Hz'
				config.av.videoport.value = port
				config.av.videomode[port].value = mode
				config.av.videorate[mode].value = rate
				config.av.save()
				video_hw.setMode(port, mode, rate)
			self.session.open(MessageBox, 'Videomode changed to ' + mode + ' at ' + rate + ' on ' + port, MessageBox.TYPE_INFO, timeout=10)
						
class MoviePlayer(InfoBarBase, InfoBarShowHide, InfoBarMenu, InfoBarSeek, InfoBarShowMovies, InfoBarInstantRecord,
		InfoBarAudioSelection, HelpableScreen, InfoBarNotifications, InfoBarServiceNotifications, InfoBarPVRState,
		InfoBarCueSheetSupport, InfoBarMoviePlayerSummarySupport, InfoBarSubtitleSupport, Screen, InfoBarTeletextPlugin,
		InfoBarAspectSelection,
		InfoBarServiceErrorPopupSupport, InfoBarExtensions, InfoBarPlugins, InfoBarPiP, InfoBarHDMI, InfoBarHotkey):

	ENABLE_RESUME_SUPPORT = True
	ALLOW_SUSPEND = True

	def __init__(self, session, service, slist=None, lastservice=None, infobar=None):
		Screen.__init__(self, session)

		InfoBarAspectSelection.__init__(self)

		self["actions"] = HelpableActionMap(self, "MoviePlayerActions",
			{
				"leavePlayer": (self.leavePlayer, _("leave movie player...")),
				"leavePlayerOnExit": (self.leavePlayerOnExit, _("leave movie player...")),
				"channelUp": (self.channelUp, _("when PiPzap enabled zap channel up...")),
				"channelDown": (self.channelDown, _("when PiPzap enabled zap channel down...")),
			})

		self["DirectionActions"] = HelpableActionMap(self, "DirectionActions",
			{
				"left": self.left,
				"right": self.right
			}, prio = -2)

		self.allowPiP = True

		for x in HelpableScreen, InfoBarShowHide, InfoBarMenu, \
				InfoBarBase, InfoBarSeek, InfoBarShowMovies, InfoBarInstantRecord, \
				InfoBarAudioSelection, InfoBarNotifications, \
				InfoBarServiceNotifications, InfoBarPVRState, InfoBarCueSheetSupport, \
				InfoBarMoviePlayerSummarySupport, InfoBarSubtitleSupport, \
				InfoBarTeletextPlugin, InfoBarServiceErrorPopupSupport, InfoBarExtensions, \
				InfoBarPlugins, InfoBarPiP, InfoBarHotkey:
			x.__init__(self)

		self.servicelist = slist
		self.infobar = infobar
		self.lastservice = lastservice or session.nav.getCurrentlyPlayingServiceOrGroup()
		session.nav.playService(service)
		self.cur_service = service
		self.returning = False
		self.onClose.append(self.__onClose)
		config.misc.standbyCounter.addNotifier(self.standbyCountChanged, initial_call=False)

	def __onClose(self):
		config.misc.standbyCounter.removeNotifier(self.standbyCountChanged)
		from Screens.MovieSelection import playlist
		del playlist[:]
		if not config.movielist.stop_service.value:
			Screens.InfoBar.InfoBar.instance.callServiceStarted()
		self.session.nav.playService(self.lastservice)
		config.usage.last_movie_played.value = self.cur_service.toString()
		config.usage.last_movie_played.save()

	def standbyCountChanged(self, value):
		if config.ParentalControl.servicepinactive.value:
			from Components.ParentalControl import parentalControl
			if parentalControl.isProtected(self.cur_service):
				self.close()

	def handleLeave(self, how):
		self.is_closing = True
		if how == "ask":
			if config.usage.setup_level.index < 2: # -expert
				list = (
					(_("Yes"), "quit"),
					(_("No"), "continue")
				)
			else:
				list = (
					(_("Yes"), "quit"),
					(_("Yes, returning to movie list"), "movielist"),
					(_("Yes, and delete this movie"), "quitanddelete"),
					(_("Yes, delete this movie and return to movie list"), "deleteandmovielist"),
					(_("No"), "continue"),
					(_("No, but restart from begin"), "restart")
				)

			from Screens.ChoiceBox import ChoiceBox
			self.session.openWithCallback(self.leavePlayerConfirmed, ChoiceBox, title=_("Stop playing this movie?"), list = list)
		else:
			self.leavePlayerConfirmed([True, how])

	def leavePlayer(self):
		setResumePoint(self.session)
		self.handleLeave(config.usage.on_movie_stop.value)

	def leavePlayerOnExit(self):
		if self.shown:
			self.hide()
		elif self.session.pipshown and "popup" in config.usage.pip_hideOnExit.value:
			if config.usage.pip_hideOnExit.value == "popup":
				self.session.openWithCallback(self.hidePipOnExitCallback, MessageBox, _("Disable Picture in Picture"), simple=True)
			else:
				self.hidePipOnExitCallback(True)
		elif config.usage.leave_movieplayer_onExit.value == "movielist":
			self.leavePlayer()
		elif config.usage.leave_movieplayer_onExit.value == "popup":
			self.session.openWithCallback(self.leavePlayerOnExitCallback, MessageBox, _("Exit movie player?"), simple=True)
		elif config.usage.leave_movieplayer_onExit.value == "without popup":
			self.leavePlayerOnExitCallback(True)

	def leavePlayerOnExitCallback(self, answer):
		if answer == True:
			setResumePoint(self.session)
			self.handleLeave("quit")

	def hidePipOnExitCallback(self, answer):
		if answer == True:
			self.showPiP()

	def deleteConfirmed(self, answer):
		if answer:
			self.leavePlayerConfirmed((True, "quitanddeleteconfirmed"))

	def deleteAndMovielistConfirmed(self, answer):
		if answer:
			self.leavePlayerConfirmed((True, "deleteandmovielistconfirmed"))

	def movielistAgain(self):
		from Screens.MovieSelection import playlist
		del playlist[:]
		self.leavePlayerConfirmed((True, "movielist"))

	def leavePlayerConfirmed(self, answer):
		answer = answer and answer[1]
		if answer is None:
			return
		if answer in ("quitanddelete", "quitanddeleteconfirmed", "deleteandmovielist", "deleteandmovielistconfirmed"):
			ref = self.session.nav.getCurrentlyPlayingServiceOrGroup()
			serviceHandler = enigma.eServiceCenter.getInstance()
			if answer in ("quitanddelete", "deleteandmovielist"):
				msg = ''
				if config.usage.movielist_trashcan.value:
					import Tools.Trashcan
					try:
						trash = Tools.Trashcan.createTrashFolder(ref.getPath())
						Screens.MovieSelection.moveServiceFiles(ref, trash)
						# Moved to trash, okay
						if answer == "quitanddelete":
							self.close()
						else:
							self.movielistAgain()
						return
					except Exception, e:
						print "[InfoBar] Failed to move to .Trash folder:", e
						msg = _("Cannot move to trash can") + "\n" + str(e) + "\n"
				info = serviceHandler.info(ref)
				name = info and info.getName(ref) or _("this recording")
				msg += _("Do you really want to delete %s?") % name
				if answer == "quitanddelete":
					self.session.openWithCallback(self.deleteConfirmed, MessageBox, msg)
				elif answer == "deleteandmovielist":
					self.session.openWithCallback(self.deleteAndMovielistConfirmed, MessageBox, msg)
				return

			elif answer in ("quitanddeleteconfirmed", "deleteandmovielistconfirmed"):
				offline = serviceHandler.offlineOperations(ref)
				if offline.deleteFromDisk(0):
					self.session.openWithCallback(self.close, MessageBox, _("You cannot delete this!"), MessageBox.TYPE_ERROR)
					if answer == "deleteandmovielistconfirmed":
						self.movielistAgain()
					return

		if answer in ("quit", "quitanddeleteconfirmed"):
#+++>
			# make sure that playback is unpaused otherwise the
			# player driver might stop working
			self.setSeekState(self.SEEK_STATE_PLAY)
#+++<
			self.close()
		elif answer in ("movielist", "deleteandmovielistconfirmed"):
			ref = self.session.nav.getCurrentlyPlayingServiceOrGroup()
			self.returning = True
			self.session.openWithCallback(self.movieSelected, Screens.MovieSelection.MovieSelection, ref)
#+++>
			# make sure that playback is unpaused otherwise the
			# player driver might stop working
			self.setSeekState(self.SEEK_STATE_PLAY)
#+++<
			self.session.nav.stopService()
			if not config.movielist.stop_service.value:
				self.session.nav.playService(self.lastservice)
		elif answer == "restart":
			self.doSeek(0)
			self.setSeekState(self.SEEK_STATE_PLAY)
		elif answer in ("playlist","playlistquit","loop"):
			( next_service, item , lenght ) = self.getPlaylistServiceInfo(self.cur_service)
			if next_service is not None:
				if config.usage.next_movie_msg.value:
					self.displayPlayedName(next_service, item, lenght)
				self.session.nav.playService(next_service)
				self.cur_service = next_service
			else:
				if answer == "playlist":
					self.leavePlayerConfirmed([True,"movielist"])
				elif answer == "loop" and lenght > 0:
					self.leavePlayerConfirmed([True,"loop"])
				else:
					self.leavePlayerConfirmed([True,"quit"])
		elif answer in ("repeatcurrent"):
			if config.usage.next_movie_msg.value:
				(item, lenght) = self.getPlaylistServiceInfo(self.cur_service)
				self.displayPlayedName(self.cur_service, item, lenght)
			self.session.nav.stopService()
			self.session.nav.playService(self.cur_service)

	def doEofInternal(self, playing):
		if not self.execing:
			return
		if not playing :
			return
		ref = self.session.nav.getCurrentlyPlayingServiceOrGroup()
		if ref:
			delResumePoint(ref)
		self.handleLeave(config.usage.on_movie_eof.value)

	def up(self):
		if self.servicelist and self.servicelist.dopipzap:
			if config.usage.oldstyle_zap_controls.value:
				self.zapDown()
			else:
				self.switchChannelUp()
		else:
			self.showMovies()

	def down(self):
		if self.servicelist and self.servicelist.dopipzap:
			if config.usage.oldstyle_zap_controls.value:
				self.zapUp()
			else:
				self.switchChannelDown()
		else:
			self.showMovies()

	def right(self):
		if self.servicelist and self.servicelist.dopipzap:
			if config.usage.oldstyle_zap_controls.value:
				self.switchChannelDown()
			else:
				self.zapDown()
		else:
			InfoBarSeek.seekFwd(self)

	def left(self):
		if self.servicelist and self.servicelist.dopipzap:
			if config.usage.oldstyle_zap_controls.value:
				self.switchChannelUp()
			else:
				self.zapUp()
		else:
			InfoBarSeek.seekBack(self)

	def channelUp(self):
		if config.usage.zap_with_ch_buttons.value and self.servicelist and self.servicelist.dopipzap:
			self.zapDown()
		else:
			return 0

	def channelDown(self):
		if config.usage.zap_with_ch_buttons.value and self.servicelist and self.servicelist.dopipzap:
			self.zapUp()
		else:
			return 0

	def switchChannelDown(self):
		if self.servicelist:
			if "keep" not in config.usage.servicelist_cursor_behavior.value:
				self.servicelist.moveDown()
			self.session.execDialog(self.servicelist)

	def switchChannelUp(self):
		if self.servicelist:
			if "keep" not in config.usage.servicelist_cursor_behavior.value:
				self.servicelist.moveUp()
			self.session.execDialog(self.servicelist)

	def zapUp(self):
		slist = self.servicelist
		if slist:
			if slist.inBouquet():
				prev = slist.getCurrentSelection()
				if prev:
					prev = prev.toString()
					while True:
						if config.usage.quickzap_bouquet_change.value:
							if slist.atBegin():
								slist.prevBouquet()
						slist.moveUp()
						cur = slist.getCurrentSelection()
						if cur:
							playable = not (cur.flags & (64|8)) and hasattr(self.session, "pip") and self.session.pip.isPlayableForPipService(cur)
							if cur.toString() == prev or playable:
								break
			else:
				slist.moveUp()
			slist.zap(enable_pipzap = True)

	def zapDown(self):
		slist = self.servicelist
		if slist:
			if slist.inBouquet():
				prev = slist.getCurrentSelection()
				if prev:
					prev = prev.toString()
					while True:
						if config.usage.quickzap_bouquet_change.value and slist.atEnd():
							slist.nextBouquet()
						else:
							slist.moveDown()
						cur = slist.getCurrentSelection()
						if cur:
							playable = not (cur.flags & (64|8)) and hasattr(self.session, "pip") and self.session.pip.isPlayableForPipService(cur)
							if cur.toString() == prev or playable:
								break
			else:
				slist.moveDown()
			slist.zap(enable_pipzap = True)

	def showPiP(self):
		slist = self.servicelist
		if self.session.pipshown:
			if slist and slist.dopipzap:
				slist.togglePipzap()
			if self.session.pipshown:
				del self.session.pip
				self.session.pipshown = False
		elif slist:
			from Screens.PictureInPicture import PictureInPicture
			self.session.pip = self.session.instantiateDialog(PictureInPicture)
			self.session.pip.show()
			if self.session.pip.playService(slist.getCurrentSelection()):
				self.session.pipshown = True
				self.session.pip.servicePath = slist.getCurrentServicePath()
			else:
				self.session.pipshown = False
				del self.session.pip

	def movePiP(self):
		if self.session.pipshown:
			InfoBarPiP.movePiP(self)

	def swapPiP(self):
		pass

	def showDefaultEPG(self):
		self.infobar and self.infobar.showMultiEPG()

	def openEventView(self):
		self.infobar and self.infobar.showDefaultEPG()

	def showEventInfoPlugins(self):
		self.infobar and self.infobar.showEventInfoPlugins()

	def showEventGuidePlugins(self):
		self.infobar and self.infobar.showEventGuidePlugins()

	def openSingleServiceEPG(self):
		self.infobar and self.infobar.openSingleServiceEPG()

	def openMultiServiceEPG(self):
		self.infobar and self.infobar.openMultiServiceEPG()

	def showMovies(self):
		ref = self.session.nav.getCurrentlyPlayingServiceOrGroup()
		self.playingservice = ref # movie list may change the currently playing
		self.session.openWithCallback(self.movieSelected, Screens.MovieSelection.MovieSelection, ref)

	def movieSelected(self, service):
		if service is not None:
			self.cur_service = service
			self.is_closing = False
			self.session.nav.playService(service)
			self.returning = False
		elif self.returning:
			self.close()
		else:
			self.is_closing = False
			ref = self.playingservice
			del self.playingservice
			# no selection? Continue where we left off
			if ref and not self.session.nav.getCurrentlyPlayingServiceOrGroup():
				self.session.nav.playService(ref)

	def getPlaylistServiceInfo(self, service):
		from MovieSelection import playlist
		for i, item in enumerate(playlist):
			if item == service:
				if config.usage.on_movie_eof.value == "repeatcurrent":
					return (i+1, len(playlist))
				i += 1
				if i < len(playlist):
					return (playlist[i], i+1, len(playlist))
				elif config.usage.on_movie_eof.value == "loop":
					return (playlist[0], 1, len(playlist))
		return ( None, 0, 0 )

	def displayPlayedName(self, ref, index, n):
		from Tools import Notifications
		Notifications.AddPopup(text = _("%s/%s: %s") % (index, n, self.ref2HumanName(ref)), type = MessageBox.TYPE_INFO, timeout = 5)

	def ref2HumanName(self, ref):
		return enigma.eServiceCenter.getInstance().info(ref).getName(ref)
	def sleepTimer(self):
		from Screens.SleepTimerEdit import SleepTimerEdit
		self.session.open(SleepTimerEdit)
