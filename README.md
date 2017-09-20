# Raytracer

A real-time raytracer in a WebGL2 fragment shader that reads a kd-tree and mesh data from a texture (generated with a blender plugin).

You can try it [online here](http://andrewhills.github.io/raytracer/demo.html). The controls are hold left click to look around and mouse wheel to move backwards and forwards.

There is also a shadron version available.

![](misc/screenshot0.jpg)
![](misc/screenshot1.jpg)
![](misc/screenshot2.jpg)

## TODO

* test if raymarching is any faster
* add mipmapping, texture filtering
* implement keyframes for camera and lights
* use blender's lighting equations instead