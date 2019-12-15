# Deployment

npm run build
scp -r build/* pi@192.168.178.35:/home/pi/ssh_transfer

## on pi
sudo cp -r ssh_transfer/* /var/www/alexa.pi.lan/app