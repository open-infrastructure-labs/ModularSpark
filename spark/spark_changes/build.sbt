/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
name := "modular-spark"

organization := ""
version := "0.1.0"
scalaVersion := "2.12.10"
publishTo := Some(Resolver.file("file", new File("/build/releases")))
javacOptions ++= Seq("-source", "1.8", "-target", "1.8")

enablePlugins(Antlr4Plugin)
Antlr4 / antlr4GenListener := true
Antlr4 / antlr4GenVisitor := true
Antlr4 / antlr4Version := "4.8-1"
Antlr4 / antlr4PackageName := Some("org.apache.spark.sql.catalyst.parser")


libraryDependencies ++= Seq(
  "org.apache.commons" % "commons-csv" % "1.8",
  "org.apache.httpcomponents" % "httpcore" % "4.4.11",
  "org.slf4j" % "slf4j-api" % "1.7.32" % "provided",
  "org.mockito" % "mockito-core" % "2.0.31-beta",
)
libraryDependencies += "org.scala-lang.modules" %% "scala-xml" % "2.0.0-M3"
libraryDependencies += "org.scalatest" %% "scalatest" % "3.2.2" % "test"
libraryDependencies += "org.apache.commons" % "commons-lang3" % "3.10" % "test"

libraryDependencies ++= Seq(
  "org.scala-lang" % "scala-library" % scalaVersion.value % "compile",
)
// Libraries for the ndp client.
libraryDependencies ++= Seq(
  "org.apache.hadoop" % "hadoop-client" % "3.2.2",
  // "org.slf4j" % "slf4j-simple" % "1.7.21" % Test,
  "org.apache.logging.log4j" % "log4j-api" % "2.17.2",
  "org.apache.logging.log4j" % "log4j-core" % "2.17.2",
  "org.json" % "json" % "20210307",
  "javax.json" % "javax.json-api" % "1.1.4",
  // "org.glassfish" % "javax.json" % "1.1.4",
  "com.github.luben" % "zstd-jni" % "1.5.0-4",
)


