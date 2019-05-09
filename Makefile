.PHONY: install uninstall
SYMLINKS = /usr/bin/nxa /usr/bin/nxt /usr/bin/nxs /usr/bin/nxl /usr/bin/nxadduser

install : $(SYMLINKS)

$(SYMLINKS):
	ln -s /opt/nebula/manage.py $@
