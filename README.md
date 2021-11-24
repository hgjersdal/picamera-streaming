# picamera-test

- `p` to take an image. Saved as img?.jpg, where ? starts at 0 and increments by one per press
- `z` to toggle between 100% crop and full screen (assuming 2560x1440 screen)
- `q` quit

For python module keyboard to work without being root:
Add user to groups tty and input.

Remove calls to ensure_root in `_nixkeyboard.py`

# web-streaming.py

Run python code on pi, go to <pi-ip-address>:8000 in a web browser

Stores all images to /home/pi/shared/img<num>.jpg, where <num> starts at 0. Works well with smb share. Images are stored at maximum resolution.


