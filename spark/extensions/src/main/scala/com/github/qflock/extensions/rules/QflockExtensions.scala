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
package com.github.qflock.extensions.rules

import java.io.FileWriter

import com.github.qflock.extensions.rules.parse.QflockSqlParser
import org.slf4j.{Logger, LoggerFactory}

import org.apache.spark.sql.{SparkSession, SparkSessionExtensions}
import org.apache.spark.sql.catalyst.plans.logical.LogicalPlan
import org.apache.spark.sql.catalyst.rules.Rule

case class QflockBasicRule(spark: SparkSession) extends Rule[LogicalPlan] {
  protected val logger: Logger = LoggerFactory.getLogger(getClass)
  override def apply(plan: LogicalPlan): LogicalPlan = {
    logger.info(s"QflockRule LogicalPlan $plan")
    // We will append to the existing file.
    val fw = new FileWriter("./rules.txt", true)
    try {
      fw.write(plan.toString() + "\n")
    }
    finally fw.close()
    plan
  }
}
object QflockBasicOptimizationRule extends Rule[LogicalPlan] {
  val spark: SparkSession =
    SparkSession.builder().appName("Extra optimization rules")
      .getOrCreate()
  def apply(logicalPlan: LogicalPlan): LogicalPlan = {
    QflockBasicRule(spark).apply(logicalPlan)
  }
}
object QflockBasicRuleBuilder {
  var injected: Boolean = false
  protected val logger: Logger = LoggerFactory.getLogger(getClass)
  def injectExtraOptimization(): Unit = {
    val testSparkSession: SparkSession =
      SparkSession.builder().appName("Extra optimization rules")
        .getOrCreate()
    import testSparkSession.implicits._
    testSparkSession.experimental.extraOptimizations = Seq(QflockBasicOptimizationRule)

    logger.info(s"added QflockBasicRule to session $testSparkSession")
  }
}

class QflockBasicRuleExtensions extends (SparkSessionExtensions => Unit) {
  def apply(e: SparkSessionExtensions): Unit = {
    e.injectOptimizerRule(QflockBasicRule)
    e.injectParser { (session, parser) =>
      new QflockSqlParser(parser)
    }
  }
}

class QflockExplainExtensions extends (SparkSessionExtensions => Unit) {
  def apply(e: SparkSessionExtensions): Unit = {
    e.injectOptimizerRule(QflockExplainRule)
  }
}

class QflockExtensions extends (SparkSessionExtensions => Unit) {
  def apply(e: SparkSessionExtensions): Unit = {
    e.injectOptimizerRule(QflockRemoteRule)
  }
}
