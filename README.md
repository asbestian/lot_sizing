About
-----
This repository implements different mixed integer programming (mip) formulations for the discrete, 
single-machine, multi-item, single-level [lot sizing problem](./doc/problem\_description.pdf). 

A mathematical description of those mip formulations is available in [mip_formulations.pdf](./doc/mip\_formulations.pdf) 
in the `doc` folder.

Further information is also available at [OptimizationHub](https://opthub.uniud.it/problem/lsp).

Installation
------------
Source code requires `python3.6` (or later versions).

In `root` directory: `python3 -m pip install -r requirements.txt`

Execution
-------------------------
In `root` directory: `python3 main.py -f input_file.txt`

Run `python3 main.py -h` to see command line options.

Unit tests
---------
In `root` directory: `python3 -m unittest discover test -v`

Documentation
--------------
In `doc` directory: `make html` 

The html documentation can then be found in `doc/build/html`.

Authors
-------
[Sebastian Schenker](https://asbestian.github.io)

