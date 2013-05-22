# -*- coding: UTF-8 -*-
## History-Zapper from Donumadeus.
## I copied a lot code from 'Zap-History Browser' plugin by AliAbdul
from Components.ActionMap import ActionMap
from Components.config import config, ConfigInteger, ConfigSelection, \
		ConfigYesNo, ConfigSet, ConfigSubsection, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Language import language
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText
from enigma import eListboxPythonMultiContent, eServiceCenter, \
		eServiceReference, gFont
from Plugins.Plugin import PluginDescriptor
from Screens.ChannelSelection import ChannelSelection
#from Screens.ParentalControlSetup import ProtectedScreen
from Screens.Screen import Screen
from Tools.Directories import resolveFilename, SCOPE_LANGUAGE, SCOPE_PLUGINS
from enigma import eServiceReference
import os, gettext

################################################

def localeInit():
	lang = language.getLanguage()
	os.environ["LANGUAGE"] = lang[:2]  # Enigma doesn't set this (or LC_ALL, LC_MESSAGES, LANG). gettext needs it!
	gettext.bindtextdomain("HistoryZapper", resolveFilename(SCOPE_PLUGINS, "Extensions/HistoryZapper/locale"))
	

def _(txt):
	t = gettext.dgettext("HistoryZapper", txt)
	if t == txt:
		print "[HistoryZapper] fallback to default translation for: ", txt
		t = gettext.gettext(txt)
	return t

localeInit()
language.addCallback(localeInit)

################################################

local_history_tv = []
local_history_radio = []

################################################
# Define configurations for this plugin.
################################################

config.plugins.HistoryZapperConf = ConfigSubsection()
config.plugins.HistoryZapperConf.enable_zap_history = ConfigSelection(choices = {"off": _("disabled"), "on": _("enabled")}, default="on")
config.plugins.HistoryZapperConf.maxEntries_zap_history = ConfigInteger(default=12, limits=(1, 60))
config.plugins.HistoryZapperConf.dont_override_skin_font = ConfigYesNo(default=False)

################################################

"""
	Add the current selected Channel to history. But only if
	feature is enabled.
	Parameter 'originalChannelSelection' is of type 
		'Screens.ChannelSelection.ChannelSelection'
"""
def addToHistory(originalChannelSelection, ref):
	#print "\n[HistoryZapper] --- addToHistory ---\n"
	#print "[HistoryZapper]   originalChannelSelection: "+str(originalChannelSelection)+"\n"
	#print "[HistoryZapper]   ref: "+str(ref)+"\n"
	#print "[HistoryZapper]   ref: "+str(eServiceCenter.getInstance().info(ref).getName(ref))+"\n"
	
	# if feature is not activated - stop function
	if config.plugins.HistoryZapperConf.enable_zap_history.value == "off":
		return
		
		
	if ref is not None:
		print "[HistoryZapper] --- add to history: %s\n" %(eServiceCenter.getInstance().info(ref).getName(ref))
	
	if originalChannelSelection.servicePath is not None:
		tmp = originalChannelSelection.servicePath[:]
		#print "[HistoryZapper]  add ref: "+repr(ref)+"\n"
		tmp.append(ref)
		try: del originalChannelSelection.history[originalChannelSelection.history_pos+1:]
		except Exception, e: pass
		
		#print "[HistoryZapper] check if tmp is in history\n"
		#print "[HistoryZapper]  tmp: "+str(tmp)+"\n"
		#print "[HistoryZapper]  history: "+str(originalChannelSelection.history)+"\n"
		if tmp in originalChannelSelection.history:
			print "[HistoryZapper] found already in history!"
			originalChannelSelection.history.remove(tmp)
		
		#print "[HistoryZapper]  history (after remove): "+str(originalChannelSelection.history)+"\n"
		originalChannelSelection.history.append(tmp)
		
		#print "[HistoryZapper]  history (after append): "+str(originalChannelSelection.history)+"\n"
		hlen = len(originalChannelSelection.history)
		#print "[HistoryZapper]   length of history after append: "+str(hlen)+"\n"
		if hlen > config.plugins.HistoryZapperConf.maxEntries_zap_history.value:
			del originalChannelSelection.history[0]
			hlen -= 1
		originalChannelSelection.history_pos = hlen-1
		

ChannelSelection.addToHistory = addToHistory


################################################

