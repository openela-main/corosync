# Conditionals
# Invoke "rpmbuild --without <feature>" or "rpmbuild --with <feature>"
# to disable or enable specific features
%bcond_with watchdog
%bcond_with monitoring
%bcond_without snmp
%bcond_without dbus
%bcond_without systemd
%bcond_without xmlconf
%bcond_without nozzle
%bcond_without vqsim
%bcond_without runautogen
%bcond_without userflags
%bcond_without spausedd

%global gitver %{?numcomm:.%{numcomm}}%{?alphatag:.%{alphatag}}%{?dirty:.%{dirty}}
%global gittarver %{?numcomm:.%{numcomm}}%{?alphatag:-%{alphatag}}%{?dirty:-%{dirty}}

%if %{with spausedd}
%global spausedd_version 20201112
%endif

Name: corosync
Summary: The Corosync Cluster Engine and Application Programming Interfaces
Version: 3.1.7
Release: 1%{?gitver}%{?dist}
License: BSD
URL: http://corosync.github.io/corosync/
Source0: http://build.clusterlabs.org/corosync/releases/%{name}-%{version}%{?gittarver}.tar.gz

%if %{with spausedd}
Source1: https://github.com/jfriesse/spausedd/releases/download/%{spausedd_version}/spausedd-%{spausedd_version}.tar.gz
# VMGuestLib exists only for x86_64 architecture
%ifarch x86_64
%global use_vmguestlib 1
%endif
%endif

# Runtime bits
# The automatic dependency overridden in favor of explicit version lock
Requires: corosynclib%{?_isa} = %{version}-%{release}

# Support crypto reload
Requires: libknet1 >= 1.18
# NSS crypto plugin should be always installed
Requires: libknet1-crypto-nss-plugin >= 1.18

# Build bits
BuildRequires: gcc
BuildRequires: groff
BuildRequires: libqb-devel
BuildRequires: libknet1-devel >= 1.18
BuildRequires: zlib-devel
%if %{with runautogen}
BuildRequires: autoconf automake libtool
%endif
%if %{with monitoring}
BuildRequires: libstatgrab-devel
%endif
%if %{with snmp}
BuildRequires: net-snmp-devel
%endif
%if %{with dbus}
BuildRequires: dbus-devel
%endif
%if %{with nozzle}
BuildRequires: libnozzle1-devel
%endif
%if %{with systemd}
%{?systemd_requires}
BuildRequires: systemd
BuildRequires: systemd-devel
%else
Requires(post): /sbin/chkconfig
Requires(preun): /sbin/chkconfig
%endif
%if %{with xmlconf}
Requires: libxslt
%endif
%if %{with vqsim}
BuildRequires: readline-devel
%endif
%if %{defined use_vmguestlib}
BuildRequires: pkgconfig(vmguestlib)
%endif

%prep
%if %{with spausedd}
%setup -q -a 1 -n %{name}-%{version}%{?gittarver}
%else
%setup -q -n %{name}-%{version}%{?gittarver}
%endif

%build
%if %{with runautogen}
./autogen.sh
%endif

%{configure} \
%if %{with watchdog}
	--enable-watchdog \
%endif
%if %{with monitoring}
	--enable-monitoring \
%endif
%if %{with snmp}
	--enable-snmp \
%endif
%if %{with dbus}
	--enable-dbus \
%endif
%if %{with systemd}
	--enable-systemd \
%endif
%if %{with xmlconf}
	--enable-xmlconf \
%endif
%if %{with nozzle}
	--enable-nozzle \
%endif
%if %{with vqsim}
	--enable-vqsim \
%endif
%if %{with userflags}
	--enable-user-flags \
%endif
	--with-initddir=%{_initrddir} \
	--with-systemddir=%{_unitdir} \
	--docdir=%{_docdir}

make %{_smp_mflags}

%if %{with spausedd}
cd spausedd-%{spausedd_version}
CFLAGS="${CFLAGS:-%{optflags}}" ; export CFLAGS
make \
%if %{defined use_vmguestlib}
    WITH_VMGUESTLIB=1 \
%else
    WITH_VMGUESTLIB=0 \
%endif
    %{?_smp_mflags}
%endif

%install
make install DESTDIR=%{buildroot}

%if %{with dbus}
mkdir -p -m 0700 %{buildroot}/%{_sysconfdir}/dbus-1/system.d
install -m 644 %{_builddir}/%{name}-%{version}%{?gittarver}/conf/corosync-signals.conf %{buildroot}/%{_sysconfdir}/dbus-1/system.d/corosync-signals.conf
%endif

