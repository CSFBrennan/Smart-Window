#Credit to danking6 for the original files. https://github.com/danking6/smart-led-window
#download files from github https://github.com/CSFBrennan/Smart-Window
#Place the html directory in /var/www/ 
#Place window.py in /home/pi/
#install these functionalities on the pi by running these commands in the terminal.
#install PHP & Lighttpd
sudo apt-get install lighttpd php php-common php-cgi
sudo chown -R www-data:www-data /var/www
sudo chmod -R 775 /var/www
sudo usermod -a -G www-data pi

#enable PHP

sudo lighty-enable-mod fastcgi-php

#restart Server

sudo /etc/init.d/lighttpd force-reload

#Open/Edit Cronjobs
sudo crontab -e

# add the following, be mindful of spaces.

# Auto adjust the window brightness
*/10 * * * * /home/pi/window.py

# Start Pi GPIO Daemon on reboot
@reboot /usr/bin/pigpiod

#GUI should be accessible by typing http://(#your Pi's IP Address#)
