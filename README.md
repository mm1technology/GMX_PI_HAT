# GMX_PI_HAT
The GMX PI HAT brings the GMX module interface to the Raspberry PI world, opening this platform to the GMX IoT modules world.
As you can see from the picture with this HAT your Raspberry PI can use two GMX modules.<br/>
<img src="/docs/gmx-lr1-gps.jpg"/>
The HAT simply bring the PI GPIOS over to the GMX connectors and adds a dual IC2 UART interface based on the NXPSC16752 chip.<br/>
The HAT works with the 40 Pins PI extension board - so only on the ...

## How to Configure your PI with Raspian
You need to add support for the NXPSX16752 chipset before being able to use the board. This hopefully its quite easy.<br/>
We have been testing the latest Raspian release Stretch ( as of August 2017).
<br/>
We are using the I2C version of the chip so first of all you need to enable I2C on the PI ( if you haven't yet done it)

```bash
sudo raspi-config
```
* Choose advanced options.
* Choose I2C Enable/Disable automatic loading.
* Follow the prompts to set this to load this automatically.
* Reboot the Pi.
<br/>

Then install the I2C utilities
<br/>

```bash
sudo rpi-update
sudo apt-get install -y i2c-tools
```
<br/>
and let's test if you can identify the GMX PI HAT.
<br/>

```bash
sudo i2cdetect -y 1
```
<br/>

You should see a device at address 0x4D.

<br/>
Now let's add the kernel support for the SC16IS752.<br/>
<br/>

Edit the module files
<br/>
```bash
sudo nano /etc/modules 
```
Add at the bottom the line

```bash
sc16is7xx
```

You should have something like this:
```bash
# /etc/modules: kernel modules to load at boot time.
#
# This file contains the names of kernel modules that should be loaded
# at boot time, one per line. Lines beginning with "#" are ignored.

i2c-dev
sc16is7xx
```

The we need to create the Device Tree Overlay sc16is752-i2c.dts.<br/> 
By default the SPI version is already present but not the I2C one ( thanks to [MaterWuff](https://www.raspberrypi.org/forums/viewtopic.php?f=107&t=146908&start=25) ) here are the steps.<br/>
<br/>
Create the file<br>
```bash

sudo nano sc16is752-i2c.dts
```

and copy this content:

```bash
/dts-v1/;
/plugin/;

/ {
    compatible = "brcm,bcm2835", "brcm,bcm2836", "brcm,bcm2708", "brcm,bcm2709"; // Depending on your RPi Board Chip
    
    fragment@0 {
        target = <&i2c1>;
        
        frag1: __overlay__ {
            #address-cells = <1>;
            #size-cells = <0>;
            status = "okay";

            sc16is752: sc16is752@4D {
                compatible = "nxp,sc16is752";
                reg = <0x4D>; // i2c address
                clocks = <&sc16is752_clk>;
                interrupt-parent = <&gpio>;
                interrupts = <17 0x2>; //GPIO and falling edge
                gpio-controller;
                #gpio-cells = <0>;
                i2c-max-frequency = <400000>;
      status = "okay";

                sc16is752_clk: sc16is752_clk {
                    compatible = "fixed-clock";
                    #clock-cells = <0>;
                    clock-frequency = <1843200>;
                };
            };
        };
    };

    __overrides__ {
        int_pin = <&sc16is752>,"interrupts:0";
    };
};

```
<br/>
The GMX PI HAT has i2c address at <b>0x4D</b> and interrupt pin GPIO <b>17</b>.<br/>
<br/>

Now we need to create the DTBO overlay file ( and you need kernel > 4.4 - use 'uname -r' to check).<br/>

```bash
dtc -@ -I dts –O dtb –o sc16is752-i2c.dtbo sc16is752-i2c.dts
```

and copy it to the overlay folder

```bash
sudo cp sc16is752-i2c.dtbo /boot/overlays/
```

and finally activate in the <b>/boot/config.txt</b>.<br/>
Add the line: dtoverlay=sc16is752-i2c ( usually at the bottom of the file)<br/>
Add the beginning of the config.txt file the 'debug on': dtdebug=on ( once everything works you can remove this)</br>

<br>
Reboot your PI.
<br/>


Let's check if everything works:
```bash
lsmod
```
you should see the file 'sc16is7xx'<br/>
then..<br/>
```bash
sudo vcdbg log msg
```
and you should find the "Loaded overlay 'sc16is752-i2c'" line

and finally...<br/>
```bash
ls –l /dev/ttyS*
```

And you should see the additional UART ports for the 2 GMX modules:
* /dev/ttySC0 
* /dev/ttySC1
<br/>
The HAT is configured and working!

# Testing the GMX-LR1 Module
Here is a quick example on how to make a LoRaWAN connection with a python script. Essentially to need to send AT Commands to make the connection.





