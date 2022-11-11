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
package org.apache.spark.sql
package stats.server

import java.io.{File, FileOutputStream, PrintWriter}

import scala.collection.mutable.ListBuffer

import org.apache.log4j.BasicConfigurator
import org.slf4j.LoggerFactory


class ClientTests {
  private val logger = LoggerFactory.getLogger(getClass)

//  def getSparkSession: SparkSession = {
//    logger.info(s"create new session")
//    SparkSession
//      .builder
//      .master("local")
//      .appName("qflock-jdbc")
//      .config("spark.local.dir", "/tmp/spark-temp")
//      .enableHiveSupport()
//      .getOrCreate()
//  }
//
//  private val spark = getSparkSession
//  spark.sparkContext.setLogLevel("INFO")

  def getStats(table: String, filter: String): Unit = {
    val url = "http://qflock-storage-dc1:9860/stats"
    val client = new StatsServerClient(table, filter, url)
    try {
      val inStream = client.getInputStream
      val value = inStream.readDouble()
      logger.info(s"value received: $value")
    } finally client.close()
  }
  def getStatsTest(): Unit = {
    getStats("store_sales", "")
  }
  def getTablesTest(): Unit = {
    val url = "http://qflock-storage-dc1:9860/stats"
    val client = new StatsServerTableClient(url, "GET_TABLES")
    try {
      val tables = client.getTables
      logger.info(s"tables received: ${tables.mkString(", ")}")
    }
    finally client.close()
  }

  def writeToFile(data: ListBuffer[String],
                  fileName: String): Unit = {
    val tmpFilename = fileName
    val writer = new PrintWriter(new FileOutputStream(
      new File(tmpFilename), true /* append */))
    data.foreach(x => writer.write(x + "\n"))
    writer.close()
  }
}

object ClientTest {
  private val logger = LoggerFactory.getLogger(getClass)

  def main(args: scala.Array[String]): Unit = {
    BasicConfigurator.configure()
    val ct = new ClientTests
    val testName = if (args.length == 0) "stats" else args(0)
    testName match {
      case "stats" => ct.getStatsTest()
      case "tables" => ct.getTablesTest()
      case test@_ => logger.warn("Unknown test " + test)
    }
  }
}