## tree fixup
# drop static libs
rm -f %{buildroot}%{_libdir}/*.a
rm -f %{buildroot}%{_libdir}/*.la
# drop docs and html docs for now
rm -rf %{buildroot}%{_docdir}/*
# /etc/sysconfig/corosync-notifyd
mkdir -p %{buildroot}%{_sysconfdir}/sysconfig
install -m 644 tools/corosync-notifyd.sysconfig.example \
   %{buildroot}%{_sysconfdir}/sysconfig/corosync-notifyd
# /etc/sysconfig/corosync
install -m 644 init/corosync.sysconfig.example \
   %{buildroot}%{_sysconfdir}/sysconfig/corosync

%if %{with spausedd}
cd spausedd-%{spausedd_version}
make DESTDIR="%{buildroot}" PREFIX="%{_prefix}" install

%if %{with systemd}
mkdir -p %{buildroot}/%{_unitdir}
install -m 644 -p init/spausedd.service %{buildroot}/%{_unitdir}
%else
mkdir -p %{buildroot}/%{_initrddir}
install -m 755 -p init/spausedd %{buildroot}/%{_initrddir}
%endif

cd ..
%endif

%description
This package contains the Corosync Cluster Engine Executive, several default
APIs and libraries, default configuration files, and an init script.

%post
%if %{with systemd} && 0%{?systemd_post:1}
%systemd_post corosync.service
%else
if [ $1 -eq 1 ]; then
	/sbin/chkconfig --add corosync || :
fi
%endif

%preun
%if %{with systemd} && 0%{?systemd_preun:1}
%systemd_preun corosync.service
%else
if [ $1 -eq 0 ]; then
	/sbin/service corosync stop &>/dev/null || :
	/sbin/chkconfig --del corosync || :
fi
%endif

%postun
%if %{with systemd} && 0%{?systemd_postun:1}
%systemd_postun corosync.service
%endif

%files
%doc LICENSE
%{_sbindir}/corosync
%{_sbindir}/corosync-keygen
%{_sbindir}/corosync-cmapctl
%{_sbindir}/corosync-cfgtool
%{_sbindir}/corosync-cpgtool
%{_sbindir}/corosync-quorumtool
%{_sbindir}/corosync-notifyd
%{_bindir}/corosync-blackbox
%if %{with xmlconf}
%{_bindir}/corosync-xmlproc
%dir %{_datadir}/corosync
%{_datadir}/corosync/xml2conf.xsl
%{_mandir}/man8/corosync-xmlproc.8*
%{_mandir}/man5/corosync.xml.5*
%endif
%dir %{_sysconfdir}/corosync
%dir %{_sysconfdir}/corosync/uidgid.d
%config(noreplace) %{_sysconfdir}/corosync/corosync.conf.example
%config(noreplace) %{_sysconfdir}/sysconfig/corosync-notifyd
%config(noreplace) %{_sysconfdir}/sysconfig/corosync
%config(noreplace) %{_sysconfdir}/logrotate.d/corosync
%if %{with dbus}
%{_sysconfdir}/dbus-1/system.d/corosync-signals.conf
%endif
%if %{with snmp}
%{_datadir}/snmp/mibs/COROSYNC-MIB.txt
%endif
%if %{with systemd}
%{_unitdir}/corosync.service
%{_unitdir}/corosync-notifyd.service
%else
%{_initrddir}/corosync
%{_initrddir}/corosync-notifyd
%endif
%dir %{_localstatedir}/lib/corosync
%dir %{_localstatedir}/log/cluster
%{_mandir}/man7/corosync_overview.7*
%{_mandir}/man8/corosync.8*
%{_mandir}/man8/corosync-blackbox.8*
%{_mandir}/man8/corosync-cmapctl.8*
%{_mandir}/man8/corosync-keygen.8*
%{_mandir}/man8/corosync-cfgtool.8*
%{_mandir}/man8/corosync-cpgtool.8*
%{_mandir}/man8/corosync-notifyd.8*
%{_mandir}/man8/corosync-quorumtool.8*
%{_mandir}/man5/corosync.conf.5*
%{_mandir}/man5/votequorum.5*
%{_mandir}/man7/cmap_keys.7*

# library
#
%package -n corosynclib
Summary: The Corosync Cluster Engine Libraries

%description -n corosynclib
This package contains corosync libraries.

%files -n corosynclib
%doc LICENSE
%{_libdir}/libcfg.so.*
%{_libdir}/libcpg.so.*
%{_libdir}/libcmap.so.*
%{_libdir}/libquorum.so.*
%{_libdir}/libvotequorum.so.*
%{_libdir}/libsam.so.*
%{_libdir}/libcorosync_common.so.*

%post -n corosynclib -p /sbin/ldconfig

%postun -n corosynclib -p /sbin/ldconfig

%package -n corosynclib-devel
Summary: The Corosync Cluster Engine Development Kit
Requires: corosynclib%{?_isa} = %{version}-%{release}
Requires: pkgconfig
Provides: corosync-devel = %{version}

%description -n corosynclib-devel
This package contains include files and man pages used to develop using
The Corosync Cluster Engine APIs.

%files -n corosynclib-devel
%doc LICENSE
%dir %{_includedir}/corosync/
%{_includedir}/corosync/corodefs.h
%{_includedir}/corosync/cfg.h
%{_includedir}/corosync/cmap.h
%{_includedir}/corosync/corotypes.h
%{_includedir}/corosync/cpg.h
%{_includedir}/corosync/hdb.h
%{_includedir}/corosync/sam.h
%{_includedir}/corosync/quorum.h
%{_includedir}/corosync/votequorum.h
%{_libdir}/libcfg.so
%{_libdir}/libcpg.so
%{_libdir}/libcmap.so
%{_libdir}/libquorum.so
%{_libdir}/libvotequorum.so
%{_libdir}/libsam.so
%{_libdir}/libcorosync_common.so
%{_libdir}/pkgconfig/*.pc
%{_mandir}/man3/cpg_*3*
%{_mandir}/man3/quorum_*3*
%{_mandir}/man3/votequorum_*3*
%{_mandir}/man3/sam_*3*
%{_mandir}/man3/cmap_*3*

%if %{with vqsim}
%package -n corosync-vqsim
Summary: The Corosync Cluster Engine - Votequorum Simulator
Requires: corosynclib%{?_isa} = %{version}-%{release}
Requires: pkgconfig

%description -n corosync-vqsim
A command-line simulator for the corosync votequorum subsystem.
It uses the same code as the corosync quorum system but forks
them into subprocesses to simulate nodes.
Nodes can be added and removed as well as partitioned (to simulate
network splits)

%files -n corosync-vqsim
%doc LICENSE
%{_bindir}/corosync-vqsim
%{_mandir}/man8/corosync-vqsim.8*
%endif

# optional spausedd
%if %{with spausedd}

%package -n spausedd
Summary: Utility to detect and log scheduler pause
URL: https://github.com/jfriesse/spausedd

%if %{with systemd}
%{?systemd_requires}
%else
Requires(post): /sbin/chkconfig
Requires(preun): /sbin/chkconfig
%endif

%description -n spausedd
Utility to detect and log scheduler pause

%files -n spausedd
%doc spausedd-%{spausedd_version}/AUTHORS spausedd-%{spausedd_version}/COPYING
%{_bindir}/spausedd
%{_mandir}/man8/spausedd*
%if %{with systemd}
%{_unitdir}/spausedd.service
%else
%{_initrddir}/spausedd
%endif

%post -n spausedd
%if %{with systemd} && 0%{?systemd_post:1}
%systemd_post spausedd.service
%else
if [ $1 -eq 1 ]; then
    /sbin/chkconfig --add spausedd || :
fi
%endif

%preun -n spausedd
%if %{with systemd} && 0%{?systemd_preun:1}
%systemd_preun spausedd.service
%else
if [ $1 -eq 0 ]; then
    /sbin/service spausedd stop &>/dev/null || :
    /sbin/chkconfig --del spausedd || :
fi
%endif

%postun -n spausedd
%if %{with systemd} && 0%{?systemd_postun:1}
    %systemd_postun spausedd.service
%endif

%endif

%changelog
* Tue Nov 15 2022 Jan Friesse <jfriesse@redhat.com> 3.1.7-1
- Resolves: rhbz#2135860

- New upstream release (rhbz#2135860)

* Wed Nov 24 2021 Jan Friesse <jfriesse@redhat.com> 3.1.5-2
- Resolves: rhbz#2002115
- Resolves: rhbz#2024658

- totem: Add cancel_hold_on_retransmit config option (rhbz#2002115)
- merge upstream commit cdf72925db5a81e546ca8e8d7d8291ee1fc77be4 (rhbz#2002115)
- totemsrp: Switch totempg buffers at the right time (rhbz#2024658)
- merge upstream commit e7a82370a7b5d3ca342d5e42e25763fa2c938739 (rhbz#2024658)

* Wed Aug 04 2021 Jan Friesse <jfriesse@redhat.com> 3.1.5-1
- Related: rhbz#1948973

- New upstream release (rhbz#1948973)

* Thu Jun 03 2021 Jan Friesse <jfriesse@redhat.com> 3.1.4-1
- Related: rhbz#1948973
- Resolves: rhbz#1962139

- New upstream release (rhbz#1948973)
- stats: fix crash when iterating over deleted keys (rhbz#1962139)

* Fri May 21 2021 Jan Friesse <jfriesse@redhat.com> 3.1.3-1
- Resolves: rhbz#1948973

- New upstream release (rhbz#1948973)

* Fri Apr 30 2021 Jan Friesse <jfriesse@redhat.com> 3.1.0-5
- Resolves: rhbz#1954432

* Tue Apr 06 2021 Jan Friesse <jfriesse@redhat.com> 3.1.0-4
- Resolves: rhbz#1946623

- knet: pass correct handle to knet_handle_compress (rhbz#1946623)

* Thu Nov 12 2020 Jan Friesse <jfriesse@redhat.com> 3.1.0-3
- Resolves: rhbz#1897085
- Resolves: rhbz#1896493

- spausedd: Add ability to move process into root cgroup (rhbz#1897085)
- totemknet: Check both cipher and hash for crypto (rhbz#1896493)

* Tue Nov 10 2020 Jan Friesse <jfriesse@redhat.com> 3.1.0-2
- Resolves: rhbz#1896309

- Fix log_perror (rhbz#1896309)

* Tue Oct 20 2020 Jan Friesse <jfriesse@redhat.com> 3.1.0-1
- Resolves: rhbz#1855293
- Resolves: rhbz#1855303
- Resolves: rhbz#1870449
- Resolves: rhbz#1887400

- New upstream release (rhbz#1855293)
- Support for reload of crypto configuration (rhbz#1855303)
- Increase default token timeout to 3000ms (rhbz#1870449)
- Add support for nodelist callback into quorum service (rhbz#1887400)

* Tue May 26 2020 Jan Friesse <jfriesse@redhat.com> 3.0.3-4
- Resolves: rhbz#1780137
- Resolves: rhbz#1791792
- Resolves: rhbz#1809864
- Resolves: rhbz#1816653

- votequorum: Ignore the icmap_get_* return value (rhbz#1780137)
- merge upstream commit cddd62f972bca276c934e58f08da84071cec1ddb (rhbz#1780137)
- man: move cmap_keys man page from section 8 to 7 (rhbz#1791792)
- merge upstream commit f1d36307e524f9440733f0b01a9fc627a0e1cac7 (rhbz#1791792)
- votequorum: Reflect runtime change of 2Node to WFA (rhbz#1780137)
- merge upstream commit 8ce65bf951bc1e5b2d64b60ea027fbdc551d4fc8 (rhbz#1780137)
- stats: Add stats for scheduler misses (rhbz#1791792)
- merge upstream commit 48b6894ef41e9a06ccbb696d062d86ef60dc2c4b (rhbz#1791792)
- stats: Use nanoseconds from epoch for schedmiss (rhbz#1791792)
- merge upstream commit ebd05fa00826c366922e619b012a0684c6856539 (rhbz#1791792)
- main: Add schedmiss timestamp into message (rhbz#1791792)
- merge upstream commit 35662dd0ec53f456445c30c0ef92892f47b25aa2 (rhbz#1791792)
- votequorum: Change check of expected_votes (rhbz#1809864)
- merge upstream commit 0c16442f2d93f32a229b87d2672e2dc8025ec704 (rhbz#1809864)
- quorumtool: exit on invalid expected votes (rhbz#1809864)
- merge upstream commit 5f543465bb3506b7f4929a426f1c22a9c854cecd (rhbz#1809864)
- votequorum: set wfa status only on startup (rhbz#1816653)
- merge upstream commit ca320beac25f82c0c555799e647a47975a333c28 (rhbz#1816653)

* Tue Apr 28 2020 Jan Friesse <jfriesse@redhat.com> - 3.0.3-3
- Resolves: rhbz#1828295

- Add explicit spausedd dependency for revdeps CI test

* Mon Nov 25 2019 Jan Friesse <jfriesse@redhat.com> - 3.0.3-2
- Related: rhbz#1745623

- New upstream release of spausedd

* Mon Nov 25 2019 Jan Friesse <jfriesse@redhat.com> - 3.0.3-1
- Resolves: rhbz#1745623

- New upstream release

* Wed Oct 30 2019 Jan Friesse <jfriesse@redhat.com> 3.0.2-4
- Resolves: rhbz#1745624
- Resolves: rhbz#1745642
- Resolves: rhbz#1749263
- Resolves: rhbz#1765025

- totem: fix check if all nodes have same number of links (rhbz#1749263)
- merge upstream commit 816324c94cfb917b11f43954b8757424db28b390 (rhbz#1749263)
- totem: Increase ring_id seq after load (rhbz#1745624)
- merge upstream commit 3675daceeeeb72af043f5c051daed463fdd2d2a1 (rhbz#1745624)
- man: Fix link_mode priority description (rhbz#1745642)
- merge upstream commit 0a323ff2ed0f2aff9cb691072906e69cb96ed662 (rhbz#1745642)
- totemsrp: Reduce MTU to left room second mcast (rhbz#1765025)
- merge upstream commit ee8b8993d98b3f6af9c058194228fc534fcd0796 (rhbz#1765025)

* Tue Aug 06 2019 Jan Friesse <jfriesse@redhat.com> - 3.0.2-3
- Resolves: rhbz#1738218

- Do not set exec permission for service file
- Fix CFLAGS definition

* Thu Jun 13 2019 Jan Friesse <jfriesse@redhat.com> 3.0.2-2
- Related: rhbz#1679656

- Improve spausedd test

* Wed Jun 12 2019 Jan Friesse <jfriesse@redhat.com> 3.0.2-1
- Resolves: rhbz#1705591
- Resolves: rhbz#1688889

* Mon May 13 2019 Jan Friesse <jfriesse@redhat.com> 3.0.0-4
- Related: rhbz#1679656

- Really add gating

* Mon May 13 2019 Jan Friesse <jfriesse@redhat.com> 3.0.0-3
- Resolves: rhbz#1691401
- Related: rhbz#1679656

- Add spausedd subpackage
- Add gating tests

* Fri Jan 11 2019 Jan Friesse <jfriesse@redhat.com> 3.0.0-2
- Resolves: rhbz#1665211

- totemip: Use AF_UNSPEC for ipv4-6 and ipv6-4 (rhbz#1665211)
- merge upstream commit 2ab4d4188670356dcb82a80f2fc4598f5145c77d (rhbz#1665211)

* Fri Dec 14 2018 Jan Friesse <jfriesse@redhat.com> - 3.0.0-1
- Resolves: rhbz#1600915

- New upstream release

* Tue Dec 11 2018 Jan Friesse <jfriesse@redhat.com> 2.99.5-2
- Resolves: rhbz#1654630

- man: Add some information about address resolution (rhbz#1654630)
- merge upstream commit 8d50bd946dd7e01da75f06da3f885e7dc82f4f12 (rhbz#1654630)
- config: Look up hostnames in a defined order (rhbz#1654630)
- merge upstream commit 3d7f136f86a56dd9d9caa9060f7a01e8b681eb7f (rhbz#1654630)

* Fri Dec  7 2018 Jan Friesse <jfriesse@redhat.com> - 2.99.5-1
- Related: rhbz#1600915

- New upstream release

* Tue Dec  4 2018 Jan Friesse <jfriesse@redhat.com> - 2.99.4-2
- Resolves: rhbz#1655179

- Add libknet1-crypto-nss-plugin dependency

* Tue Nov 20 2018 Jan Friesse <jfriesse@redhat.com> - 2.99.4-1
- Related: rhbz#1600915

- New upstream release

* Mon Oct 15 2018 Jan Friesse <jfriesse@redhat.com> 2.99.3-5
- Resolves: rhbz#1639211

- config: Fix crash in reload if new interfaces are added (rhbz#1639211)
- merge upstream commit 9f2d5a3a3faa8bd1021b505bcf3c5428b3435e39 (rhbz#1639211)

* Tue Sep 18 2018 Jan Friesse <jfriesse@redhat.com> 2.99.3-4
- Related: rhbz#1615945

- Rebuild for new LibQB

* Mon Aug 20 2018 Jan Friesse <jfriesse@redhat.com> 2.99.3-3
- Resolves: rhbz#1602409

- Remove libcgroup (rhbz#1602409)
- merge upstream commit c9e5d6db13fa965d83e27a3b664477e9b5b26edf (rhbz#1602409)

* Mon Jul 30 2018 Florian Weimer <fweimer@redhat.com> - 2.99.3-2
- Rebuild with fixed binutils

* Fri Jul 13 2018 Jan Friesse <jfriesse@redhat.com> - 2.99.3-1
- New upstream release

* Mon Apr 30 2018 Jan Friesse <jfriesse@redhat.com> - 2.99.2-1
- New upstream release

* Fri Mar 16 2018 Jan Friesse <jfriesse@redhat.com> - 2.99.1-1
- New upstream release

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 2.4.3-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Fri Jan 19 2018 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 2.4.3-2
- Rebuild to fix upgradepath

* Fri Oct 20 2017 Jan Friesse <jfriesse@redhat.com> - 2.4.3-1
- New upstream release

* Mon Oct 09 2017 Troy Dawson <tdawson@redhat.com> - 2.4.2-7
- Cleanup spec file conditionals

* Mon Oct 02 2017 Troy Dawson <tdawson@redhat.com> - 2.4.2-6
- Bump to rebuild on newer binutils

* Wed Aug 23 2017 Adam Williamson <awilliam@redhat.com> - 2.4.2-5
- Disable RDMA on 32-bit ARM (#1484155)

* Wed Aug 02 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2.4.2-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2.4.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2.4.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Mon Nov  7 2016 Jan Friesse <jfriesse@redhat.com> - 2.4.2-1
- New upstream release

* Thu Aug  4 2016 Jan Friesse <jfriesse@redhat.com> - 2.4.1-1
- New upstream release

* Thu Jun 30 2016 Jan Friesse <jfriesse@redhat.com> - 2.4.0-1
- New upstream release

* Thu Jun 16 2016 Jan Friesse <jfriesse@redhat.com> - 2.3.6-1
- New upstream release

* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 2.3.5-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Wed Jul 01 2015 Jan Friesse <jfriesse@redhat.com> - 2.3.5-1
- New upstream release

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.3.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Tue Aug 26 2014 Jan Friesse <jfriesse@redhat.com> - 2.3.4-1
- New upstream release

* Sat Aug 16 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.3.3-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.3.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Tue Jan 14 2014 Jan Friesse <jfriesse@redhat.com> - 2.3.3-1
- New upstream release

* Mon Sep 16 2013 Jan Friesse <jfriesse@redhat.com> - 2.3.2-1
- New upstream release

* Mon Aug 19 2013 Jan Friesse <jfriesse@redhat.com> 2.3.1-3
- Resolves: rhbz#998362

- Fix scheduler pause-detection timeout (rhbz#998362)
- merge upstream commit 2740cfd1eac60714601c74df2137fe588b607866 (rhbz#998362)

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.3.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Wed Jul 10 2013 Jan Friesse <jfriesse@redhat.com> - 2.3.1-1
- New upstream release
- Fix incorrect dates in specfile changelog section

* Mon Mar 25 2013 Jan Friesse <jfriesse@redhat.com> - 2.3.0-3
- Resolves: rhbz#925185

- Run autogen by default

* Wed Feb 13 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.3.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Fri Jan 18 2013 Jan Friesse <jfriesse@redhat.com> - 2.3.0-1
- New upstream release

* Wed Dec 12 2012 Jan Friesse <jfriesse@redhat.com> - 2.2.0-1
- New upstream release

* Thu Oct 11 2012 Jan Friesse <jfriesse@redhat.com> - 2.1.0-1
- New upstream release

* Fri Aug 3 2012 Steven Dake <sdake@redhat.com> - 2.0.1-3
- add groff as a BuildRequires as it is no longer installed in the buildroot

* Wed Jul 18 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.0.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Tue May 22 2012 Jan Friesse <jfriesse@redhat.com> - 2.0.1-1
- New upstream release

* Tue Apr 17 2012 Fabio M. Di Nitto <fdinitto@redhat.com> - 2.0.0-2
- Backport IPCS fix from master (ack by Steven)

* Tue Apr 10 2012 Jan Friesse <jfriesse@redhat.com> - 2.0.0-1
- New upstream release

* Thu Apr 05 2012 Karsten Hopp <karsten@redhat.com> 1.99.9-1.1
- bump release and rebuild on PPC

* Tue Mar 27 2012 Jan Friesse <jfriesse@redhat.com> - 1.99.9-1
- New upstream release

* Fri Mar 16 2012 Jan Friesse <jfriesse@redhat.com> - 1.99.8-1
- New upstream release

* Tue Mar  6 2012 Jan Friesse <jfriesse@redhat.com> - 1.99.7-1
- New upstream release

* Tue Feb 28 2012 Jan Friesse <jfriesse@redhat.com> - 1.99.6-1
- New upstream release

* Wed Feb 22 2012 Jan Friesse <jfriesse@redhat.com> - 1.99.5-1
- New upstream release

* Tue Feb 14 2012 Jan Friesse <jfriesse@redhat.com> - 1.99.4-1
- New upstream release

* Tue Feb 14 2012 Jan Friesse <jfriesse@redhat.com> - 1.99.3-1
- New upstream release

* Tue Feb  7 2012 Fabio M. Di Nitto <fdinitto@redhat.com> - 1.99.2-1
- New upstream release
- Re-enable xmlconfig bits
- Ship cmap man pages
- Add workaround to usrmove breakage!!

* Thu Feb  2 2012 Fabio M. Di Nitto <fdinitto@redhat.com> - 1.99.1-2
- Add proper Obsoltes on openais/cman/clusterlib

* Wed Feb  1 2012 Fabio M. Di Nitto <fdinitto@redhat.com> - 1.99.1-1
- New upstream release
- Temporary disable xml config (broken upstream tarball)

* Tue Jan 24 2012 Jan Friesse <jfriesse@redhat.com> - 1.99.0-1
- New upstream release

* Thu Jan 12 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.4.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Thu Oct 06 2011 Jan Friesse <jfriesse@redhat.com> - 1.4.2-1
- New upstream release

* Thu Sep 08 2011 Jan Friesse <jfriesse@redhat.com> - 1.4.1-2
- Add upstream fixes

* Tue Jul 26 2011 Jan Friesse <jfriesse@redhat.com> - 1.4.1-1
- New upstream release

* Wed Jul 20 2011 Jan Friesse <jfriesse@redhat.com> - 1.4.0-2
- Change attributes of cluster log directory

* Tue Jul 19 2011 Jan Friesse <jfriesse@redhat.com> - 1.4.0-1
- New upstream release
- Resync spec file with upstream changes

* Fri Jul 08 2011 Jan Friesse <jfriesse@redhat.com> - 1.3.2-1
- New upstream release

* Tue May 10 2011 Fabio M. Di Nitto <fdinitto@redhat.com> - 1.3.1-1
- New upstream release

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.3.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Thu Dec  2 2010 Fabio M. Di Nitto <fdinitto@redhat.com> - 1.3.0-1
- New upstream release
- drop upstream patch revision-2770.patch now included in release
- update spec file to ship corosync-blackbox

* Thu Sep  2 2010 Fabio M. Di Nitto <fdinitto@redhat.com> - 1.2.8-1
- New upstream release

* Thu Jul 29 2010 Fabio M. Di Nitto <fdinitto@redhat.com> - 1.2.7-1
- New upstream release

* Fri Jul  9 2010 Dan Horák <dan[at]danny.cz> - 1.2.6-2
- no InfiniBand stack on s390(x)

* Mon Jul  5 2010 Fabio M. Di Nitto <fdinitto@redhat.com> - 1.2.6-1
- New upstream release
- Resync spec file with upstream changes

* Tue May 25 2010 Fabio M. Di Nitto <fdinitto@redhat.com> - 1.2.3-1
- New upstream release
- Rediff revision 2770 patch

* Mon May 17 2010 Fabio M. Di Nitto <fdinitto@redhat.com> - 1.2.2-1
- New upstream release
- Add upstream trunk revision 2770 to add cpg_model_initialize api.
- Fix URL and Source0 entries.
- Add workaround to broken 1.2.2 Makefile with make -j.

* Wed Mar 24 2010 Fabio M. Di Nitto <fdinitto@redhat.com> - 1.2.1-1
- New upstream release

* Tue Dec  8 2009 Fabio M. Di Nitto <fdinitto@redhat.com> - 1.2.0-1
- New upstream release
- Use global instead of define
- Update Source0 url
- Use more name macro around
- Cleanup install section. Init script is now installed by upstream
- Cleanup whitespace
- Don't deadlock between package upgrade and corosync condrestart
- Ship service.d config directory
- Fix Conflicts vs Requires
- Ship new sam library and man pages

* Fri Oct 23 2009 Fabio M. Di Nitto <fdinitto@redhat.com> - 1.1.2-1
- New upstream release fixes major regression on specific loads

* Wed Oct 21 2009 Fabio M. Di Nitto <fdinitto@redhat.com> - 1.1.1-1
- New upstream release

* Fri Sep 25 2009 Fabio M. Di Nitto <fdinitto@redhat.com> - 1.1.0-1
- New upstream release
- spec file updates:
  * enable IB support
  * explicitly define built-in features at configure time

* Tue Sep 22 2009 Fabio M. Di Nitto <fdinitto@redhat.com> - 1.0.1-1
- New upstream release
- spec file updates:
  * use proper configure macro

* Tue Jul 28 2009 Fabio M. Di Nitto <fdinitto@redhat.com> - 1.0.0-3
- spec file updates:
  * more consistent use of macros across the board
  * fix directory ownership

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Wed Jul  8 2009 Fabio M. Di Nitto <fdinitto@redhat.com> - 1.0.0-1
- New upstream release

* Thu Jul  2 2009 Fabio M. Di Nitto <fdinitto@redhat.com> - 0.100-1
- New upstream release

* Sat Jun 20 2009 Fabio M. Di Nitto <fdinitto@redhat.com> - 0.98-1
- New upstream release
- spec file updates:
  * Drop corosync-trunk patch and alpha tag.
  * Fix alphatag vs buildtrunk handling.
  * Drop requirement on ais user/group and stop creating them.
  * New config file locations from upstream: /etc/corosync/corosync.conf.

* Wed Jun 10 2009 Fabio M. Di Nitto <fdinitto@redhat.com> - 0.97-1.svn2233
- spec file updates:
  * Update to svn version 2233 to include library linking fixes

* Wed Jun 10 2009 Fabio M. Di Nitto <fdinitto@redhat.com> - 0.97-1.svn2232
- New upstream release
- spec file updates:
  * Drop pkgconfig fix that's now upstream
  * Update to svn version 2232
  * Define buildtrunk if we are using svn snapshots
  * BuildRequires: nss-devel to enable nss crypto for network communication
  * Force autogen invokation if buildtrunk is defined
  * Whitespace cleanup
  * Stop shipping corosync.conf in favour of a generic example
  * Update file list

* Mon Mar 30 2009 Fabio M. Di Nitto <fdinitto@redhat.com> - 0.95-2
- Backport svn commit 1913 to fix pkgconfig files generation
  and unbreak lvm2 build.

* Tue Mar 24 2009 Fabio M. Di Nitto <fdinitto@redhat.com> - 0.95-1
- New upstream release
- spec file updates:
  * Drop alpha tag
  * Drop local patches (no longer required)
  * Allow to build from svn trunk by supporting rpmbuild --with buildtrunk 
  * BuildRequires autoconf automake if building from trunk
  * Execute autogen.sh if building from trunk and if no configure is available
  * Switch to use rpm configure macro and set standard install paths
  * Build invokation now supports _smp_mflags
  * Remove install section for docs and use proper doc macro instead
  * Add tree fixup bits to drop static libs and html docs (only for now)
  * Add LICENSE file to all subpackages
  * libraries have moved to libdir. Drop ld.so.conf.d corosync file
  * Update BuildRoot usage to preferred versions/names

* Tue Mar 10 2009 Fabio M. Di Nitto <fdinitto@redhat.com> - 0.94-5.svn1797
- Update the corosync-trunk patch for real this time.

* Tue Mar 10 2009 Fabio M. Di Nitto <fdinitto@redhat.com> - 0.94-4.svn1797
- Import fixes from upstream:
  * Cleanup logsys format init around to use default settings (1795)
  * logsys_format_set should use its own internal copy of format_buffer (1796)
  * Add logsys_format_get to logsys API (1797)
- Cherry pick svn1807 to unbreak CPG.

* Mon Mar  9 2009 Fabio M. Di Nitto <fdinitto@redhat.com> - 0.94-3.svn1794
- Import fixes from upstream:
  * Add reserve/release feature to totem message queue space (1793)
  * Fix CG shutdown (1794)

* Fri Mar  6 2009 Fabio M. Di Nitto <fdinitto@redhat.com> - 0.94-2.svn1792
- Import fixes from upstream:
  * Fix uninitialized memory. Spotted by valgrind (1788)
  * Fix logsys_set_format by updating the right bits (1789)
  * logsys: re-add support for timestamp  (1790)
  * Fix cpg crash (1791)
  * Allow logsys_format_set to reset to default (1792)

* Tue Mar  3 2009 Fabio M. Di Nitto <fdinitto@redhat.com> - 0.94-1
- New upstream release.
- Drop obsolete patches.
- Add soname bump patch that was missing from upstream.

* Wed Feb 25 2009 Fabio M. Di Nitto <fdinitto@redhat.com> - 0.93-4
- Add Makefile fix to install all corosync tools (commit r1780)

* Tue Feb 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.93-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Mon Feb 23 2009 Fabio M. Di Nitto <fdinitto@redhat.com> - 0.93-2
- Rename gcc-4.4 patch to match svn commit (r1767).
- Backport patch from trunk (commit r1774) to fix quorum engine.

* Thu Feb 19 2009 Fabio M. Di Nitto <fdinitto@redhat.com> - 0.93-1
- New upstream release.
- Drop alphatag from spec file.
- Drop trunk patch.
- Update Provides for corosynclib-devel.
- Backport gcc-4.4 build fix from trunk.

* Mon Feb  2 2009 Fabio M. Di Nitto <fdinitto@redhat.com> - 0.92-7.svn1756
- Update to svn trunk at revision 1756 from upstream.
- Add support pkgconfig to devel package.
- Tidy up spec files by re-organazing sections according to packages.
- Split libraries from corosync to corosynclib.
- Rename corosync-devel to corosynclib-devel.
- Comply with multiarch requirements (libraries).

* Tue Jan 27 2009 Fabio M. Di Nitto <fdinitto@redhat.com> - 0.92-6.svn1750
- Update to svn trunk at revision 1750 from upstream.
- Include new quorum service in the packaging.

* Mon Dec 15 2008 Fabio M. Di Nitto <fdinitto@redhat.com> - 0.92-5.svn1709
- Update to svn trunk at revision 1709 from upstream.
- Update spec file to include new include files.

* Wed Dec 10 2008 Fabio M. Di Nitto <fdinitto@redhat.com> - 0.92-4.svn1707
- Update to svn trunk at revision 1707 from upstream.
- Update spec file to include new lcrso services and include file.

* Mon Oct 13 2008 Dennis Gilmore <dennis@ausil.us> - 0.92-3
- remove ExclusiveArch line

* Wed Sep 24 2008 Steven Dake <sdake@redhat.com> - 0.92-2
- Add conflicts for openais and openais-devel packages older then 0.90.

* Wed Sep 24 2008 Steven Dake <sdake@redhat.com> - 0.92-1
- New upstream release corosync-0.92.

* Sun Aug 24 2008 Steven Dake <sdake@redhat.com> - 0.91-3
- move logsys_overview.8.* to devel package.
- move shared libs to main package.

* Wed Aug 20 2008 Steven Dake <sdake@redhat.com> - 0.91-2
- use /sbin/service instead of calling init script directly.
- put corosync-objctl man page in the main package.
- change all initrddir to initddir for fedora 10 guidelines.

* Thu Aug 14 2008 Steven Dake <sdake@redhat.com> - 0.91-1
- First upstream packaged version of corosync for rawhide review.
