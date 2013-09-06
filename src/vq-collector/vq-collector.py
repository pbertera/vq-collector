#!/usr/bin/python
# vi:si:et:sw=4:sts=4:ts=4
# -*- coding: UTF-8 -*-
# -*- Mode: Python -*-

import socket
import struct
import re
import sys
import select
import ConfigParser
import os
import signal
import cStringIO
from string import Template

from siplib import sip
from siplib import daemon

version = "__VERSION__"
logger = daemon.Logger(sys.argv[0])


class SocketOptionError(Exception):
    pass


class CreateSocketError(Exception):
    pass


class BindSocketError(Exception):
    pass


class SendDataError(Exception):
    pass


class CollectorServer:

    def __init__(self, local_ip, port=5060):
        self.port = port
        self.local_ip = local_ip
        self.listen_addr = local_ip

        logger.debugMessage("Local IP: %s" % self.local_ip)
        logger.debugMessage("Listen IP: %s" % self.listen_addr)

        self.recvsocket = self._create_socket()

    def listen(self):
        # Sockets from which we expect to read
        inputs = [self.recvsocket]
        # Sockets to which we expect to write
        outputs = []

        logger.debugMessage("Starting listening loop")

        while inputs:
            readable, writable, exceptional = select.select(inputs, outputs,
                                                            inputs)
            # Handle inputs
            for s in readable:
                if s is self.recvsocket:
                    if not self.handle_request():
                        continue

    def handle_request(self):
        data, remote = self.recvsocket.recvfrom(10240)
        try:
            request = sip.Request(data)
        except sip.SipUnpackError:
            return False

        logger.debugMessage("Received request from %s:%d : \n%s" %
                            (remote[0], remote[1], str(request)))
        response = sip.Response()
        # logging the body
        logger.infoMessage(request.body.split())
        if request.method != "PUBLISH":
            logger.debugMessage("Received a non PUBLISH: %s" %
                                request.method)
            response.reason = "Not implemented"
            response.status = "501"
        else:
            try:
                if request.headers["content-type"] != "application/vq-rtcpxr":
                    logger.debugMessage("No VQ RTCP-XR body detected")
                    response.reason = "Not implementented"
                    response.status = "501"

            except KeyError:
                logger.debugMessage("No VQ RTCP-XR body detected")
                response.reason = "Not implementented"
                response.status = "501"

        response.headers['from'] = request.headers['from']
        response.headers['to'] = request.headers['to']
        response.headers['call-id'] = request.headers['call-id']
        response.headers['cseq'] = request.headers['cseq']
        response.headers['expires'] = 0
        response.headers['via'] = request.headers['via']
        response.headers['contact'] = "<sip:%s:%d;transport=tcp;handler=dum>"\
                                      % (self.local_ip, self.port)
        response.headers['content-length'] = 0
        # Regexp parsing via Header: SIP/2.0/UDP 172.16.18.90:5060;rport
        p = re.compile(r'SIP/(.*)/(.*)\s(.*):([0-9]*);*')
        m = p.search(request.headers['via'])

        if m:
            version = m.group(1)
            transport = m.group(2)
            if version != "2.0":
                UnsupportedSIPVersion(
                    "Unsupported SIP version in Via header: %s" % version)
                return false

            phone_ip = m.group(3)
            phone_port = m.group(4)
        else:
            sendDataError("Wrong Via: header")
            return False
        if transport.upper() == "UDP":
            self.send_response(phone_ip, phone_port, response)
        else:
            UnsupportedSIPTransport("Unsupported Transport in Via: header")
            return False

    def send_response(self, phone_ip, phone_port, response):
        logger.debugMessage("Creating send socket")
        try:
            self.sendsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                          socket.IPPROTO_UDP)
        except Exception, e:
            CreateSocketError("Cannot create socket: %s" % e)
        try:
            self.sendsock.setsockopt(socket.SOL_SOCKET,
                                     socket.SO_REUSEADDR, 1)
            # self.sendsock.setsockopt(socket.SOL_SOCKET,
            #                         socket.SO_REUSEPORT, 1)
        except AttributeError, e:
            pass
        try:
            logger.debugMessage("Binding to local ip:port %s:%s" %
                                (self.local_ip, self.port))
            self.sendsock.bind((self.local_ip, self.port))
        except Exception, e:
            SendDataError("Cannot bind socket to %s:%d: %s"
                          % (self.local_ip, self.port, e))

        # sent the OK (or 501)
        try:
            logger.debugMessage("Sending response to %s:%s : \n%s" %
                                (phone_ip, phone_port, str(response)))
            self.sendsock.sendto(str(response), (phone_ip,
                                                 int(phone_port)))
        except Exception, e:
            SendDataError("Cannot send OK/DENY response to %s:%s: %s" %
                          (phone_ip, phone_port, e))
        self.sendsock.close()

    def _create_socket(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                 socket.IPPROTO_UDP)
            sock.setblocking(0)
        except Exception, e:
            raise CreateSocketError("Cannot create socket: %s" % e)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            pass
        try:
            sock.bind((socket.gethostbyname(self.listen_addr), self.port))
        except Exception, e:
            raise BindSocketError("Cannot bind socket to %s:%d: %s" %
                                  (self.listen_addr, self.port, e))
        return sock

