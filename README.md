# Computational Management of Data – Project

The software handles two types of data:
- **Bibliographic metadata** (JSON) → stored in a relational database (SQLite)
- **Citation data** (CSV) → stored in a graph database (Blazegraph)


## Requirements

### Python
Python 3.x is required. Install the dependencies with:
```bash
pip install -r requirements.txt
```

The following libraries are used:
- `pandas` — data manipulation and relational database queries
- `rdflib` — building and uploading RDF graphs to Blazegraph
- `sparql-dataframe` — querying Blazegraph via SPARQL

### Java & Blazegraph
Blazegraph is required as the graph database backend.

1. Make sure Java is installed on your machine
2. Download `blazegraph.jar` from:
   https://github.com/blazegraph/database/releases/tag/BLAZEGRAPH_2_1_6_RC
3. Place the file in the project root directory
4. Start the server before running any code:
```bash
java -server -Xmx4g -jar blazegraph.jar
```
The SPARQL endpoint will be available at `http://127.0.0.1:9999/blazegraph/sparql`.


## Running Tests

```bash
python -m unittest test.py -v
```
