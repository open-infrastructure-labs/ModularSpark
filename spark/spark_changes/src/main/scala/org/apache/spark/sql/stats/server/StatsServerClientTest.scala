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


/**
 *  Tests for the StatsServerClient and StatsServerTableClient.
 */
class ClientTests {
  private val logger = LoggerFactory.getLogger(getClass)

  def testClient(table: String, query: String): Unit = {
    val url = "http://qflock-storage-dc1:9860/stats"
    val client = new StatsServerClient(table, query, url)
    try {
      val inStream = client.getInputStream
      val value = inStream.readDouble()
      logger.info(s"value received: $value")
    } finally client.close()
  }

  def statsTest(): Unit = {
    testClient("store_sales", "")
    testClient("store_sales",
      "SELECT * FROM store_sales WHERE " +
              "( ss_quantity IS NOT NULL AND ss_quantity > '1' )")
    testClient("inventory", "")
    testClient("inventory",
      "SELECT * FROM inventory WHERE " +
              "( inv_quantity_on_hand IS NOT NULL AND inv_quantity_on_hand > '1' )")
    testClient("call_center", "")
    testClient("call_center",
       "SELECT * FROM call_center WHERE " +
               "( cc_call_center_id IS NOT NULL AND cc_call_center_id > '5' )")
  }

  def writeToFile(data: ListBuffer[String],
                  fileName: String): Unit = {
    val tmpFilename = fileName
    val writer = new PrintWriter(new FileOutputStream(
      new File(tmpFilename), true /* append */))
    data.foreach(x => writer.write(x + "\n"))
    writer.close()
  }

  def tablesTest(): Unit = {
    val url = "http://qflock-storage-dc1:9860/stats"
    val client = new StatsServerTableClient(url, "GET_TABLES")
    try {
      val tables = client.getTables
      logger.info(s"value received: $tables")
    } finally client.close()
  }
}

object ClientTest {
  private val logger = LoggerFactory.getLogger(getClass)

  def main(args: scala.Array[String]): Unit = {
    BasicConfigurator.configure()
    val ct = new ClientTests
    val testName = if (args.length == 0) "stats" else args(0)
    testName match {
      case "stats" => ct.statsTest()
      case "tables" => ct.tablesTest()
      case test@_ => logger.warn("Unknown test " + test)
    }
  }
}
