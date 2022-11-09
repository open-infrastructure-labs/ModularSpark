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
package org.apache.spark.sql.catalyst.plans.logical

import org.apache.spark.sql.{Row, SparkSession}
import org.apache.spark.sql.catalyst.TableIdentifier
import org.apache.spark.sql.catalyst.expressions.{Attribute, AttributeReference}
import org.apache.spark.sql.catalyst.trees.TreePattern
import org.apache.spark.sql.execution.command.LeafRunnableCommand
import org.apache.spark.sql.types.{DoubleType, LongType, StringType}

/**
 * The `NEWFUNC` command implementation for Spark SQL. Example SQL:
 * {{{
 *    NEWFUNC ('/path/to/dir' | delta.`/path/to/dir`) [WHERE number] [DRY RUN];
 * }}}
 */
case class NFuncCommand(param: Option[String],
                        number: Option[Double]
                       ) extends LeafRunnableCommand {

  override val output: Seq[Attribute] =
    Seq(AttributeReference("param", StringType, nullable = true)(),
        AttributeReference("number", DoubleType, nullable = true)(),
        AttributeReference("result", LongType, nullable = true)())

  override def run(sparkSession: SparkSession): Seq[Row] = {
    if (param.isEmpty || number.isEmpty) {
      Seq(Row.fromSeq(Seq("emptyPath", 1.42, 44L)))
    } else {
      Seq(Row.fromSeq(Seq(param.get, number.get, 42L)))
    }
  }
}
/**
 * The `NEWFUNC` command implementation for Spark SQL. Example SQL:
 * {{{
 *    NEWFUNC ('/path/to/dir' | delta.`/path/to/dir`) [WHERE number] [DRY RUN];
 * }}}
 */

object NewFuncCommand {
  val testValue=42
}