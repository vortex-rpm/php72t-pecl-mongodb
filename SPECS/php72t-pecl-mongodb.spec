# vortex spec file for php72t-pecl-mongodb, forked from:
# IUS spec file for php72u-pecl-mongodb, forked from:
#
# Fedora spec file for php-pecl-mongodb
# without SCL compatibility, from
#
# remirepo spec file for php-pecl-mongodb
#
# Copyright (c) 2015-2017 Remi Collet
# License: CC-BY-SA
# http://creativecommons.org/licenses/by-sa/4.0/
#
# Please, preserve the changelog entries
#
%global pecl_name  mongodb
# After 40-smbclient.ini, see https://jira.mongodb.org/browse/PHPC-658
%global ini_name   50-%{pecl_name}.ini
%global php        php72t

%bcond_without zts
%bcond_with libbson
%bcond_with libmongoc

Summary:        MongoDB driver for PHP
Name:           %{php}-pecl-%{pecl_name}
Version:        1.4.2
Release:        1.vortex%{?dist}
License:        ASL 2.0
Group:          Development/Languages
URL:            https://pecl.php.net/package/%{pecl_name}
Source0:        https://pecl.php.net/get/%{pecl_name}-%{version}.tgz

BuildRequires:  %{php}-devel
BuildRequires:  %{php}-json
BuildRequires:  cyrus-sasl-devel
BuildRequires:  openssl-devel
%{?with_libbson:BuildRequires: pkgconfig(libbson-1.0) >= 1.9.0}
%{?with_libmongoc:BuildRequires: pkgconfig(libmongoc-1.0) >= 1.9.0}
BuildRequires:  snappy-devel
BuildRequires:  zlib-devel

BuildRequires:  pear1u
# explicitly require pear dependencies to avoid conflicts
BuildRequires:  %{php}-cli
BuildRequires:  %{php}-common
BuildRequires:  %{php}-process
BuildRequires:  %{php}-xml

Requires:       php(zend-abi) = %{php_zend_api}
Requires:       php(api) = %{php_core_api}
Requires:       %{php}-json%{?_isa}

# provide the stock name
Provides:       php-pecl-%{pecl_name} = %{version}
Provides:       php-pecl-%{pecl_name}%{?_isa} = %{version}

# Don't provide php-mongodb which is the pure PHP library

# provide the stock and IUS names in pecl() format
Provides:       php-pecl(%{pecl_name})         = %{version}
Provides:       php-pecl(%{pecl_name})%{?_isa} = %{version}
Provides:       %{php}-pecl(%{pecl_name})         = %{version}
Provides:       %{php}-pecl(%{pecl_name})%{?_isa} = %{version}

# conflict with the stock name
Conflicts:      php-pecl-%{pecl_name} < %{version}

%{?filter_provides_in: %filter_provides_in %{php_extdir}/.*\.so$}
%{?filter_provides_in: %filter_provides_in %{php_ztsextdir}/.*\.so$}
%{?filter_setup}


%description
The purpose of this driver is to provide exceptionally thin glue between
MongoDB and PHP, implementing only fundemental and performance-critical
components necessary to build a fully-functional MongoDB driver.


%prep
%setup -q -c
mv %{pecl_name}-%{version} NTS

# Don't install/register tests and License
sed -e 's/role="test"/role="src"/' \
    -e '/LICENSE/s/role="doc"/role="src"/' \
    -i package.xml

# Sanity check, really often broken
extver=$(sed -n '/#define PHP_MONGODB_VERSION/{s/.* "//;s/".*$//;p}' NTS/php_phongo.h)
if test "x${extver}" != "x%{version}"; then
   : Error: Upstream extension version is ${extver}, expecting %{version}.
   exit 1
fi

%if %{with zts}
# Duplicate source tree for NTS / ZTS build
cp -pr NTS ZTS
%endif

# Create configuration file
cat << 'EOF' | tee %{ini_name}
; Enable %{summary} extension module
extension=%{pecl_name}.so

