import RPi.GPIO as GPIO
import time
import serial
import re

#
#               GPIO PINOUT
#
# GMX               SLOT #0             SLOT# 1
# GMX_Reset         GPIO 5              GPIO 6
# GMX_GPIO_1        GPIO 23             GPIO 21
# GMX_GPIO_2        GPIO 24             GPIO 16
# GMX_GPIO_3        GPIO 25             GPIO 12
# GMX_GPIO_4        GPIO 18             GPIO 19
# GMX_GPIO_5        GPIO 22             GPIO 26
# GMX_GPIO_6/BOOT0  GPIO 13             GPIO 13
# GMX_I2C_SCL       SCL1 (GPIO 02)      SCL1 (GPIO 02)
# GMX_I2C_SDA       SDA1 (GPIO 03)      SDA1 (GPIO 03)
# GMX_SPI_MISO      SPI_MISO (GPIO 09)  SPI_MISO (GPIO 09)
# GMX_SPI_MOSI      SPI_MOSI (GPIO10)   SPI_MOSI (GPIO10)
# GMX_SPI_CLK       SPI_CLK (GPIO11)    SPI_CLK (GPIO11)
# GMX_SPI_CS        SPI_CE0_N (GPIO 08) SPI_CE1_N (GPIO 07)
# GMX_gmxINT        GPIO 20             GPIO 27
#
#

print "Booting GMX-NBIOT..."

#Init GPIO's
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Reset PIN for GMX Slot #1
#  - for Slor #0 pin is 5
GPIO.setup(6, GPIO.OUT)   # SLOT 1

# Cycle the Reset
GPIO.output(6,0)
time.sleep( .1 )
GPIO.output(6,1)

#wait for reboot
time.sleep(2)

# GMX STATUS Defines
GMX_OK = 0
GMX_ERROR = -1
GMX_UKNOWN_ERROR = -2

print "Ready."

# Use /dev/ttySC0 o /dev/ttySC1
port = serial.Serial("/dev/ttySC1",  baudrate=9600)  # => SLOT 2

def _sendCmd(command):
    port.reset_input_buffer()  # flush any pending data
    port.write(command)
    return

def _parseResponse():
    time.sleep(0.2)
    response = ""

    response = port.read(4)  # start reading
    response += port.read(port.in_waiting)

    matchOk = re.match(r"((.|\n)*)\r\nOK",response)

    if matchOk:
        response = matchOk.group(1)
        # not very eleganto
        matchOk2 = re.match(r"((.|\n)*)\r\n",response)
        if matchOk2:
            response = matchOk2.group(1)
        return GMX_OK,response

    matchError = re.match("((.|\n)*)\r\n(.*)ERRROR", response);
    if matchOk:
        print matchError.group()
        return GMX_ERROR,response

    return GMX_UKNOWN_ERROR,response



# Query the Module

_sendCmd("AT+CGMR=1\r\n")
status,response = _parseResponse()
print "Version:"+response

_sendCmd("AT+CGSN=1\r\n")
status,response = _parseResponse()
print "IMEI:"+response

# Setup DT
_sendCmd("AT+NCONFIG=CR_0354_0338_SCRAMBLING,TRUE\r\n")
status,response = _parseResponse()

_sendCmd("AT+NCONFIG=CR_0859_SI_AVOID,TRUE\r\n")
status,response = _parseResponse()

_sendCmd("AT+CFUN=0\r\n")
status,response = _parseResponse()

_sendCmd("AT+CGDCONT=1,\"IP\",\"internet.nbiot.telekom.de.MNC040.MCC901.GPRS\"\r");
status,response = _parseResponse()

_sendCmd("AT+CFUN=1\r")
status,response = _parseResponse()

_sendCmd("AT+NBAND=8\r")
status,response = _parseResponse()

_sendCmd("AT+COPS=1,2,\"26201\"\r")
status,response = _parseResponse()

print "\nWaiting to connect..."

# Now we try to Join
join_status = 0
join_wait = 0
while join_status == 0:

    print "Join Attempt:"+str(join_wait)
    join_wait+=1
    time.sleep(5)

    #check id Network Joined
    _sendCmd("at+cgatt?\r")
    status, response = _parseResponse()
    join_status = int(response)


# Joined - we start application

print "Connected!!!"

last_tx_time = time.time()
time_interval_tx = 20

# main loop testing
print "Starting  TX Loop - TX every "+str(time_interval_tx)+" seconds"
while True:
    delta_tx = time.time() - last_tx_time

    if ( delta_tx > time_interval_tx ):
        print "TX!"
        # TX Data

        # PUT YOUR DATA HERE
        _udp_port = "9200"
        _upd_socket_ip = "1.1.1.1"

        data_to_send = '010203'
        num_bytes = len( data_to_send ) / 2

        _sendCmd("at+nsocr=DGRAM,17," + _udp_port + "\r")
        status, response = _parseResponse()

        _sendCmd("at+nsost=0," + _upd_socket_ip + "," + _udp_port + "," + str(num_bytes) + "," + data_to_send + "\r");
        status, response = _parseResponse()

        _sendCmd("at+nsocl=0\r")
        status, response = _parseResponse()

        last_tx_time = time.time()
