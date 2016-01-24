Nebula
======

Nebula is media asset management and workflow automation system for TV and radio broadcast.

This is not a working version of the software. Please use stable version 4:

 - [Server](https://github.com/opennx/nx.server)
 - [Client](https://github.com/opennx/nx.client)

Version 5 should be data-compatible with version 4, but there will be API changes.

Several deprecated methods will be removed, workers and plugins will have to be updated.
This version is under heavy development and new features are backported if possible.

Key features
------------

 - media asset management, metadata handling
 - conversion, video and audio normalization using [Themis](https://github.com/martastain/themis) library
 - programme planning, scheduling
 - linear playout control ([CasparCG](http://www.casparcg.com) and [Liquidsoap](http://liquidsoap.fm))
 - VOD and pseudolinear output automation
 - dynamic CG ([nxcg](https://github.com/martastain/nxcg))
 - web publishing
 - statistics reporting

### Integration

 - [CasparCG](http://casparcg.com) - Video and CG Playout server
 - [Unity](https://github.com/immstudios/unity) - Pseudo-linear streaming server
 - [Mediatheque](https://github.com/immstudios/mediatheque) - VOD HLS CDN (RTFM BTW)
 - [Dramatica](https://github.com/martastain/dramatica) - Automated playlist creation
 - [Themis](https://github.com/martastain/themis) - File ingest server
 - [Aura](https://github.com/martastain/aura) - VOD Encoder
 - [Warp](http://weebo.cz) - Web CMS

Installation
------------

### Prerequisities

 - Debian Jessie
 - ffmpeg (media processing nodes) - use [inst.ffmpeg.sh](https://github.com/immstudios/installers/blob/master/install.ffmpeg.sh) script
 - nginx (core node) - use [inst.nginx.sh](https://github.com/immstudios/installers/blob/master/install.nginx.sh) script

### Installation

```bash
cd /opt
git clone https://github.com/immstudios/nebula
```

### Starting

Preffered way is to start Nebula in GNU Screen:

```bash
cd /opt/nebula && ./nebula.py
```

### Stopping

To stop nebula press `CTRL+C` ONCE.


Need help?
----------

Community version support is not provided directly by imm studios.

Professional support for Nebula is provided to organisations with support contract.
On site installation and support is available via our Czech (support.prague@immstudios.org) and New Zealand (support.christchurch@immstudios.org) offices.

