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

import java.io._
import java.net.{HttpURLConnection, URL}
import java.nio.ByteBuffer
import javax.json.Json

import com.github.qflock.newfunc.server.ModSparkClient
import org.slf4j.LoggerFactory


class StatsServerClient(table: String,
                        filter: String,
                        urlPath: String) extends ModSparkClient {
  private val logger = LoggerFactory.getLogger(getClass)

  override def toString: String = {
    s"StatsServerClient $table $filter"
  }
  private def getJson(table: String, filter: String): String = {
    val queryBuilder = Json.createObjectBuilder()
    queryBuilder.add("table", table)
    queryBuilder.add("filter", filter)
    val queryJson = queryBuilder.build
    val stringWriter = new StringWriter
    val writer = Json.createWriter(stringWriter)
    writer.writeObject(queryJson)
    stringWriter.getBuffer.toString
  }
  def getEmptyQueryStream: DataInputStream = {
    // Write a header with a column number of 0.
    val b = ByteBuffer.allocate(4)
    b.putInt(0)
    val s = new DataInputStream(new ByteArrayInputStream(b.array()))
    s
  }
  private val connection: Option[HttpURLConnection] = getConnection
  def close(): Unit = {
    if (connection.isDefined) {
      //      logger.info("close start")
      if (stream.isDefined) {
        stream.get.close()
      }
      connection.get.disconnect()
      //      logger.info("close end")
    }
  }
  private var stream: Option[DataInputStream] = None
  def getStream: DataInputStream = stream.get
  def getOutputStream: OutputStream = connection.get.getOutputStream
  def getConnection: Option[HttpURLConnection] = {
    //    logger.info(s"opening stream to: $tableName $rgOffset $rgCount")
    val url = new URL(urlPath)
    val con = url.openConnection.asInstanceOf[HttpURLConnection]
    con.setRequestMethod("POST")
    con.setRequestProperty("Accept", "application/json")
    val jsonString = getJson(table, filter)
    con.setRequestProperty("request-json", jsonString)
    con.setChunkedStreamingMode(4096) // .getBytes("utf-8")
    con.setDoOutput(true)
    con.setDoInput(true)
    con.setReadTimeout(0)
    con.setConnectTimeout(0)
    con.connect()
    logger.info("Connection opened to: " + urlPath)
    Some(con)
  }
  def getInputStream: DataInputStream = {
    val con = connection.get
    val statusCode = con.getResponseCode
    stream = Some(if (statusCode == 200) {
      //      logger.info(s"opening stream done $tableName $rgOffset $rgCount")
      new DataInputStream(new BufferedInputStream(con.getInputStream))
    } else {
      logger.error(s"unexpected http status on connect: $statusCode")
      getEmptyQueryStream
    })
    stream.get
  }
}
