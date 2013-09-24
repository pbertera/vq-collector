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

After editing the CONFIG file you must run **make vq-collector**
Now you're ready to configure the collector

## Configuration:
The configuration file contains some directives under the **[main]** section:

* **local_ip**: this parameter defines where the damon must bind, here you can insert a local IP address, a network interface name or *default*, using *default* the daemon will use the default ip address
* **pid_file**: where the PID will be stored
* **port**: local UDP port to use
* **log_file**: here you can insert a file path or a syslog definition following this syntax: *syslog:IP_ADDRESS:PORT:FACILITY* 
   
   Eg.: *syslog:172.16.18.99:514:local7* will send all messages to the remote syslog on 172.16.18.99, using the 514 UDP port and the local7 facility.
* **debug**: here you can insert *True* or *False*, use *True* only during debug purpose
* **daemon**: another boolean value, using *False* the program will start in foreground

## Usage:
You can run the collector in this way:
 
    ./vq-collector -s /etc/vq-collector.conf
    
Or using the init scritp

    /etc/init.d/vq-collector start

**NOTE:** the init script is very simple and need some adjustements in order to run in your distribution.

# VQ-Session report syntax:

    VQSessionReport: CallTerm
    CallID:b4d42387@pbx
    LocalID:"John Doe" <sip:102@pbx.example.com>
    RemoteID:"Anonymous" <sip:anonymous@pbx.example.com;user=phone>
    OrigID:"Anonymous" <sip:anonymous@pbx.example.com;user=phone>
    LocalAddr:IP=172.16.18.187 PORT=60696 SSRC=0x2769A169
    RemoteAddr:IP=81.29.211.196 PORT=50086 SSRC=0x87F33D64
    DialogID:b4d42387@pbx;to-tag=1094356377;from-tag=ugyisema34
    x-UserAgent:snom710/8.7.3.201309022318
    LocalMetrics:
    Timestamps:START=2000-01-04T08:12:27Z STOP=2000-01-04T08:12:48Z
    SessionDesc:PT=0 PD=PCMU SR=8000 PPS=50 SSUP=off
    x-SIPterm:SDC=OK SDT=21 SDR=AN
    JitterBuffer:JBA=3 JBR=2 JBN=39 JBM=40 JBX=240
    PacketLoss:NLR=0.0 JDR=0.0
    BurstGapLoss:BLD=0.0 BD=0 GLD=0.0 GD=20440 GMIN=16
    Delay:RTD=34 ESD=0 IAJ=1
    QualityEst:MOSLQ=4.1 MOSCQ=3.9
    RemoteMetrics:
    JitterBuffer:JBA=0 JBR=0 JBN=0 JBM=0 JBX=0
    PacketLoss:NLR=0.0 JDR=0.0
    BurstGapLoss:BLD=0.0 BD=0 GLD=0.0 GD=18458 GMIN=16
    Delay:RTD=34 ESD=0 IAJ=0
    QualityEst:MOSLQ=4.1 MOSCQ=4.1

* VQSessionReport: **CallTerm** means that this report is henerated at the end of the call, in the VQSessionReport section you can find all information useful to identify local and remote peers.

* JitterBuffer:
  * JBA (JitterBufferAdaptive)
  
        JitterBufferAdaptive indicates whether the jitter buffer in
        the endpoint is adaptive, static, or unknown.
        The values follow the same numbering convention as RFC 3611 [4].
        For more details, please refer to that document.
        0 - unknown
        1 - reserved
        2 - non-adaptive
        3 - adaptive
  
  * JBR (JitterBufferRate), this parameter is defined by [RFC3611, sec.4.7.7](http://tools.ietf.org/html/rfc3611#section-4.7.7):
        
        jitter buffer rate (JB rate): 4 bits
        J = adjustment rate (0-15).  This represents the implementation 
        specific adjustment rate of a jitter buffer in adaptive mode.
        This parameter is defined in terms of the approximate time
        taken to fully adjust to a step change in peak to peak jitter
        from 30 ms to 100 ms such that:
        adjustment time = 2 * J * frame size (ms)
        
  * JBN (JitterBufferNominal delay):
       
        jitter buffer nominal delay (JB nominal): 16 bits
        This is the current nominal jitter buffer delay in
        milliseconds, which corresponds to the nominal jitter buffer
        delay for packets that arrive exactly on time.  
  
  * JBM (JitterBufferMaximum delay):
  
        jitter buffer maximum delay (JB maximum): 16 bits
        This is the current maximum jitter buffer delay in milliseconds
        which corresponds to the earliest arriving packet that would
        not be discarded.  In simple queue implementations this may
        correspond to the nominal size.  In adaptive jitter buffer
        implementations, this value may dynamically vary up to JB abs
        max (see below).
        
  * JBX (JitterBufferAbsMax delay):
  
        jitter buffer absolute maximum delay (JB abs max): 16 bits
        This is the absolute maximum delay in milliseconds that the
        adaptive jitter buffer can reach under worst case conditions.
        If this value exceeds 65535 milliseconds, then this field SHALL
        convey the value 65535.
  
* PacketLoss:
  
  * NLR (NetworkPacketLossRate):
         
        The fraction of RTP data packets from the source lost since the
        beginning of reception, expressed as a fixed point number with
        the binary point at the left edge of the field.  This value is
        calculated by dividing the total number of packets lost (after
        the effects of applying any error protection such as FEC) by
        the total number of packets expected, multiplying the result of
        the division by 256, limiting the maximum value to 255 (to
        avoid overflow), and taking the integer part.  The numbers of
        duplicated packets and discarded packets do not enter into this
        calculation.  Since receivers cannot be required to maintain
        unlimited buffers, a receiver MAY categorize late-arriving
        packets as lost.  The degree of lateness that triggers a loss
        SHOULD be significantly greater than that which triggers a
        discard.
        
   * JDR (JitterBufferDiscardRate):
       
        The fraction of RTP data packets from the source that have been
        discarded since the beginning of reception, due to late or
        early arrival, under-run or overflow at the receiving jitter
        buffer.  This value is expressed as a fixed point number with
        the binary point at the left edge of the field.  It is
        calculated by dividing the total number of packets discarded
        (excluding duplicate packet discards) by the total number of
        packets expected, multiplying the result of the division by
        256, limiting the maximum value to 255 (to avoid overflow), and
        taking the integer part.
        
* BurstGapLoss