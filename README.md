# Voice Quality Collector daemon

VQ Collector is simple pure Python daemon that receives SIP Voice Quality reports sent by VoIP devices.
This collector uses the PUBLISH method defined by [sec. 3.2 of RFC 6035](http://tools.ietf.org/html/rfc6035#section-3.2)

## Behavior:
VQ-Collector daemon handles SIP PUBLISH requests containing a body and declaring an *application/vq-rtcpxr* Content-Type.
The PUBLISH body is logged on a local file or trough a remote syslog server

## Supported enviroments:
VQ-Collector is tested on Debian GNU/Linux and OSX 10.7

## Installation:
* you need to configure the installation destination editing the *CONFIG* file
* **DESTDIR** defines the installation directory
* **PYTHON_LIB** defines the directory where all needed python modules will be installed
* **INITDIR** defines the directory where the init script will be placed
* **TARGET** defines the distributrion where the daemon is installed, supported values: *rh* and *deb*, this affects the init script

After editing the CONFIG file you must run **make vq-collector**
Now you're ready to configure the collector

## Configuration:
The configuration file contains some directives under the **[main]** section:

* **local_ip**: this parameter defines where the damon must bind, here you can insert a local IP address, a network interface name or *default*, using *default* the daemon will use the default ip address
* **pid_file**: where the PID will be stored
* **port**: local UDP port to use
* **log_file**: here you can insert a file path or a syslog definition following this syntax: *syslog:IP_ADDRESS:PORT:FACILITY* 
   
   Eg.: *syslog:172.16.18.99:514:local7* will send all messages to the remote syslog on 172.16.18.99, using the 514 UDP port and the local7 facility.
* **reply_to_socket**: setting this paramether to True all PUBLISH reply will be sent to the remote IP/port, otherwise IP and port will be extracted from the PUBLISH *Contact* header 
* **debug**: here you can insert *True* or *False*, use *True* only during debug purpose
* **daemon**: another boolean value, using *False* the program will start in foreground

## Usage:
You can run the collector in this way:
 
    ./vq-collector -s /etc/vq-collector.conf
    
Or using the init scritp

    /etc/init.d/vq-collector start

**NOTE:** the init script is very simple and need some adjustements in order to run in your distribution.

# VQ-Session report syntax:

Reports syntax is defined by [RFC3611](http://tools.ietf.org/html/rfc3611)
