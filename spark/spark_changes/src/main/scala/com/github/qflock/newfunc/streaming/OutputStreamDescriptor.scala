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
package com.github.qflock.newfunc.streaming

import java.io.OutputStream
import java.nio.ByteBuffer
import java.nio.channels.{Channels, WritableByteChannel}
import java.util.concurrent.ConcurrentLinkedQueue
import scala.collection.mutable



class OutputStreamRecord(var stream: Option[OutputStream]) {

  var channel: Option[WritableByteChannel] = None
  def updateStream(newOutputStream: OutputStream): Unit = {
    stream = Some(newOutputStream)
    channel = Some(Channels.newChannel(newOutputStream))
  }

  var freed: Boolean = true
  private val streamer: DataStreamer = new DataStreamer

  def fill(inputStream: OutputStream): Unit = {
    stream = Some(inputStream)
    updateStream(inputStream)
    freed = false
  }

  def free(): Unit = {
    stream = None
    wroteHeader = false
    freed = true
    streamer.reset
  }
  def bytesStreamed: Long = streamer.bytesStreamed
  def streamsOutstanding: Boolean = streamer.streamsOutstanding
  streamer.start()
  var wroteHeader: Boolean = false
  def writeHeader(byteBuffer: ByteBuffer): Boolean = {
    this.synchronized {
      if (!wroteHeader) {
        wroteHeader = true
        // channel.get.write(byteBuffer)
        stream.get.write(byteBuffer.array())
        stream.get.flush()
        true
      } else false
    }
  }
  def streamAsync(bufferStream: DataStreamItem): Unit = {
    streamer.enqueue(bufferStream)
  }
}

case class OutputStreamDescriptor(requests: Int) {
  private val freeQueue: ConcurrentLinkedQueue[Int] =
    new ConcurrentLinkedQueue[Int]()
  private val requestMap = {
    val requestMap: mutable.HashMap[Int, OutputStreamRecord] =
      new mutable.HashMap[Int, OutputStreamRecord]
    for (i <- 0 until requests) {
      requestMap(i) = new OutputStreamRecord(None)
      freeQueue.add(i)
    }
    requestMap
  }
  def getRequestInfo(requestId: Int): OutputStreamRecord = {
    requestMap(requestId)
  }
  def fillRequestInfo(stream: OutputStream): Int = {
    val requestId = freeQueue.remove()
    val record = requestMap(requestId)
    record.fill(stream)
    requestId
  }
  def freeRequest(requestId: Int): Unit = {
    val request = requestMap(requestId)
    request.free()
    freeQueue.add(requestId)
  }
}

/** This object holds the global state that allows us to
 *  pass objects as parameters to our data source.
 */
object OutputStreamDescriptor {
  private val defaultRequests: Int = 16
  private var descriptor = new OutputStreamDescriptor(defaultRequests)
  def initMap(maxRequests: Int): Unit = {
    descriptor = OutputStreamDescriptor(maxRequests)
  }

  def get: OutputStreamDescriptor = {
    descriptor
  }
}
