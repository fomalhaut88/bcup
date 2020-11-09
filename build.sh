#!/bin/bash

python_interpreter=python3.8

if [[ "$VIRTUAL_ENV" != "" ]]
then
  invenv=1
else
  invenv=0
fi

if [[ $invenv == 0 ]]; then
    if [ ! -d '.venv' ]; then
        echo "Initializing virtualenv..."
        $python_interpreter -m virtualenv .venv
        source .venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
    else
        echo "Activating virtualenv..."
        source .venv/bin/activate
    fi
fi

version=`cat version`

echo "Removing old build and dist..."
rm -rf build
rm -rf dist

echo "Pyinstaller packing..."
pyinstaller bcup.spec --log-level WARN

echo "Compressing into .tar.gz format..."
tar -czvf dist/bcup-$version.tar.gz -C dist bcup

echo "Creating .deb package..."
deb_pkg_dir=dist/bcup-$version

mkdir -p $deb_pkg_dir/DEBIAN
mkdir -p $deb_pkg_dir/usr/bin
mkdir -p $deb_pkg_dir/usr/share/applications
mkdir -p $deb_pkg_dir/usr/share/pixmaps
mkdir -p $deb_pkg_dir/etc/systemd/system
mkdir -p $deb_pkg_dir/etc/bcup
mkdir -p $deb_pkg_dir/var/log/bcup

cp dist/bcup $deb_pkg_dir/usr/bin/
cp linux/control $deb_pkg_dir/DEBIAN/
cp linux/postinst $deb_pkg_dir/DEBIAN/
cp linux/postrm $deb_pkg_dir/DEBIAN/
cp bcup.service $deb_pkg_dir/etc/systemd/system/
cp config-base.yml $deb_pkg_dir/etc/bcup/config.yml

sed -i "s/Version:.*/Version: $version/" $deb_pkg_dir/DEBIAN/control
dpkg-deb --build $deb_pkg_dir
rm -r $deb_pkg_dir

if [[ $invenv == 0 ]]
then
    deactivate
fi

echo "Completed."
