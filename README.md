<p align="center">
    <img width="183px" src="https://raw.githubusercontent.com/nav/dbviz/master/docs/img/dbviz-light.png" alt='DBviz'>
</p>
<p align="center">
    <em>A tool to visualize databases.</em>
</p>

---

# DBviz

DBviz is a tool to visualize databases. It works by introspecting the given database to
generate a [dot diagram](https://graphviz.org/doc/info/lang.html), and representing it
as HTML. The main reason this tool was built was because I couldn't easily find an
existing tool that would allow me to pick a specific table and show its relationships.

Currently, it only works with MySQL based databases.

## Requirements

Python 3.9+

Graphviz

## Installation

```shell
$ make install
```

## Usage

1. Start the server by running:

```shell
$ make run
```

2. Go to [http://localhost:8000](http://localhost:8000) in your browser and enter database credentials.

3. Select the table you would like to visualize.

## Demo

![DBViz Demo](https://raw.githubusercontent.com/nav/dbviz/master/docs/img/demo.gif)

<p align="center">&mdash;</p>
<p align="center"><i>DBviz is <a href="https://github.com/nav/dbviz/blob/master/LICENSE">MIT licensed</a> code.</i></p>