; Configuration
;mongodb.debug=''
EOF


%build
peclbuild() {
  %{_bindir}/${1}ize

  # Ensure we use system library
  # Need to be removed only after phpize because of m4_include
  %{?with_libbson:rm -r src/libbson}
  %{?with_libmongoc:rm -r src/libmongoc}

  %configure \
    --with-php-config=%{_bindir}/${1}-config \
    %{?_with_libbson} \
    %{?_with_libmongoc} \
    --with-mongodb-sasl \
    --enable-mongodb

  %make_build
}

pushd NTS
peclbuild php
popd

%if %{with zts}
pushd ZTS
peclbuild zts-php
popd
%endif


%install
make -C NTS install INSTALL_ROOT=%{buildroot}
install -D -m 644 %{ini_name} %{buildroot}%{php_inidir}/%{ini_name}

# Install XML package description
install -D -m 644 package.xml %{buildroot}%{pecl_xmldir}/%{pecl_name}.xml

%if %{with zts}
make -C ZTS install INSTALL_ROOT=%{buildroot}
install -D -m 644 %{ini_name} %{buildroot}%{php_ztsinidir}/%{ini_name}
%endif

# Documentation
for i in $(grep 'role="doc"' package.xml | sed -e 's/^.*name="//;s/".*$//')
do install -D -p -m 644 NTS/$i %{buildroot}%{pecl_docdir}/%{pecl_name}/$i
done


%check
OPT="-n"
[ -f %{php_extdir}/json.so ] && OPT="$OPT -d extension=json.so"

: Minimal load test for NTS extension
%{__php} $OPT \
    --define extension=%{buildroot}%{php_extdir}/%{pecl_name}.so \
    --modules | grep %{pecl_name}

%if %{with zts}
: Minimal load test for ZTS extension
%{__ztsphp} $OPT \
    --define extension=%{buildroot}%{php_ztsextdir}/%{pecl_name}.so \
    --modules | grep %{pecl_name}
%endif


%triggerin -- pear1u
if [ -x %{__pecl} ]; then
    %{pecl_install} %{pecl_xmldir}/%{pecl_name}.xml >/dev/null || :
fi


%posttrans
if [ -x %{__pecl} ]; then
    %{pecl_install} %{pecl_xmldir}/%{pecl_name}.xml >/dev/null || :
fi


%postun
if [ $1 -eq 0 -a -x %{__pecl} ]; then
    %{pecl_uninstall} %{pecl_name} >/dev/null || :
fi


%files
%license NTS/LICENSE
%doc %{pecl_docdir}/%{pecl_name}
%{pecl_xmldir}/%{pecl_name}.xml

%config(noreplace) %{php_inidir}/%{ini_name}
%{php_extdir}/%{pecl_name}.so

%if %{with zts}
%config(noreplace) %{php_ztsinidir}/%{ini_name}
%{php_ztsextdir}/%{pecl_name}.so
%endif


%changelog
* Fri Oct 05 2018 Ilya Otyutskiy <ilya.otyutskiy@icloud.com> - 1.4.2-1.vortex
- Rebuilt with php72t

* Wed Mar 07 2018 Ben Harper <ben.harper@rackspace.com> - 1.4.2-1.ius
- Latest upstream

* Wed Feb 21 2018 Ben Harper <ben.harper@rackspace.com> - 1.4.1-1.ius
- Latest upstream
- update libbson and libmongoc version requirements from Fedora:
  https://src.fedoraproject.org/rpms/php-pecl-mongodb/c/0a6ae3aa4027cf545c3f1f8d48938d65e0ee893f
- add with-mongodb-sasl build option from Fedora:
  https://src.fedoraproject.org/rpms/php-pecl-mongodb/c/a75ea22c57ba9de17169b5a0409289754abfc4a3

