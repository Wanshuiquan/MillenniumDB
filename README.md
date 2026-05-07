# MillenniumDB

MillenniumDB is a **graph oriented database management system** developed by the [Millennium Institute for Foundational Research on Data (IMFD)](https://imfd.cl/).

The main objective of this project is to create a fully functional and easy-to-extend DBMS that serves as the basis for testing new techniques and algorithms related to databases and graphs. We support multiple graph models and query languages:

- RDF, with a fairly complete support for the SPARQL 1.1 standard. See [this document](https://github.com/MillenniumDB/MillenniumDB/wiki/SPARQL-Implementation-Status) for more info.
- We have two models for property graphs:

  - Property Graphs with a single edge label and directed edges only, with a custom Cypher-like language (we call this Quad Model or QM in the docs).

  - Property Graphs specified by the GQL Standard (undirected edges, 0-N edge labels), with an early implementation of GQL, still missing a lot of functionality and optimizations.

This project is still in active development and is not production ready yet, some functionality is missing and there may be bugs.

To learn more about MillenniumDB and how to use it, see our [Wiki](https://github.com/MillenniumDB/MillenniumDB/wiki).


_______________
what to do 
I want you to run benchmark on the new added feature based on /evaluation
but you need to open a new directory

you need to do the following things

1.convert each .qm file such that each numeric attribute is a interger, you need to inspect the file structure and notice the maximal memory usage
2. run benchmark on the converted .qm file and record the result with LIA(Linear Integer Arithmetic) and NIA(Nonlinear Integer Arithmetic) separately, for LIA, you can just choose a make sense interger value to replace each occured decimal, for NIA, if there is only minus/plus, you should replace minus/plus with multiplication, otherwise, you need to replace plus by multiplication 

3. You need to compare if our optimization outperforms the naive version

4. note, you should have the benchmark thread running with nohup, such that in case I leave the terminal 