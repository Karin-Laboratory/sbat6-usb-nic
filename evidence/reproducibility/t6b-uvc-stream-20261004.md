# UVC probe and stream evidence

- Workspace: `uvcvideo-sbat6b-canonical-20261004`
- Source: official Linux 5.4.238, commit `6849d8c4a61a93bb3abf2f65c84ec1ebfa9a9fb6`
- Device: UltraSemi USB2 Video, `345f:2130`, 480 Mbps, UVC 1.00
- Exact live stack: Build A, all seven published modules

The seven modules were transferred to SBA6D, SHA256-verified, and loaded in the
documented DAG order. Every `insmod` returned 0; `uvcvideo` registered normally.
The device bound and exposed `/dev/video0` (capture) and `/dev/video1`. MMAP plus
STREAMON on `/dev/video0` captured five MJPEG 640x480 frames; frames 1-4 and the
saved fifth frame were 15,843 bytes. The JPEG decoded successfully and the image
showed clean vertical color bars with no visible corruption.

The saved frame hash is
`9f195adca098a089e27ac312556b293b100f58845f466ac4923b6730f8281c17`.
boot_id was unchanged, and there was no USB reset/disconnect, UVC/vb2 warning,
Oops, or panic. The published image is linked from the UVC README.

