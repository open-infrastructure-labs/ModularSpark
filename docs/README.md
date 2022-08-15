Modular Spark Documentation
===========================
# Overview
Spark is a unified analytics engine for large-scale data processing. It provides high-level APIs in Scala, Java, Python, and R, and an optimized engine that supports general computation graphs for data analysis. It also supports a rich set of higher-level tools including Spark SQL for SQL and DataFrames, pandas API on Spark for pandas workloads, MLlib for machine learning, GraphX for graph processing, and Structured Streaming for stream processing.
## Key areas to improve
* Spark is complex and not flexible
* Spark is slow to adopt new hardware (GPU, DPU, TPU, etc.)
* Sparks internal interfaces are “private” and impossible to expand or reuse
# Objectives
* Provide performance optimization package for Spark to allow dynamic adoption of optimization techniques based on hardware capabilities of cluster nodes.
* Create custom Datasources (v1/v2) to allow seamless job execution between Datacenters and Clouds
* A logical plan is a tree that represents both schema and data. 
  These trees are manipulated and optimized by catalyst framework. 
  We will create cluster capabilities aware Logical and Physical planing Rules to improve hardware and Cloud utilization and overall performance
* Create asyncronous scheduler to better utilize local hardware of Spark workers.

# Components
## Datasource
## Scheduler
## Catalist framework (Logical and Physical planning Rules)

# Tool
## Class Loaders [ClassLoader](tools/ClassLoader/README.md)