* Thu Feb 01 2018 Carl George <carl@george.compuoter> - 1.3.4-2.ius
- Remove pear requirement and update scriptlets (adapted from remirepo)

* Tue Jan 30 2018 Ben Harper <ben.harper@rackspace.com> - 1.3.4-1.ius
- port from Fedora

* Sun Dec  3 2017 Remi Collet <remi@remirepo.net> - 1.3.4-1
- Update to 1.3.4

* Wed Nov 22 2017 Remi Collet <remi@remirepo.net> - 1.3.3-1
- Update to 1.3.3

* Tue Oct 31 2017 Remi Collet <remi@remirepo.net> - 1.3.2-1
- Update to 1.3.2

* Tue Oct 17 2017 Remi Collet <remi@remirepo.net> - 1.3.1-1
- update to 1.3.1 (stable)

* Tue Oct 03 2017 Remi Collet <remi@fedoraproject.org> - 1.3.0-2
- rebuild for https://fedoraproject.org/wiki/Changes/php72

* Wed Sep 20 2017 Remi Collet <remi@remirepo.net> - 1.3.0-1
- update to 1.3.0 (stable)

* Fri Sep 15 2017 Remi Collet <remi@remirepo.net> - 1.3.0~RC1-1
- update to 1.3.0RC1
- raise dependency on libbson and mongo-c-driver 1.8.0
- raise dependency on PHP 5.5

* Fri Aug 11 2017 Remi Collet <remi@remirepo.net> - 1.3.0~beta1-1
- update to 1.3.0beta1
- raise dependency on libbson and mongo-c-driver 1.7.0

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.2.9-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.2.9-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Thu May  4 2017 Remi Collet <remi@remirepo.net> - 1.2.9-1
- Update to 1.2.9

* Mon Mar 20 2017 Remi Collet <remi@remirepo.net> - 1.2.8-1
- Update to 1.2.8 (no change)

* Wed Mar 15 2017 Remi Collet <remi@remirepo.net> - 1.2.7-1
- Update to 1.2.7

* Wed Mar  8 2017 Remi Collet <remi@remirepo.net> - 1.2.6-1
- Update to 1.2.6

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.2.5-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Wed Feb  1 2017 Remi Collet <remi@fedoraproject.org> - 1.2.5-1
- update to 1.2.5

* Wed Dec 14 2016 Remi Collet <remi@fedoraproject.org> - 1.2.2-1
- update to 1.2.2

* Thu Dec  8 2016 Remi Collet <remi@fedoraproject.org> - 1.2.1-1
- update to 1.2.1

* Tue Nov 29 2016 Remi Collet <remi@fedoraproject.org> - 1.2.0-1
- update to 1.2.0
- internal dependency on date, json, spl and standard

* Wed Nov 23 2016 Remi Collet <remi@fedoraproject.org> - 1.2.0-0.4.alpha3
- add upstream patch for libbson and mongo-c-driver 1.5.0RC6
- fix FTBFS detected by Koschei

* Mon Nov 14 2016 Remi Collet <remi@fedoraproject.org> - 1.2.0-0.3.alpha3
- rebuild for https://fedoraproject.org/wiki/Changes/php71

* Fri Oct 21 2016 Remi Collet <remi@fedoraproject.org> - 1.2.0-0.2.alpha3
- add upstream patch for libbson and mongo-c-driver 1.5.0RC3
- fix FTBFS detected by Koschei

* Fri Oct 14 2016 Remi Collet <remi@fedoraproject.org> - 1.2.0-0.1.alpha3
- update to 1.2.0alpha3 for libbson and mongo-c-driver 1.5

