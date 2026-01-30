# Practice 2 · Accessing and Managing HDFS with PyArrow

## Summary & Goals
- Prepared the user environment (`.venv`, `requirements.txt`) described in `p2.ipynb` to develop Python clients that read/write HDFS through `pyarrow.fs`.
- Implemented `filesystem_cat.py` (a drop-in replacement for `hdfs dfs -cat` that understands `hdfs://` and `file://` URIs) and `copy_half_file.py` to copy the lower half of any file across heterogeneous filesystems.
- Took the administrator role (`hdadmin`) to practice namespace quotas with `hdfs dfsadmin`, audit the cluster via `hdfs fsck`, simulate DataNode failures, and recover by onboarding a new node.

## Supporting Files
- `p2.ipynb`: step-by-step guide for the virtual environment, environment variables, and operational tasks.
- `filesystem_cat.py`: final script that streams any PyArrow-readable file (local or HDFS) to STDOUT.
- `copy_half_file.py`: script that leverages `FileInfo`, `seek()`, and `shutil.copyfileobj` to copy the last N/2 bytes from source (`a.txt`, `t.txt` examples included) to a destination URI.
- `requirements.txt`: dependency pins (`pyarrow`, `hdfs`, etc.).
- `tcdm_pr2.pdf`: report with screenshots covering script executions, namespace quota enforcement, consecutive `fsck` runs, and the replication status after adding `datanode6`.

## Runtime Environment
- **`namenode` container**: executed scripts as `luser` and administrative commands as `hdadmin`, all inside the cluster created in Practice 1.
- **Python 3 + virtualenv**: `python3 -m venv ~/.venv`, activation via `. ~/.venv/bin/activate`, and `CLASSPATH="$(hadoop classpath --glob):$CLASSPATH"` so PyArrow can load Hadoop jars.
- **Test data**: sample text files (`a.txt`, `t.txt`) live in `/user/luser` on HDFS; administrative commands operate over the entire namespace (`hdfs dfs -put`, `hdfs dfsadmin -setQuota`).

## Technologies & Theory in Action
- **HDFS as a distributed filesystem**: `filesystem_cat.py` uses `FileSystem.from_uri` to hide protocol differences and stream data regardless of physical block placement, showcasing HDFS’s POSIX-like façade over replicated 128 MB blocks.
- **Namespaces & quotas**: the four-inode limit from `tcdm_pr2.pdf` highlights that the directory itself consumes quota, clarifying the distinction between namespace and space quotas.
- **Metadata governance with `dfsadmin`**: running `hdfs dfsadmin -report` after killing `datanode2`/`datanode3` showed 48 under-replicated blocks, reinforcing how replication factor ties directly to resilience.
- **`hdfs fsck` diagnostics**: inspecting `random_words.txt.bz2` after failures confirmed that files remain readable as long as at least one replica survives, aligning with HDFS fault-tolerance theory.
- **Recovery through expansion**: onboarding `datanode6` and repeating `fsck` demonstrated automatic rebalancing until the replication factor returned to its configured value.

## Lessons Learned
Working with PyArrow atop HDFS forced me to internalize what the NameNode really does: when you deliberately break nodes or trip quotas, you see that metadata is as critical as raw blocks. I can now quickly determine whether an issue stems from namespace limits or replica health, and I have reusable Python clients to check the system without relying solely on the traditional CLI.