if __name__ == '__main__':

    def usage():
        print "\nUsage: %s [options] <config-file>" % sys.argv[0]
        print "\n\tOptions:"
        print "\t\t-s <config-file>\t\tStart the program"
        sys.exit()

    def signal_handler(signal, frame):
        logger.infoMessage('Killed by SIGTERM. Goodbye.')
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)

    # TODO: improve command line handling
    if len(sys.argv) < 3:
        print "\nERROR: missing args."
        usage()

    if sys.argv[1] not in ["-c", "-s"]:
        print "\nERROR: wrong arg."
        usage()

    parser = daemon.SettingsParser(sys.argv[2], logger)
    config = parser.get_config()
    main_settings = parser.parse_main()

    if main_settings["debug"].upper() == 'TRUE':
        logger.set_level("debug")
        logger.debugMessage("Log level: DEBUG")
    else:
        logger.set_level("info")
        logger.debugMessage("Log level: INFO")

    local_ip = main_settings["local_ip"]

    if main_settings["conf_log_handler"]:
        logger.debugMessage("Logging to %s" % main_settings["log_file"])
        logger.change_handler(main_settings["conf_log_handler"])
    # non-common setting
    try:
        port = int(config.get('main', 'port'))
        logger.debugMessage("Listening to %d port" % int(port))
    except ConfigParser.NoOptionError:
        port = 5060

    server = CollectorServer(local_ip=local_ip, port=port)

    if sys.argv[1] == "-s":
        try:
            if config.get('main', 'daemon').upper() == 'TRUE':
                logger.infoMessage('Daemonizing')
                try:
                    pid_file = config.get('main', 'pid_file')
                    logger.infoMessage('Using pid file %s' % pid_file)
                    try:
                        pid = daemon.become_daemon(pid_file)
                    except Exception, e:
                        logger.systemError("Cannot start daemon: %s, exiting"
                                           % e)
                        sys.exit(-1)
                except ConfigParser.NoOptionError:
                    try:
                        pid = daemon.become_daemon(None)
                    except Exception, e:
                        logger.systemError("Cannot start daemon: %s, \
                                            exiting" % e)
                        sys.exit(-1)
                    logger.infoMessage("No pid file in configuration \
                                               file")
                logger.infoMessage("Daemon started with pid %d"
                                   % pid)

        except ConfigParser.NoOptionError:
            logger.infoMessage('Run in foreground')
        try:
            server.listen()
        except Exception, e:
            logger.systemError('Received fatal exception: %s' % e)