class HistoryZapperConfigurator(ConfigListScreen, Screen):
	skin = """
		<screen position="center,center" size="420,80" title="%s" >
			<widget name="config" position="0,0" size="420,80" scrollbarMode="showOnDemand" />
		</screen>""" % _("HistoryZapperConfiguratorTitle")

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		
		ConfigListScreen.__init__(self, [
			getConfigListEntry(_("ConfEnableZapHistory:"), config.plugins.HistoryZapperConf.enable_zap_history),
			getConfigListEntry(_("ConfMaximumZapHistoryEntries:"), config.plugins.HistoryZapperConf.maxEntries_zap_history),
			getConfigListEntry(_("ConfDontOverrideSkinFont"), config.plugins.HistoryZapperConf.dont_override_skin_font)])
			
		
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.save, "cancel": self.exit}, -2)

	"""
		Save configuration and close config screen.
	"""
	def save(self):
		
		for x in self["config"].list:
			x[1].save()
		self.close()

	def exit(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()

################################################

class ZapHistoryList(MenuList):
	def __init__(self, list, enableWrapAround=False):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.l.setItemHeight(40)
		self.l.setFont(0, gFont("Regular", 18))
		self.l.setFont(1, gFont("Regular", 14))

def ZapHistoryListEntry(serviceName, eventName):
	res = [serviceName]
	if config.plugins.HistoryZapperConf.dont_override_skin_font:
		res.append(MultiContentEntryText(pos=(2, 0), size=(400-2, 20), font=0, text=serviceName))
		res.append(MultiContentEntryText(pos=(2, 22), size=(400-2, 16), font=1, text=eventName))
	else:
		res.append(MultiContentEntryText(pos=(2, 0), size=(400-2, 20), font=0, text=serviceName))
		res.append(MultiContentEntryText(pos=(2, 22), size=(400-2, 16), font=1, text=eventName, color=0x00AAAAAA, color_sel=0x00CCCCCC))
		
	return res

################################################

class HistoryZapper(Screen):
	skin = """
	<screen size="400,240" title="%s" flags="wfNoBorder">
		
		<widget name="list" position="0,0" size="400,200" scrollbarMode="showOnDemand" />
		
		<ePixmap pixmap="skin_default/buttons/red.png" position="0,207" size="90,28" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="90,207" size="90,28" transparent="1" alphatest="on" />
		<widget name="key_red" position="0,207" zPosition="1" size="90,28" font="Regular;12" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
		<widget name="key_blue" position="90,207" zPosition="1" size="90,28" font="Regular;12" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
	</screen>""" % _("HistoryZapperTitle")

	## plugin start
	def __init__(self, session, servicelist):
		Screen.__init__(self, session)
		self.session = session
		
		self.serviceHandler = eServiceCenter.getInstance()
		from Screens.InfoBar import InfoBar
		try:
			#self.servicelist = InfoBar.instance.servicelist
			self.servicelist = servicelist
		except AttributeError, e:
			print "[HistoryZapper]  ####################    error   ############\n"
			pass

				
		self["list"] = ZapHistoryList([])
		self["key_red"] = Label(_("Clear"))
		self["key_blue"] = Label(_("Config"))

		
		## remote-key : method-ref
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"ok": self.zapAndClose,
				"cancel": self.close,
				"red": self.clear,
				"blue": self.config
			}, prio=-1)
			
		
		
		self.onLayoutFinish.append(self.buildList)

	"""
		Override the method of 'Screen' to move the 
		history selection screen to the upper right corner.
	"""
	def applySkin(self):
		
		posX = 0
		posY = 0
		width = 400;
		height = 240;
				
		dsize = self.desktop.size()

		if self.desktop is not None:
			offset = 50
			posX = dsize.width() - (width+offset)
			posY = 15
		
		self.skinAttributes.append(("position", "%s,%s"%(posX, posY)))
		
		Screen.applySkin(self)
		
		
	"""
		Build the list of the last watched channels
		and put the result to the UI widget named 'list'
		in history selection screen.
	"""
	def buildList(self):
		curChannel = self.session.nav.getCurrentlyPlayingServiceReference()
		#print "[HistoryZapper] service-list:"+str(self.servicelist)+"\n"
		
		#print "[HistoryZapper] currently watching: "+str(self.serviceHandler.info(curChannel).getName(curChannel))+"\n"
		
		#print "[HistoryZapper] len of history: "+str(len(self.servicelist.history))+"\n"
		#print "[HistoryZapper] history:"+str(self.servicelist.history)+"\n"
		
		
		
		list = [] # list containing the ZapHistoryListEntries
		
		for x in self.servicelist.history:
			if len(x) == 2: # Single-Bouquet
				ref = x[1]
			else: # Multi-Bouquet
				ref = x[2]
			#print "[HistoryZapper]  ##- service-ref: "+str(ref)+"\n"
			#print "[HistoryZapper]  ##- channel-cur: "+str(curChannel)+"\n"
			
			sameCh = bool(ref == curChannel)
			#print "same: "+str(sameCh)+"\n"
			
			if sameCh:
				continue
			
			info = self.serviceHandler.info(ref)
			#print "[HistoryZapper]  ##- info of this service: "+str(info)+"\n"
			if info:
				name = info.getName(ref).replace('\xc2\x86', '').replace('\xc2\x87', '')
				event = info.getEvent(ref)
				if event is not None:
					eventName = event.getEventName()
					if eventName is None:
						eventName = ""
				else:
					eventName = ""
			else:
				name = "N/A"
				eventName = ""
			list.append(ZapHistoryListEntry(name, eventName))
		
		# removes the last entry since this is the currently watched channel
		#lastChannel = list.pop()
		#print "popped this channel: "+str(lastChannel)+"\n"
		list.reverse()
		print "[HistoryZapper]  set list into UI: "+str(list)+"\n"
		self["list"].setList(list)

	
	"""
		Zap to the channel that is currently selected in
		history selection screen.
	"""
	def zap(self):
		length = len(self.servicelist.history)
		
		# at least two history entries must exist to be able to zap
		if length > 1:
			length-= 1 # remove one, since the currently watched channel does not count
			#print "[HistoryZapper]  try to zap, history count: "+str(length)+", selected index: "+str(self["list"].getSelectionIndex())+"\n"
			#print "[HistoryZapper]  root: "+str(self.servicelist.getRoot())+"\n"
			#print "  current selection is: "+str(self.servicelist.getCurrentSelection())+"\n"
		
			newHistIdx = (length - self["list"].getSelectionIndex()) - 1
			#print "[HistoryZapper]  new hist-idx: "+str(newHistIdx)+"\n"
			#self.servicelist.history_pos = (length - self["list"].getSelectionIndex()) - 1
			#print "[HistoryZapper]  new hist-pos: "+str(self.servicelist.history_pos)+"\n"
			#self.servicelist.setHistoryPath()
			
			zapToChannel = self.servicelist.history[newHistIdx]
			lastRefIdx = len(zapToChannel)-1
			#print "[HistoryZapper]  count of zapToChannel: "+str(len(zapToChannel))+"\n"
			#print "[HistoryZapper]  - so last index is: "+str(len(zapToChannel)-1)+"\n"
			zapToChannelRef = zapToChannel[lastRefIdx]
			print "[HistoryZapper]  planned channel to zap: "+str(zapToChannelRef)+"\n"
			
			self.servicelist.setCurrentSelection(zapToChannelRef)
			self.servicelist.zap()
			

	"""
		Delete the recorded history and clean the
		list widget of history selection screen.
	"""
	def clear(self):
		for i in range(0, len(self.servicelist.history)):
			del self.servicelist.history[0]
		self.buildList()
		self.servicelist.history_pos = 0
		

	"""
		Zap to the channel which is currently selected
		in history selection screen and close the screen.
	"""
	def zapAndClose(self):
		self.zap()
		self.close()

	"""
		Open the configuration screen.
	"""
	def config(self):
		self.session.open(HistoryZapperConfigurator)

	
################################################

"""
	kwargs has argument 'servicelist' of type 
	'Screens.ChannelSelection.ChannelSelection'
"""
def openZapUI(session, servicelist, **kwargs):
	print "[HistoryZapper] ----- main!!!"
	session.open(HistoryZapper, servicelist)
	
def openConfig(session, **kwargs):
	print "[HistoryZapper] open-config"
	session.open(HistoryZapperConfigurator)

"""
	Definition of the Plugin.
"""
def Plugins(**kwargs):
	return [PluginDescriptor(
		name=_("History-Zapper-Conf"), 
		description = _("HistoryZapperDescription"),
		where=PluginDescriptor.WHERE_PLUGINMENU, 
		fnc=openConfig,
		icon="history-zapper.png"),
		
		PluginDescriptor(
		name=_("History-Zapper"), 
		description = _("HistoryZapperDescription"),
		where=PluginDescriptor.WHERE_EXTENSIONSMENU, 
		fnc=openZapUI,
		icon="history-zapper.png")
		]
