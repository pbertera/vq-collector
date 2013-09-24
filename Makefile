# voice quality collector Daemon 
# Modify CONFIG befor run the make command

include CONFIG
include VERSION

BUILDDIR=buildir
BUILDTARDIR=$(NAME)_$(VERSION)

# TODO: split substitutions between
# pre-dists substitution and installation substitution
# include AUTHOR, HOMEPAGE and so on in VERSION file 
do_subst = sed -e 's,__VERSION__,${VERSION},g' \
			-e 's,__PIDFILE__,$(PIDFILE),g' \
			-e 's,__LOGFILE__,$(LOGFILE),g' \
			-e 's,__DESTDIR__,$(DESTDIR),g' \
			-e 's,__DAEMONDIR__,$(DAEMONDIR),g' \
			-e 's,__CONFDIR__,$(CONFDIR),g' \
			-e 's,__PYTHON_LIB__,$(PYTHON_LIB),g' \

build-setup:
	mkdir -p $(BUILDDIR)

vq-collector-bin:
	$(do_subst) < src/vq-collector/vq-collector.py > $(BUILDDIR)/vq-collector

vq-collector-init-script:
	if [ -f  src/utils/vq-collector.$(TARGET).init ];then\
		$(do_subst) < src/utils/vq-collector.$(TARGET).init > $(BUILDDIR)/vq-collector.init;\
	else\
		echo "ERROR: No init script found for $(TARGET) target";\
	fi;
	# TODO:
	#else\
	#	$(do_subst) < src/utils/vq-collector.lsb.init > $(BUILDDIR)/vq-collector.init;\
	#fi;

vq-collector-conf:
	$(do_subst) < src/vq-collector/vq-collector.conf-default > $(BUILDDIR)/vq-collector.conf

build-clean:
	rm -rf ${BUILDTARDIR}
	find src/ -name "*.pyc" | xargs rm -fr
	rm -rf $(BUILDDIR)
	rm -rf src/setup.py

siplib-build:
	$(do_subst) < src/setup.py.in > src/setup.py
	cd src && python setup.py build --build-lib ../$(BUILDDIR)/python-build

# install siplib python package
siplib: siplib-build
	install -d -m 0755 $(PYTHON_LIB)
	install -d -m 0755 $(PYTHON_LIB)/siplib
	install -o $(USER) -g $(GROUP) -m 0644 $(BUILDDIR)/python-build/siplib/__init__.py $(PYTHON_LIB)/siplib/__init__.py
	install -o $(USER) -g $(GROUP) -m 0644 $(BUILDDIR)/python-build/siplib/sip.py $(PYTHON_LIB)/siplib/sip.py
	install -o $(USER) -g $(GROUP) -m 0644 $(BUILDDIR)/python-build/siplib/daemon.py $(PYTHON_LIB)/siplib/daemon.py

vq-collector: build-clean build-setup vq-collector-bin vq-collector-init-script vq-collector-conf siplib
	# install scripts
	install -d -m 0755 $(DAEMONDIR)
	install -d -m 0755 $(INITDIR)
	install -d -m 0750 $(CONFDIR)
	install -o $(USER) -g $(GROUP) -m 0755 $(BUILDDIR)/vq-collector $(DAEMONDIR)/vq-collector
	install -o $(USER) -g $(GROUP) -m 0755 $(BUILDDIR)/vq-collector.init $(INITDIR)/vq-collector
	install -o $(USER) -g $(GROUP) -m 0644 $(BUILDDIR)/vq-collector.conf $(CONFDIR)/vq-collector.conf

vq-collector-remove:
	rm -f $(DAEMONDIR)/vq-collector
	rm -f $(CONFDIR)/vq-collector.conf
	rm -f $(INITDIR)/vq-collector
	rm -rf $(PYTHON_LIB)/siplib

dist: build-clean
	mkdir ${BUILDTARDIR}
	cp -a src ${BUILDTARDIR}/
	find ${BUILDTARDIR} -name .svn -type d | xargs rm -r
	find ${BUILDTARDIR} -name .git -type d | xargs rm -r
	cp changelog TODO CONFIG VERSION INSTALL README.md COPYING ${BUILDTARDIR}/
	cp Makefile ${BUILDTARDIR}/
	tar czvf ${BUILDTARDIR}.tgz ${BUILDTARDIR}
