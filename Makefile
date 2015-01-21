PREFIX = /usr

INSTALL_ROOT := $(DESTDIR)$(PREFIX)/share/deepin-social-sharing


all:

com.deepin.SocialSharing.service: com.deepin.SocialSharing.service.in
	sed -e "s,@prefix@,$(PREFIX)," $< > $@

install:
	mkdir -p $(INSTALL_ROOT)
	cp -r src qmls images $(INSTALL_ROOT)
	mkdir -p $(DESTDIR)$(PREFIX)/bin
	ln -s $(PREFIX)/share/deepin-share/src/deepin-social-sharing $(DESTDIR)$(PREFIX)/bin/deepin-social-sharing
	mkdir -p $(DESTDIR)$(PREFIX)/share/dbus-1/services
	cp *.service $(DESTDIR)$(PREFIX)/share/dbus-1/services

clean:
	rm -f com.deepin.SocialSharing.service
