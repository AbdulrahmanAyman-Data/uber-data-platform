#!/bin/bash

# Start SSH Service
echo "Starting SSH service..."
/usr/sbin/sshd -D &

# Ensure correct ownership of HDFS directories
# NOTE (fix): dfs.namenode.name.dir / dfs.datanode.data.dir in hdfs-site.xml
# point to /opt/hadoop/dfs/{name,data} — chowning /opt/hadoop/hdfs (a
# different, unrelated path) was a no-op for the actual NameNode/DataNode
# storage dirs and left them root-owned, which made the NameNode process
# die silently on startup (running as the hdfs user, unable to write to
# its own storage directory).
echo "Setting ownership for HDFS directories..."
chown -R hdfs:hadoop /opt/hadoop/dfs
chown -R hdfs:hadoop /opt/hadoop/hdfs 2>/dev/null || true

# Ensure Java is available
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

# Format the NameNode on first-ever start only (if its storage dir is empty).
# Safe to leave in permanently: once formatted, the VERSION file exists and
# this block is skipped on every subsequent container start/restart.
if [ ! -d "/opt/hadoop/dfs/name/current" ]; then
    echo "NameNode storage not found — formatting for first-time setup..."
    su - hdfs -c "/opt/hadoop/bin/hdfs namenode -format -force -nonInteractive"
fi

# Start Hadoop Services as hdfs user
echo "Starting HDFS..."
su - hdfs -c "/opt/hadoop/sbin/start-dfs.sh"

echo "Starting YARN..."
su - hdfs -c "/opt/hadoop/sbin/start-yarn.sh"

# Keep the container running while monitoring logs
echo "Hadoop services are running. Keeping container alive..."
exec tail -f /opt/hadoop/logs/*.log
