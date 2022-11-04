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

package org.apache.spark.sql.execution.newfunc

import java.io.{DataInputStream, OutputStream}

import com.github.qflock.newfunc.server.FuncServerClient
import com.github.qflock.newfunc.streaming.{OutputStreamDescriptor, RemoteDataWriter}
import org.slf4j.LoggerFactory

import org.apache.spark.{ContextAwareIterator, TaskContext}
import org.apache.spark.api.python.{ChainedPythonFunctions, PythonEvalType}
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.catalyst.InternalRow
import org.apache.spark.sql.catalyst.plans.physical.Partitioning
import org.apache.spark.sql.catalyst.expressions._
import org.apache.spark.sql.execution.SparkPlan


/**
 * This relation is the Physical object for the NewFunction logical object.
 * This takes a child and sends that data to a
 */
case class NewFuncCommandExec(param: Option[String],
                              func: Expression,
                              child: SparkPlan)
  extends NewBatchExec { // extends MapInBatchExec {

  private val logger = LoggerFactory.getLogger(getClass)
  val output: Seq[Attribute] = child.output // func.dataType.asInstanceOf[StructType].toAttributes

  private val batchSize = conf.arrowMaxRecordsPerBatch

  override def outputPartitioning: Partitioning = child.outputPartitioning
  override protected def withNewChildInternal(newChild: SparkPlan): NewFuncCommandExec =
    copy(child = newChild)
  private val client: FuncServerClient = new FuncServerClient("test",
                                                               output.toStructType,
                                                      "http://10.124.48.63:9860")
  // private val inputStream: DataInputStream = client.getInputStream()
  private val outputStream: OutputStream = client.getOutputStream()
  override protected def doExecute(): RDD[InternalRow] = {
    val writeRequestId = OutputStreamDescriptor.get.fillRequestInfo(outputStream)
    val desc = OutputStreamDescriptor.get.getRequestInfo(writeRequestId)
    if (desc.wroteHeader) {
      throw new IllegalStateException("descriptor stat is not valid.")
    }
    val writer = new RemoteDataWriter(0, 0, output.toStructType, requestId = writeRequestId)
    child.execute().mapPartitionsInternal { inputIter =>
      val unsafeProj = UnsafeProjection.create(output, output)
      val rows = inputIter //.map(unsafeProj)
      rows.foreach {
        row => writer.write(row)
      }
      rows
    }
  }
}
