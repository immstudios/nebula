Nebula
======

Nebula is a media asset management and workflow automation system for TV and radio broadcast. Version 5 is under development.

Key features
------------

 - media asset management, metadata handling
 - conversion, video and audio normalization using [Themis](https://github.com/martastain/themis) library
 - programme planning, scheduling
 - linear playout control ([CasparCG](http://www.casparcg.com) and [Liquidsoap](http://liquidsoap.fm))
 - VOD and pseudolinear output automation
 - dynamic CG ([nxcg](https://github.com/martastain/nxcg))
 - web publishing
 - statistics, reporting

### Ingest

Import service normalizes and transcodes all incoming files to the production format.

This process includes metadata extraction, aspect ratio correction, crop and rotation detection, smart frame rate and size normalization and EBU R128 loudness adjustment.

### Asset management

Nebula uses extendable, EBUCore based metadata model backed by a powerful database engine.

Python scripting allows limitless extendability and automation.

### Scheduling(

Client application Firefly allows simple drag&drop block (EPG) based scheduling and creating and applying templates

Optional Dramatica engine - template based scheduler with smart solving algorithm enables automatic or semi-automatic playlist creation including "selector style" music blocks solving.

### Playout

Nebula uses CasparCG playout server for 24/7 multichannel playback in various resolutions and frame rates.

Installation
------------

Use [nebula-setup](https://github.com/immstudios/nebula-setup) repository to install prerequisites.

Need help?
----------

Professional support for Nebula is provided by [Nebula broadcast](http://nebulabroadcast.com)
