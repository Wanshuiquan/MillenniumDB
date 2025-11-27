This is the artifact for paper [url], which is build on MillenniumDB. MillenniumDB is a graph oriented database management system developed by the [Millennium Institute for Foundational Research on Data (IMFD)](https://imfd.cl/).  
 
The main objective of this project is to create a functional constraint database. This project supports property graphs as graph models. 

This project is still in active development and is not production ready yet, some functionality is missing and there may be bugs.


Table of Contents
================================================================================
- [Property Graphs](#property-graph-model)
- [Project Build](#project-build)
- [Import Data](#import-data)
- [Run Experiments](#run-experiments)



# [Property Graph Model](#millenniumdb)
The definition of the graph model and how to create a graph file is explained [here](doc/quad_model/data_model.md).
The query language is inspired on Cypher and its defined [here](doc/quad_model/query_language.md).



[Project build](#millenniumdb)
================================================================================
MillenniumDB should be able to be built on any x86-64 Linux distribution.
On windows, Windows Subsystem for Linux (WSL) can be used. MacOS is supported if using a Mac chip.
For Mac with Intel chips or Windows without WSL, Docker can be used: see [Docker](#docker).


Install Dependencies:
--------------------------------------------------------------------------------
MillenniumDB needs the following dependencies:
- GCC >= 8.1
- CMake >= 3.12
- Git
- libssl
- ncursesw and less for the CLI
- Python >= 3.8 with venv to run tests
- Boost 1.82

On current Debian and Ubuntu based distributions they can be installed by running:
```bash
sudo apt update && sudo apt install git g++ cmake libssl-dev libncurses-dev less python3 python3-venv libicu-dev
```

On mac:
```bash
brew install cmake ncurses openssl@3 icu4c
```

Clone the repository
--------------------------------------------------------------------------------
 Clone this repository, enter the repository root directory and set `MDB_HOME`:
```bash
git clone git@github.com:MillenniumDB/MillenniumDB.git
cd MillenniumDB
export MDB_HOME=$(pwd)
```


Install Boost
--------------------------------------------------------------------------------
Download [`boost_1_82_0.tar.gz`](https://archives.boost.io/release/1.82.0/source/boost_1_82_0.tar.gz) using a browser or wget:
```bash
wget -q --show-progress https://archives.boost.io/release/1.82.0/source/boost_1_82_0.tar.gz
```

and run the following in the directory where boost was downloaded:
```bash
tar -xf boost_1_82_0.tar.gz
mkdir -p $MDB_HOME/third_party/boost_1_82/include
mv boost_1_82_0/boost $MDB_HOME/third_party/boost_1_82/include
rm -r boost_1_82_0.tar.gz boost_1_82_0
```

Install Z3
-----------------------------------------------------------------------------------
Download z3 from [`z3 repository'](https://github.com/Z3Prover/z3) and enter the repository directory
```bash 
    git clone https://github.com/Z3Prover/z3.git
    cd z3
```

and run the following
```bash 
    python scripts/mk_make.py
    cd build
    make
    sudo make install
```

Build the Project:
--------------------------------------------------------------------------------
Go back into the repository root directory and configure and build MillenniumDB:
```bash
cmake -Bbuild/Release -DCMAKE_BUILD_TYPE=Release && cmake --build build/Release/
```
To use multiple cores during compilation (much faster) use the following command and replace `<n>` with the desired number of threads:
```bash
cmake -Bbuild/Release -DCMAKE_BUILD_TYPE=Release && cmake --build build/Release/ -j <n>
```

[Import Data](#import-data)
=================================================

Source Dataset
-------------------------------
We have store the dataset used for bench mark in the following repositories of Zenodo 


The directory to store data is ```evaluation/data```

Create Databases 
--------------------------
After download `all' datasets, please run the following commands to create databases. 

```bash 
    build/Release/bin/mdb-import evaluation/data/icij-leak.qm evaluation/database/icij-leak &&
    build/Release/bin/mdb-import evaluation/data/icij-paradise.qm evaluation/database/paradise &&
    build/Release/bin/mdb-import evaluation/data/soc-pokec.qm evaluation/database/pokec &&
    build/Release/bin/mdb-import evaluation/data/telecom.qm evaluation/database/telecom &&
    build/Release/bin/mdb-import evaluation/data/ldbc01.qm evaluation/database/ldbc01 &&
    build/Release/bin/mdb-import evaluation/data/ldbc10.qm evaluation/database/ldbc10 

```

[Run Experiments](#run-experiments)
================================================================================

Run Experiments
---------------
You may run the experiment by 
```bash
./run-benchmark <dataset>
```

```<dataset>``` includes `icijleak', 'paradise', 'ldbc01', 'ldbc10', 'pokec', 'telecom'


Results
---------------------------
Each iteration of an experiment over a dataset will produce two directories,  ```evaluation/directory/<dataset>``` stores 
the data of optimized algorithm, and ```evaluation/directory/<dataset>-naive``` stores the statistics of the naive algorithm, for each directory,
there are three files:

1. statics.csv contain the statistics of each query  
2. results.csv contain the query results
3. z3_debug.log contain the statistics regarding the smt solver 



<!-- 
Results Visible
----------------------------------
You can visualize the results 
MillenniumDB supports two database formats: RDF and QuadModel. A RDF database can only be queried with SPARQL and a QuadModel database can only be queried with MQL. In this document we will focus on RDF/SPARQL.


Creating a Database
--------------------------------------------------------------------------------
```bash
build/Release/bin/mdb-import <data-file> <db-directory> [--prefixes <prefixes-file>]
```
- `<data-file>` is the path to the file containing the data to import, using the [Turtle](https://www.w3.org/TR/turtle/) format for RDF, or [QuadModel Format](doc/quad_model/data_model.md#import-format) for Property Graphs.
- `<db-directory>` is the path of the directory where the new database will be created.
- `--prefixes <prefixes-file>` is an optional path to a prefixes file (used only when using RDF).

### Prefix Definitions
The optional prefixes file passed using the `--prefixes` option contains one prefix per line. Each line consists of a prefix alias and the prefix itself:

```
http://www.myprefix.com/
https://other.prefix.com/foo
https://other.prefix.com/bar
```

Using a prefix file is optional, but helps reduce the space occupied by IRIs in the database when using the RDF model. MillenniumDB generates IDs for each prefix, and when importing IRIs into the database replaces any prefixes with IDs. For large databases this can safe a significant amount of space. The total number of user defined prefixes cannot exceed 255.


Querying a Database
--------------------------------------------------------------------------------
We implement the typical client/server model, so in order to query a database, you need to have a server running and then send queries to it.

### Run the Server
To run the server use the following command, passing the `<db-directory>` where the database was created:
```bash
build/Release/bin/mdb-server <db-directory>
```

**IMPORTANT:** we supposing you execute the server from the root directory of this repository (`MDB_HOME`). If you execute the server from another directory, the web server won't be available unless set the environment variable `MDB_BROWSER` is `$MDB_HOME/browser`.

### Execute a Query
The easiest way to run a query is to use the Web Browser at http://localhost:4321/ after starting the server.

The other option is sending the query via HTTP request.

The MillenniumDB SPARQL server supports all three query operations specified in the [SPARQL 1.1 Protocol](https://www.w3.org/TR/2013/REC-sparql11-protocol-20130321/#query-operation):
- `query via GET`
- `query via URL-encoded POST`
- `query via POST directly`

When using Property Graphs, we expect an HTTP POST where query is contained in the request body.

We provide a script to make queries using curl.
To use it you have to pass a file with the query as a parameter:
```bash
bash scripts/query <query-file>
```

where `<query-file>` is the path to a file containing a query in SPARQL format.

For updates, we have an analogous script:
```bash
bash scripts/update <query-file>
```


[Example](#millenniumdb)
================================================================================
This is a step by step example of creating a database, running the server and making a query.
To run this example MillenniumDB has to be [built](#project-build) first.


Create an Example Database
--------------------------------------------------------------------------------
From the repository root directory run the following command to create the example database:
```bash
build/Release/bin/mdb-import data/example-rdf-database.ttl data/example-rdf-database
```
That should have created the directory `data/example-rdf-database` containing a database initialized with the data from `data/example-rdf-database.ttl`.


Launch the Server
--------------------------------------------------------------------------------
The server can now be launched with the previously created database:
```
build/Release/bin/mdb-server data/example-rdf-database
```


Execute a Query
--------------------------------------------------------------------------------
Go to http://localhost:4321/

Remove the Database
--------------------------------------------------------------------------------
To remove the database that was created just delete the directory:
```bash
rm -r data/example-rdf-database
```



[Docker](#millenniumdb)
================================================================================
We also supply a Dockerfile to build and run MillenniumDB using Docker.


Build the Docker Image
--------------------------------------------------------------------------------
To build a Docker image of MillenniumDB run the following:
```bash
docker build -t mdb .
```


Creating a Database
--------------------------------------------------------------------------------
Put any `.ttl` files into the `data` directory and from the repository root directory run:
```bash
docker run --rm --volume "$PWD"/data:/data mdb \
    mdb-import \
    /data/example-rdf-database.ttl \
    /data/example-rdf-database
```

You can change `/data/example-rdf-database.ttl` to the path of of your `.ttl` and
`/data/example-rdf-database` to the directory where you want the database to be
created. The `.ttl` files and database directories have to be inside `data`. The `.ttl`
file must not be a symbolic link to a `.ttl` file but a real one. Also the `.ttl` file must exist or else the DB will be created empty.

Running a Server
--------------------------------------------------------------------------------
To run the server with the previously created database use:
```bash
docker run --rm --volume "$PWD"/data:/data -p 1234:1234 -p 4321:4321 mdb \
    mdb-server /data/example-rdf-database
```


Executing a Query
--------------------------------------------------------------------------------
Go to http://localhost:4321/ to see the web interface (available while running the server).

Also we provide a script to make queries using the console:

```bash

Creating a Database
--------------------------------------------------------------------------------
```bash
build/Release/bin/mdb-import <data-file> <db-directory> [--prefixes <prefixes-file>]
```
- `<data-file>` is the path to the file containing the data to import, using the [Turtle](https://www.w3.org/TR/turtle/) format for RDF, or [QuadModel Format](doc/quad_model/data_model.md#import-format) for Property Graphs.
- `<db-directory>` is the path of the directory where the new database will be created.
- `--prefixes <prefixes-file>` is an optional path to a prefixes file (used only when using RDF).

### Prefix Definitions
The optional prefixes file passed using the `--prefixes` option contains one prefix per line. Each line consists of a prefix alias and the prefix itself:

```
http://www.myprefix.com/
https://other.prefix.com/foo
https://other.prefix.com/bar
```

Using a prefix file is optional, but helps reduce the space occupied by IRIs in the database when using the RDF model. MillenniumDB generates IDs for each prefix, and when importing IRIs into the database replaces any prefixes with IDs. For large databases this can safe a significant amount of space. The total number of user defined prefixes cannot exceed 255.


Querying a Database
--------------------------------------------------------------------------------
We implement the typical client/server model, so in order to query a database, you need to have a server running and then send queries to it.

### Run the Server
To run the server use the following command, passing the `<db-directory>` where the database was created:
```bash
build/Release/bin/mdb-server <db-directory>
```

**IMPORTANT:** we supposing you execute the server from the root directory of this repository (`MDB_HOME`). If you execute the server from another directory, the web server won't be available unless set the environment variable `MDB_BROWSER` is `$MDB_HOME/browser`.

### Execute a Query
The easiest way to run a query is to use the Web Browser at http://localhost:4321/ after starting the server.

The other option is sending the query via HTTP request.

The MillenniumDB SPARQL server supports all three query operations specified in the [SPARQL 1.1 Protocol](https://www.w3.org/TR/2013/REC-sparql11-protocol-20130321/#query-operation):
- `query via GET`
- `query via URL-encoded POST`
- `query via POST directly`

When using Property Graphs, we expect an HTTP POST where query is contained in the request body.

We provide a script to make queries using curl.
To use it you have to pass a file with the query as a parameter:
```bash
bash scripts/query <query-file>
```

where `<query-file>` is the path to a file containing a query in SPARQL format.

For updates, we have an analogous script:
```bash
bash scripts/update <query-file>
```


[Example](#millenniumdb)
================================================================================
This is a step by step example of creating a database, running the server and making a query.
To run this example MillenniumDB has to be [built](#project-build) first.


Create an Example Database
--------------------------------------------------------------------------------
From the repository root directory run the following command to create the example database:
```bash
build/Release/bin/mdb-import data/example-rdf-database.ttl data/example-rdf-database
```
That should have created the directory `data/example-rdf-database` containing a database initialized with the data from `data/example-rdf-database.ttl`.


Launch the Server
--------------------------------------------------------------------------------
The server can now be launched with the previously created database:
```
build/Release/bin/mdb-server data/example-rdf-database
```


Execute a Query
--------------------------------------------------------------------------------
Go to http://localhost:4321/

Remove the Database
--------------------------------------------------------------------------------
To remove the database that was created just delete the directory:
```bash
rm -r data/example-rdf-database
```



[Docker](#millenniumdb)
================================================================================
We also supply a Dockerfile to build and run MillenniumDB using Docker.


Build the Docker Image
--------------------------------------------------------------------------------
To build a Docker image of MillenniumDB run the following:
```bash
docker build -t mdb .
```


Creating a Database
--------------------------------------------------------------------------------
Put any `.ttl` files into the `data` directory and from the repository root directory run:
```bash
docker run --rm --volume "$PWD"/data:/data mdb \
    mdb-import \
    /data/example-rdf-database.ttl \
    /data/example-rdf-database
```

You can change `/data/example-rdf-database.ttl` to the path of of your `.ttl` and
`/data/example-rdf-database` to the directory where you want the database to be
created. The `.ttl` files and database directories have to be inside `data`. The `.ttl`
file must not be a symbolic link to a `.ttl` file but a real one. Also the `.ttl` file must exist or else the DB will be created empty.

Running a Server
--------------------------------------------------------------------------------
To run the server with the previously created database use:
```bash
docker run --rm --volume "$PWD"/data:/data -p 1234:1234 -p 4321:4321 mdb \
    mdb-server /data/example-rdf-database
```


Executing a Query
--------------------------------------------------------------------------------
Go to http://localhost:4321/ to see the web interface (available while running the server).

Also we provide a script to make queries using the console:

```bash
bash scripts/query <query-file>
```


Remove the Database
--------------------------------------------------------------------------------
To remove the database that was created just delete the directory:
```bash
rm -r data/example-rdf-database
```
Depending on your Docker configuration you may have to use sudo. -->
<!-- 
feasible solution 
solvable reasonable on average with 1s, 
on the meantime  


QF_LRA + theory of equality + support by major solvers 

Ref NL-Complete Sipser + no more complocated than graph reachbility 

NL-Complete avoid quantifier-elimination combined complexity is polynomial  P - NP 

data complexity: input query 

combined- complexity: input query + 

solvability
maximazition 
linear program + LP solver 

macro state 
-->