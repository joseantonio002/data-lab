# Practice 1 · Manual Deployment of a Hadoop 3 Cluster

## Summary & Goals
- Built a reusable Ubuntu 22.04 + OpenJDK 8 + Hadoop 3.3.4 base image (`hadoop-base`) following `p1.ipynb`, then instantiated every cluster node from that Docker image.
- From that base, deployed a NameNode/ResourceManager reachable on ports 9870/8088, initialized its metadata directories, and validated the installation with `hadoop-mapreduce-examples`.
- Extended the initial layout (1 NameNode + 4 DataNodes) by adding a BackupNode and the YARN TimelineServer, tested adding/removing DataNodes/NodeManagers, and enabled rack awareness to prove fault tolerance and balanced replica placement.

## Runtime Environment
- **Dockerized cluster**: everything runs on a Linux host with Docker Engine; every Hadoop role is a container attached to the custom `hadoop-cluster` network described in `p1.ipynb`.
- **`hadoop-base` image**: derived from `ubuntu:latest`, adds OpenJDK 8, Python 3, Maven, locale settings, and Hadoop itself; finalized via `docker container commit hadoop-install hadoop-base`.
- **Users and permissions**: `hdadmin` owns the Hadoop daemons, while `luser` submits MapReduce jobs. NameNode data directories (`/var/data/hdfs/namenode`) are prepared with `chown hdadmin:hadoop` to avoid permission issues.
- **Exposed services**: NameNode (`namenode:9000/9870`), ResourceManager (`resourcemanager:8088`), BackupNode UI, and TimelineServer endpoints (all captured inside the PDF).

## Technologies & Theory in Action
- **Hadoop coordination**: tuned `core-site.xml` (default FS, temp dirs) and `mapred-site.xml` (`mapreduce.framework.name=yarn`) so every job launched by `luser` routes through YARN.
- **HDFS internals**: configured `dfs.replication=3`, `dfs.blocksize=64m`, and `dfs.namenode.name.dir`. Adding/removing DataNodes validated how the NameNode tracks block metadata and how `hdfs balancer` redistributes replicas.
- **BackupNode & checkpoints**: demonstrated how the BackupNode keeps a near-real-time copy of `fsimage` and edits, providing a safety net consistent with NameNode theory.
- **YARN & TimelineServer**: separated scheduling (ResourceManager) from execution (NodeManagers) and persisted job histories via the TimelineServer, using the `QuasiMonteCarlo` example to capture metrics.
- **Rack awareness**: crafted `topology.data`/`topology.script.file.name` so Hadoop places replicas across racks, illustrating the theoretical benefits for fault domains.

## Lessons Learned
Meticulous documentation highlighted how fragile a cluster can be without consistent image builds. Exporting `JAVA_HOME`, separating daemon vs. user accounts, and cleaning SSH artifacts all affect stability. Iterating on the deployment clarified how HDFS and YARN bootstrap together and which dashboards/checkpoints to monitor before trusting the cluster.
