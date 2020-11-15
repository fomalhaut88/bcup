# bcup

A service for Linux to make backups. The configuration is stored in `config.yml` where you can specify the source and target folders and
some other customizations. The goals of the solution are the simplicity to configure and several ways to backup that include data compression and
efficient storing all versions of the files.

## Configuration

The configuration YML-file is stored at `/etc/bcup/config.yml`. Here is how it looks like:

```yml
format: Ymd.HMS.f
sources:
  - source: /home/user/Folder1
    target: /media/Data/Bcup
    period: 86400
    method: full
    compress: false
    limit: 10
  - source: /home/user/Folder2
    target: /media/Data/Bcup
    period: 86400
    method: last
    compress: true
  - source: /home/user/Folder3
    target: /media/Data/Bcup
    period: 3600
    method: diff
    compress: true
```

At the moment there are 3 ways to backup. The parameter is named **method**.

1. **full** - it copies the source if it changed and keeps the stored files before.
2. **last** - same as **full** but keeps the last copy only.
3. **diff** - it stores only the files that have been changed, added or removed (differences), 
so the space on the disk is used efficiently keeping the change history of each file.

Parameter **source** is the path to the directory that is to backup.

Parameter **target** is the target directory where the backup files will be stored.

Parameter **period** is the period in seconds between the runs of backup algorithm.

Parameter **compress** shows the need to compress the backup files with **tar.gz**. If the method is set to **diff**, 
the last backup is never compress, this is done to increse the performance.

Parameter **limit** is the number of recent backups that are stored, extra ones will be removed by the algorithm when a new backup happens. 
The limit is infinite if it is not set or set to `null`. **limit** is not relevant for the method **full**.

When you modified `/etc/bcup/config.yml` do not forget to restart the service to apply changed:

```
sudo service bcup restart
```

## Installation from source

It is supposed you have got Python 3.8 interpreter installed and it is available as **python3.8** in command line.

Step 1. Download the source code from here:

```
git clone https://github.com/fomalhaut88/bcup.git --depth 1
cd bcup
```

Step 2. Build:

```
./build.sh
```

Step 3. Install from the built deb-file:

```
sudo dpkg -i dist/bcup-1.0.deb
```

Step 4. Configure your backups:

```
sudo nano /etc/bcup/config.yml
```

Step 5: Restart the service when you made the changes in the config file:

```
sudo service bcup restart
```

## Logging

The logs are available in `/var/log/bcup/error.log`.
