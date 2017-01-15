# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# streamondemand 5
# Copyright 2015 tvalacarta@gmail.com
# http://www.mimediacenter.info/foro/viewforum.php?f=36
#
# Distributed under the terms of GNU General Public License v3 (GPLv3)
# http://www.gnu.org/licenses/gpl-3.0.html
# ------------------------------------------------------------
# This file is part of streamondemand 5.
#
# streamondemand 5 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# streamondemand 5 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with streamondemand 5.  If not, see <http://www.gnu.org/licenses/>.
# --------------------------------------------------------------------------------
# Updater process
# --------------------------------------------------------------------------------

import os
import re
import sys
import time

import config
import logger
import scrapertools

ROOT_DIR = config.get_runtime_path()

REMOTE_VERSION_FILE = "https://raw.githubusercontent.com/streamondemand/plugin.video.streamondemand/master/version.xml"
REMOTE_FILE = "https://github.com/streamondemand/plugin.video.streamondemand/archive/master.zip"

LOCAL_FILE = os.path.join(ROOT_DIR, config.PLUGIN_NAME + "-")

# DESTINATION_FOLDER sera siempre el lugar donde este la carpeta del plugin,
# No hace falta "xbmc.translatePath", get_runtime_path() ya tiene que devolver la ruta correcta
DESTINATION_FOLDER = os.path.join(ROOT_DIR, "..")



def get_current_plugin_version():
    return int(config.get_setting("plugin_version_number"))
    
def get_current_channels_version():
    return int(config.get_setting("channels_version_number"))
    
def get_current_servers_version():
    return int(config.get_setting("servers_version_number"))
    
def set_current_plugin_version(new_version):
    return int(config.set_setting("plugin_version_number",str(new_version)))
    
def set_current_channels_version(new_version):
    return int(config.set_setting("channels_version_number",str(new_version)))
    
def set_current_servers_version(new_version):
    return int(config.set_setting("servers_version_number",str(new_version)))
    
def checkforupdates():
    logger.info("pelisalacarta.core.updater checkforupdates")

    # Valores por defecto
    numero_version_publicada = 0
    tag_version_publicada = ""

    # Lee la versión remota
    logger.info("streamondemand.core.updater Verificando actualizaciones...")
    logger.info("streamondemand.core.updater Version remota: " + REMOTE_VERSION_FILE)
    data = scrapertools.cachePage(REMOTE_VERSION_FILE)

    numero_version_publicada = scrapertools.find_single_match(data, "<version>([^<]+)</version>").strip()
    tag_version_publicada = scrapertools.find_single_match(data, "<tag>([^<]+)</tag>").strip()
    logger.info("streamondemand.core.updater version remota=" + tag_version_publicada + " " + numero_version_publicada)

    try:
        numero_version_publicada = int(numero_version_publicada)
    except:
        import traceback
        logger.info(traceback.format_exc())

    # Lee la versión local
    numero_version_local = get_current_plugin_version()
    logger.info("streamondemand.core.updater checkforupdates version local="+str(numero_version_local))

    hayqueactualizar = numero_version_publicada > numero_version_local
    logger.info("streamondemand.core.updater checkforupdates -> hayqueactualizar="+repr(hayqueactualizar))

    # Si hay actualización disponible, devuelve la Nueva versión para que cada plataforma se encargue de mostrar los avisos
    if hayqueactualizar:
        return tag_version_publicada
    else:
        return None

def update(item):
    logger.info("streamondemand.core.updater update")

    remotefilename = REMOTE_FILE
    localfilename = LOCAL_FILE + item.version + ".zip"

    download_and_install(remotefilename,localfilename)

    set_current_plugin_version(item.version)

def download_and_install(remote_file_name,local_file_name):
    logger.info("streamondemand.core.updater download_and_install from "+remote_file_name+" to "+local_file_name)

    if os.path.exists(local_file_name):
        os.remove(local_file_name)

    # Descarga el fichero
    inicio = time.clock()
    from core import downloadtools
    downloadtools.downloadfile(remote_file_name, local_file_name, continuar=False)
    fin = time.clock()
    logger.info("streamondemand.core.updater Descargado en %d segundos " % (fin-inicio+1))
    
    logger.info("streamondemand.core.updater descomprime fichero...")
    import ziptools
    unzipper = ziptools.ziptools()

    # Lo descomprime en "addons" (un nivel por encima del plugin)
    installation_target = os.path.join(config.get_runtime_path(),"..")
    logger.info("streamondemand.core.updater installation_target=%s" % installation_target)

    unzipper.extract(local_file_name,installation_target)
    
    # Borra el zip descargado
    logger.info("streamondemand.core.updater borra fichero...")
    os.remove(local_file_name)
    logger.info("streamondemand.core.updater ...fichero borrado")

def update_channel(channel_name):
    logger.info("streamondemand.core.updater update_channel "+channel_name)
    
    import channeltools
    remote_channel_url , remote_version_url = channeltools.get_channel_remote_url(channel_name)
    local_channel_path , local_version_path , local_compiled_path = channeltools.get_channel_local_path(channel_name)
    
    # Version remota
    try:
        data = scrapertools.cachePage( remote_version_url )
        logger.info("streamondemand.core.updater update_channel remote_data="+data)
        remote_version = int( scrapertools.find_single_match(data,'<version>([^<]+)</version>') )
    except:
        remote_version = 0

    logger.info("streamondemand.core.updater update_channel remote_version=%d" % remote_version)

    # Version local
    if os.path.exists( local_version_path ):
        infile = open( local_version_path )
        data = infile.read()
        infile.close();
        #logger.info("streamondemand.core.updater local_data="+data)

        local_version = int( scrapertools.find_single_match(data,'<version>([^<]+)</version>') )
    else:
        local_version = 0

    logger.info("streamondemand.core.updater local_version=%d" % local_version)

    # Comprueba si ha cambiado
    updated = remote_version > local_version

    if updated:
        logger.info("streamondemand.core.updater update_channel downloading...")
        download_channel(channel_name)

    return updated

