# ClassLoader
## Overview
* Spark is written in Scala and compiles to Java Bytecode
* Java Bytecode loaded and executed inside JVM 
* JVM natively supports custom class loaders [ClassLoader](https://docs.oracle.com/javase/7/docs/api/java/lang/ClassLoader.html?is-external=true)
* Use custom ClassLoader to overwrite a subset of Spark classes
* Some Spark components from a particular release copied to ModularSpark repo and enhanced to support new functionality while fully supporting Spark API 
* This allows dynamic / runtime control of code execution and features for a particular set of applications.
