# picamera-test

Show images over HDMI.

- `p` to take an image. Saved as img?.jpg, where ? starts at 0 and increments by one per press
- `z` to toggle between 100% crop and full screen (assuming 2560x1440 screen)
- `q` quit

For python module keyboard to work without being root:
Add user to groups tty and input.

Remove calls to ensure_root in `_nixkeyboard.py`

# web-streaming.py

Run python code on pi, go to <pi-ip-address>:8000 in a web browser. For example fyspi-elab-microscope-nikon.local:8000.

Clicking `Capture image` stores an image at maximum resolution. Images are stored to /home/pi/shared/img<num>.jpg, where <num> starts at 0. 

The camera will stop recording after 10 minutes. Refreshing the page will restart it.

# streaming-microscope.service

To autostart web streaming on start, vopy file to `/etc/systemd/system`.

    sudo systemctl enable streaming-microscope
    sudo systemctl start streaming-microscope

It is then not possible to view images over HDMI until the service is stopped

    sudo systemctl stop streaming-microscope

To enable samba sharing: `sudo apt install samba samba-common-bin`

Edit /etc/samba/smb.conf and add:

    [microscope]
    path = /home/pi/shared
    writeable=Yes
    create mask=0777
    directory mask=0777
    public=yes

Enable and start

    sudo systemctl start smbd
    sudo systemctl enable smbd