def download_channel(channel_name):
    logger.info("streamondemand.core.updater download_channel "+channel_name)

    import channeltools
    remote_channel_url , remote_version_url = channeltools.get_channel_remote_url(channel_name)
    local_channel_path , local_version_path , local_compiled_path = channeltools.get_channel_local_path(channel_name)

    # Descarga el canal
    try:
        updated_channel_data = scrapertools.cachePage( remote_channel_url )
        outfile = open(local_channel_path,"wb")
        outfile.write(updated_channel_data)
        outfile.flush()
        outfile.close()
        logger.info("streamondemand.core.updater Grabado a " + local_channel_path)
    except:
        import traceback
        logger.info(traceback.format_exc())

    # Descarga la version (puede no estar)
    try:
        updated_version_data = scrapertools.cachePage( remote_version_url )
        outfile = open(local_version_path,"w")
        outfile.write(updated_version_data)
        outfile.flush()
        outfile.close()
        logger.info("streamondemand.core.updater Grabado a " + local_version_path)
    except:
        import traceback
        logger.info(traceback.format_exc())

    if os.path.exists(local_compiled_path):
        os.remove(local_compiled_path)


def get_server_remote_url(server_name):
    _remote_server_url_ = "https://raw.githubusercontent.com/streamondemand/plugin.video.streamondemand/master/servers/"

    remote_server_url = _remote_server_url_ + server_name + ".py"
    remote_version_url = _remote_server_url_ + server_name + ".xml"

    logger.info("streamondemand.core.updater remote_server_url=" + remote_server_url)
    logger.info("streamondemand.core.updater remote_version_url=" + remote_version_url)

    return remote_server_url, remote_version_url


def get_server_local_path(server_name):
    local_server_path = os.path.join(config.get_runtime_path(), 'servers', server_name + ".py")
    local_version_path = os.path.join(config.get_runtime_path(), 'servers', server_name + ".xml")
    local_compiled_path = os.path.join(config.get_runtime_path(), 'servers', server_name + ".pyo")

    logger.info("streamondemand.core.updater local_servers_path=" + local_server_path)
    logger.info("streamondemand.core.updater local_version_path=" + local_version_path)
    logger.info("streamondemand.core.updater local_compiled_path=" + local_compiled_path)

    return local_server_path, local_version_path, local_compiled_path


def updateserver(server_name):
    logger.info("streamondemand.core.updater updateserver('" + server_name + "')")

    # Canal remoto
    remote_server_url, remote_version_url = get_server_remote_url(server_name)

    # Canal local
    local_server_path, local_version_path, local_compiled_path = get_server_local_path(server_name)

    # if not os.path.exists(local_server_path):
    #    return False;

    # Version remota
    try:
        data = scrapertools.cachePage(remote_version_url)
        logger.info("streamondemand.core.updater remote_data=" + data)

        if "<tag>" in data:
            patronvideos = '<tag>([^<]+)</tag>'
        elif "<version>" in data:
            patronvideos = '<version>([^<]+)</version>'

        matches = re.compile(patronvideos, re.DOTALL).findall(data)
        remote_version = int(matches[0])
    except:
        remote_version = 0

    logger.info("streamondemand.core.updater remote_version=%d" % remote_version)

    # Version local
    if os.path.exists(local_version_path):
        infile = open(local_version_path)
        data = infile.read()
        infile.close()
        logger.info("streamondemand.core.updater local_data=" + data)

        if "<tag>" in data:
            patronvideos = '<tag>([^<]+)</tag>'
        elif "<version>" in data:
            patronvideos = '<version>([^<]+)</version>'

        matches = re.compile(patronvideos, re.DOTALL).findall(data)

        local_version = int(matches[0])
    else:
        local_version = 0
    logger.info("streamondemand.core.updater local_version=%d" % local_version)

    # Comprueba si ha cambiado
    updated = remote_version > local_version

    if updated:
        logger.info("streamondemand.core.updater updated")
        download_server(server_name)

    return updated


def download_server(server_name):
    logger.info("streamondemand.core.updater download_server('" + server_name + "')")
    # Canal remoto
    remote_server_url, remote_version_url = get_server_remote_url(server_name)

    # Canal local
    local_server_path, local_version_path, local_compiled_path = get_server_local_path(server_name)

    # Descarga el canal
    updated_server_data = scrapertools.cachePage(remote_server_url)
    try:
        outfile = open(local_server_path, "wb")
        outfile.write(updated_server_data)
        outfile.flush()
        outfile.close()
        logger.info("streamondemand.core.updater Grabado a " + local_server_path)
    except:
        logger.info("streamondemand.core.updater Error al grabar " + local_server_path)
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)

    # Descarga la version (puede no estar)
    try:
        updated_version_data = scrapertools.cachePage(remote_version_url)
        outfile = open(local_version_path, "w")
        outfile.write(updated_version_data)
        outfile.flush()
        outfile.close()
        logger.info("streamondemand.core.updater Grabado a " + local_version_path)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)

    if os.path.exists(local_compiled_path):
        os.remove(local_compiled_path)

