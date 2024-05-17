Name:		shibboleth-embedded-ds
Version:	1.2.1
Release:	1
Summary:	Client-side federation discovery service for SAML-based SSO
Group:		Productivity/Networking/Security
Vendor:		Shibboleth Consortium
License:	Apache-2.0
URL:		http://shibboleth.net/
Source:		%{name}-%{version}.tar.gz
BuildArch:	noarch
BuildRoot:	%{_tmppath}/%{name}-%{version}-root
%if "%{_vendor}" == "redhat"
BuildRequires: redhat-rpm-config
%{!?_without_builtinapache:BuildRequires: httpd}
%endif
%if "%{_vendor}" == "suse"
%{!?_without_builtinapache:BuildRequires: apache2}
%endif

%description
The Embedded Discovery Service is a JS/CSS/HTML-based tool for
identity provider selection in conjunction with SAML-based web
single sign-on implementations such as Shibboleth.

%prep
%setup -q

%build


%install
%{__make} install DESTDIR=$RPM_BUILD_ROOT

# Plug the DS into the built-in Apache on a recognized system.
touch rpm.filelist
APACHE_CONFIG="shibboleth-ds.conf"
%{?_without_builtinapache:APACHE_CONFIG="no"}
if [ "$APACHE_CONFIG" != "no" ] ; then
    APACHE_CONFD="no"
    if [ -d %{_sysconfdir}/httpd/conf.d ] ; then
            APACHE_CONFD="%{_sysconfdir}/httpd/conf.d"
    fi
    if [ -d %{_sysconfdir}/apache2/conf.d ] ; then
            APACHE_CONFD="%{_sysconfdir}/apache2/conf.d"
    fi
    if [ "$APACHE_CONFD" != "no" ] ; then
        %{__mkdir} -p $RPM_BUILD_ROOT$APACHE_CONFD
        %{__cp} -p $RPM_BUILD_ROOT%{_sysconfdir}/shibboleth-ds/$APACHE_CONFIG $RPM_BUILD_ROOT$APACHE_CONFD/$APACHE_CONFIG 
        echo "%config(noreplace) $APACHE_CONFD/$APACHE_CONFIG" > rpm.filelist
    fi
fi

%clean
[ "$RPM_BUILD_ROOT" != "/" ] && %{__rm} -rf $RPM_BUILD_ROOT

%post
%if "%{_vendor}" == "redhat"
	# On upgrade, restart components if they're already running.
    if [ "$1" -gt "1" ] ; then
        %{!?_without_builtinapache:/sbin/service httpd status 1>/dev/null && /sbin/service httpd restart 1>/dev/null}
        exit 0
    fi
%endif

%preun
%if "%{_vendor}" == "redhat"
	if [ "$1" = 0 ] ; then
        %{!?_without_builtinapache:/sbin/service httpd status 1>/dev/null && /sbin/service httpd restart 1>/dev/null}
	fi
%endif
%if "%{_vendor}" == "suse"
    if [ "$1" = 0 ] ; then
        %{!?_without_builtinapache:/sbin/service apache2 status 1>/dev/null && /sbin/service apache2 restart 1>/dev/null}
    fi
%endif
exit 0

%postun
%if "%{_vendor}" == "suse"
cd /
%{!?_without_builtinapache:%restart_on_update apache2}
%endif

%files -f rpm.filelist
%defattr(-,root,root,-)
%dir %{_sysconfdir}/shibboleth-ds
%{_sysconfdir}/shibboleth-ds/*.txt
%{_sysconfdir}/shibboleth-ds/*.gif
%config(noreplace) %{_sysconfdir}/shibboleth-ds/index.html
%config(noreplace) %{_sysconfdir}/shibboleth-ds/idpselect.css
%config(noreplace) %{_sysconfdir}/shibboleth-ds/idpselect_config.js
%config %{_sysconfdir}/shibboleth-ds/idpselect.js
%config %{_sysconfdir}/shibboleth-ds/shibboleth-ds.conf

%changelog
* Mon Jun 6 2016 Scott Cantor <cantor.2@osu.edu> - 1.2.0-1
- Update version
- Fix license name

* Wed Apr 29 2015  Scott Cantor  <cantor.2@osu.edu>  - 1.1.0-1
- Update version
- Stop marking text files as configs
- Add gif to package

* Mon Apr 11 2011  Scott Cantor  <cantor.2@osu.edu>  - 1.0-1
- First version.