* Mon Aug 29 2016 Petr Pisar <ppisar@redhat.com> - 1.1.8-4
- Rebuild against libbson-1.4.0 (bug #1361166)

* Tue Jul 19 2016 Remi Collet <remi@fedoraproject.org> - 1.1.8-2
- License is ASL 2.0, from review #1269056

* Wed Jul 06 2016 Remi Collet <remi@fedoraproject.org> - 1.1.8-1
- Update to 1.1.8

* Thu Jun  2 2016 Remi Collet <remi@fedoraproject.org> - 1.1.7-1
- Update to 1.1.7

* Thu Apr  7 2016 Remi Collet <remi@fedoraproject.org> - 1.1.6-1
- Update to 1.1.6

* Thu Mar 31 2016 Remi Collet <remi@fedoraproject.org> - 1.1.5-3
- load after smbclient to workaround
  https://jira.mongodb.org/browse/PHPC-658

* Fri Mar 18 2016 Remi Collet <remi@fedoraproject.org> - 1.1.5-1
- Update to 1.1.5 (stable)

* Thu Mar 10 2016 Remi Collet <remi@fedoraproject.org> - 1.1.4-1
- Update to 1.1.4 (stable)

* Sat Mar  5 2016 Remi Collet <remi@fedoraproject.org> - 1.1.3-1
- Update to 1.1.3 (stable)

* Thu Jan 07 2016 Remi Collet <remi@fedoraproject.org> - 1.1.2-1
- Update to 1.1.2 (stable)

* Thu Dec 31 2015 Remi Collet <remi@fedoraproject.org> - 1.1.1-3
- fix patch for 32bits build
  open https://github.com/mongodb/mongo-php-driver/pull/191

* Sat Dec 26 2015 Remi Collet <remi@fedoraproject.org> - 1.1.1-1
- Update to 1.1.1 (stable)
- add patch for 32bits build,
  open https://github.com/mongodb/mongo-php-driver/pull/185

* Wed Dec 16 2015 Remi Collet <remi@fedoraproject.org> - 1.1.0-1
- Update to 1.1.0 (stable)
- raise dependency on libmongoc >= 1.3.0

* Tue Dec  8 2015 Remi Collet <remi@fedoraproject.org> - 1.0.1-1
- update to 1.0.1 (stable)
- ensure libmongoc >= 1.2.0 and < 1.3 is used

* Fri Oct 30 2015 Remi Collet <remi@fedoraproject.org> - 1.0.0-1
- update to 1.0.0 (stable)

* Tue Oct 27 2015 Remi Collet <remi@fedoraproject.org> - 1.0.0-0.6.RC0
- Update to 1.0.0RC0 (beta)

* Tue Oct  6 2015 Remi Collet <remi@fedoraproject.org> - 1.0.0-0.4-beta2
- drop SCL compatibility for Fedora

* Tue Oct  6 2015 Remi Collet <remi@fedoraproject.org> - 1.0.0-0.3-beta2
- Update to 1.0.0beta2 (beta)

* Fri Sep 11 2015 Remi Collet <remi@fedoraproject.org> - 1.0.0-0.2-beta1
- Update to 1.0.0beta1 (beta)

* Mon Aug 31 2015 Remi Collet <remi@fedoraproject.org> - 1.0.0-0.1.alpha2
- Update to 1.0.0alpha2 (alpha)
- buid with system libmongoc

* Thu May 07 2015 Remi Collet <remi@fedoraproject.org> - 0.6.3-1
- Update to 0.6.3 (alpha)

* Wed May 06 2015 Remi Collet <remi@fedoraproject.org> - 0.6.2-1
- Update to 0.6.2 (alpha)

* Wed May 06 2015 Remi Collet <remi@fedoraproject.org> - 0.6.0-1
- Update to 0.6.0 (alpha)

* Sat Apr 25 2015 Remi Collet <remi@fedoraproject.org> - 0.5.1-1
- Update to 0.5.1 (alpha)

* Thu Apr 23 2015 Remi Collet <remi@fedoraproject.org> - 0.5.0-2
- build with system libbson
- open https://jira.mongodb.org/browse/PHPC-259

* Wed Apr 22 2015 Remi Collet <remi@fedoraproject.org> - 0.5.0-1
- initial package, version 0.5.0 (alpha)

