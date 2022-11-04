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
package com.github.qflock.newfunc.server

import java.io.{File, FileOutputStream, PrintWriter, StringWriter}
import javax.json.Json

import scala.collection.mutable.ListBuffer

// import com.github.qflock.extensions.remote.{QflockRemoteClient, QflockRemoteColVectReader}
import org.apache.log4j.BasicConfigurator
import org.slf4j.LoggerFactory

//import org.apache.spark.sql.hive.extension.ExtHiveUtils
import org.apache.spark.sql.types._


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

  def runQuery(function: String, schema: StructType): ListBuffer[String] = {
    val url = "http://10.124.48.63:9860/function"
    val client = new FuncServerClient(function, schema, url)
    var data = ListBuffer.empty[String]
    try {
      // data = readData(schema, 1024, client)
    } finally client.close()
    data
  }
  def funcTest1(): Unit = {
    val schema = StructType(Array(
    StructField("name", StringType, nullable = true)
  ))
    runQuery("function", schema)
  }
//  def readData(schema: StructType,
//               inputBatchSize: Int,
//               client: FuncServerClient): ListBuffer[String] = {
//    val data: ListBuffer[String] = ListBuffer.empty[String]
//    val batchSize = if (schema.fields.length > 10) 256 * 1024 else inputBatchSize
//    val reader = new QflockRemoteColVectReader(schema, batchSize, "", client)
//    while (reader.next()) {
//      val batch = reader.get()
//      val rowIterator = batch.rowIterator()
//      while (rowIterator.hasNext) {
//        val row = rowIterator.next()
//        val values = schema.fields.zipWithIndex.map(s => s._1.dataType match {
//          case LongType => row.getLong(s._2)
//          case DoubleType => row.getDouble(s._2)
//          case StringType => row.getUTF8String(s._2)
//        })
//        // scalastyle:off println
//        data += values.mkString(",")
//        // scalastyle:on println
//      }
//    }
//    reader.close()
//    data
//  }

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
    val testName = if (args.length == 0) "1" else args(0)
    testName match {
      case "1" => ct.funcTest1()
      case test@_ => logger.warn("Unknown test " + test)
    }
  }
}
