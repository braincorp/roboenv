robustus
=======

Tool to make and configure python virtualenv, setup necessary packages and cache them if necessary.

### Prerequesties
* python 2.7
* virtualenv
* pytest (for testing)

### Usage
First you need to create virtual environment. Robustus will automatically look
for [katipo](https://github.com/braincorp/katipo) assembly file and add paths
to mentioned repositories.

    robustus env <dir> --cache <binary package dir> <other virtualenv options>

Afterwards you can go to env directory and install packages using usual pip syntax.
Robustus will store binary packages in 'wheelhouse' directory, you can change it
using --cache option during creation of environment.

    robustus install numpy==1.7.2
    robustus install -r <requirements file>
    robustus install <other pip options>

You can specify binary package cache where to install package.

    robustus --cache ~/wheelhouse install numpy==1.7.2

You may also install non pip packages, e.g. opencv or cudamat. Robustus has
platform specific scripts to setup them.

You may also want to reuse existing binary package cache. You can do that by
downloading cache directory before installing packages. Robustus has convenience
command to do that. Cache can be stored as a directory or *.tar.gz, *.tar.bz or
*.zip archive.

    robustus download-cache <cache url>

In the same manner you can upload cache.
  
    robustus upload-cache <cache url>
    robustus --cache ~/wheelhouse upload-cache <cache url>

Make sure that binary package cache is suitable for your platform. It is highly
recommended to use cached packages only on the machine there they have been compiled.
