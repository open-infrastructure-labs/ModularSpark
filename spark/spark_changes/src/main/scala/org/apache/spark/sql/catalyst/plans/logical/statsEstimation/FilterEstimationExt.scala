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
package catalyst.plans.logical.statsEstimation

import catalyst.catalog.CatalogTable
import catalyst.expressions._
import catalyst.plans.logical._
import catalyst.plans.logical.statsEstimation.EstimationUtils._
import execution.datasources.LogicalRelation
import execution.datasources.v2.DataSourceV2ScanRelation
import org.slf4j.{Logger, LoggerFactory}
import stats.server.{StatsServerClient, StatsServerTableClient}

import org.apache.spark.internal.Logging

case class FilterEstimationExt(plan: Filter) extends Logging {

  protected val logger: Logger = LoggerFactory.getLogger(getClass)
  private val childStats = plan.child.stats

  private val colStatsMap = ColumnStatsMap(childStats.attributeStats)

  private val catalogTable: Option[CatalogTable] = {
    plan.child match {
      case DataSourceV2ScanRelation(_, scan, _, _) =>
        scan match {
          case s: LogicalRelation => s.catalogTable
          case _ => None
        }
      case s: LogicalRelation => s.catalogTable
      case _ => None
    }
  }
  private val tableName: String = catalogTable.get.identifier.table
  private val sparkSession: SparkSession = SparkSession.builder().getOrCreate()
  private val statsServerUrl = sparkSession.conf.get("spark.custom.statsserver", "")
  private val validTables = getValidTables
  private def getValidTables: Seq[String] = {
    val client = new StatsServerTableClient(s"http://$statsServerUrl", "GET_TABLES")
    val tables = try {
     client.getTables
    } finally client.close()
    val tableString = tables.mkString(" ")
    logger.info(s"tables received from http://$statsServerUrl}: $tableString")
    tables
  }
  private def canFilter: Boolean = {
    // The buffers for the strings contain nulls as well.  Eliminate the nulls for comparison.
    val normalizedTables = validTables.map(s => s.slice(0, tableName.length))
    normalizedTables.contains(tableName)
  }
  /**
   * Returns an option of Statistics for a Filter logical plan node.
   * For a given compound expression condition, this method computes filter selectivity
   * (or the percentage of rows meeting the filter condition), which
   * is used to compute row count, size in bytes, and the updated statistics after a given
   * predicated is applied.
   *
   * @return Option[Statistics] When there is no statistics collected, it returns None.
   */
  def estimate: Option[Statistics] = {
    // If this table is not available for filtering, then we return None.
    if (childStats.rowCount.isEmpty || !canFilter) return None

    // Estimate selectivity of this filter predicate, and update column stats if needed.
    // For not-supported condition, set filter selectivity to a conservative estimate 100%
    val filterSelectivity = calculateFilterSelectivity(plan.condition).getOrElse(1.0)

    val filteredRowCount: BigInt = ceil(BigDecimal(childStats.rowCount.get) * filterSelectivity)
    val newColStats = if (filteredRowCount == 0) {
      // The output is empty, we don't need to keep column stats.
      AttributeMap[ColumnStat](Nil)
    } else {
      colStatsMap.outputColumnStats(rowsBeforeFilter = childStats.rowCount.get,
        rowsAfterFilter = filteredRowCount)
    }
    val filteredSizeInBytes: BigInt = getOutputSize(plan.output, filteredRowCount, newColStats)

    Some(childStats.copy(sizeInBytes = filteredSizeInBytes, rowCount = Some(filteredRowCount),
      attributeStats = newColStats))
  }

  private def calculateFilterSelectivity(filter: Expression): Option[Double] = {
    // Parse the objects to generate the query (sqlGen.query).
    val sqlGen = StatsSqlGeneration(filter.references.toSeq.toStructType,
                                    Seq(filter),
                                    Array.empty[String],
                                    tableName)
    logger.info(s"checking selectivity of ${sqlGen.query} " +
                s"from http://$statsServerUrl}")
    // Reach out to server to get selectivity.
    val client = new StatsServerClient(tableName, sqlGen.query, s"http://$statsServerUrl")
    val selectivity = try {
      val inStream = client.getInputStream
      inStream.readDouble()
    } finally client.close()
    logger.info(s"selectivity received from http://$statsServerUrl}: $selectivity")
    Some(selectivity)
  }
}

