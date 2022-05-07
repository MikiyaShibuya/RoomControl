# RoomControl

## Setup

**Setup ip-address notification(optoinal)**  
Setup slack webhook according to https://github.com/MikiyaShibuya/IP-PUSH  
The ip-address of rpi will be used afterward.  

**Install homebridge**  
Get GPG key and install node, npm and homebridge.  
```
curl -sSfL https://repo.homebridge.io/KEY.gpg | sudo gpg --dearmor | sudo tee /usr/share/keyrings/homebridge.gpg  > /dev/null
echo "deb [signed-by=/usr/share/keyrings/homebridge.gpg] https://repo.homebridge.io stable main" | sudo tee /etc/apt/sources.list.d/homebridge.list > /dev/null

sudo apt update
sudo apt install -y nodejs npm
sudo apt install -y homebridge
```

**Launch homebridge and test if it working**  
Enable service  
```
sudo systemctl enable homebridge
sudo systemctl start homebridge
```
then access to `<raspberry pi address>:8581`.  
after login with user: admin pass: admin, dashboard (QR code, temperature etc...) should be displayed.   

**Install cmd4 plugin**  
Search for "cmd4" in plugins tab.  
If there are multiple results, install a plugin provided by @ztalbot2000.  

**Setup**  
```
cd ~ && git clone git@github.com:MikiyaShibuya/RoomControl.git
sudo mv /var/lib/homebridge/config.json /var/lib/homebridge/config.json.org
sudo ln -sfn ~/RoomControl/config.json /var/lib/homebridge/config.json
```

**Hue bridge config**
Get access token to control lightbulbs via http request.  
1. Access to http://<raspberry pi address>/debug/clip.html
2. Put `/api` in URL, `{"devicetype": ""}` in message body
3. Push circlar button on hue bridge(physical), then push POST button on browser
4. Copy username displayed in Command Response.
5. Create hue config in repository root
```
cd ~/RoomControl
echo <username> >> hue_config.txt
echo <raspberry pi address> >> hue_config.txt
```
  
**Fix clock for IR modulation**  
sudo vim /lib/systemd/system/pigpiod.service  
add `-t 0` option to ExecStart like  
`ExecStart=/usr/bin/pigpio -l -t 0`

**Operation check**  
Reboot and check everything is working.  

**Trouble shooting**  
* hue bridge is not respond  
  Check if the lights can be turnd on/off manually.  
  `sudo /home/pi/RoomControl/hue_client.py /home/pi/RoomControl/hue_config.txt Set hoge On 0`  
  \* last 0 means off, try 1 to turn on  
  `sudo /home/pi/RoomControl/hue_client.py /home/pi/RoomControl/hue_config.txt Set hoge Brightness 30`  
  \* last 30 means % of brightness  
  If this command is not working, there is something wrong with hue_config.txt or hue bridge setting.  

* aircon is not respond  
  Check if IR LED is flashing using camera after flipping switch.

  Make sure that the CLOCK FREQ is fixed.

  Check if the aircon can be turned on/off manually.  
  `sudo /home/pi/RoomControl/aircon.py Set a Active 0`  
  \* last 0 means off, try 1 to. turn on
  
