package org.apache.spark.sql.execution.python

import scala.collection.JavaConverters._
import org.apache.hadoop.shaded.javax.xml.bind.DatatypeConverter
import org.apache.spark.SparkFiles
import org.apache.spark.api.python.{PythonBroadcast, PythonEvalType, PythonFunction}
import org.apache.spark.broadcast.Broadcast
import org.apache.spark.sql.catalyst.expressions.PythonUDF
import org.apache.spark.sql.types.{LongType, StructField, StructType}
import org.slf4j.LoggerFactory

import scala.sys.process.{Process, ProcessLogger}

object PythonReader {
  private val logger = LoggerFactory.getLogger(getClass)

  def getFunctionString(param: String): String = {
    val rootPath = SparkFiles.getRootDirectory() + "/pydike_venv"
    val pythonPath = "/build/spark-3.3.0/pyspark-3.3.0/"
    val pythonExec = s"${rootPath}/bin/python"
    val sparkDriverPath = "lib/python3.8/site-packages/pydike/client/spark_driver.py"
    val pythonCmd = s"$pythonExec ${rootPath}/${sparkDriverPath}"
    val stdout = new StringBuilder
    val stderr = new StringBuilder
    //    val status = Process(s"$pythonCmd", None,
    //      "PYTHONPATH" -> pythonPath) ! ProcessLogger(stdout append _, stderr append _)
    val status = Process(s"python3 /qflock/spark/spark_changes/scripts/spark_function.py", None,
      "PYTHONPATH" -> pythonPath) ! ProcessLogger(stdout append _, stderr append _)
    logger.info(s"python status: $status")
    logger.info(s"python stdout: ${stdout.toString}")
    logger.info(s"python stderr: ${stderr.toString}")
    stdout.toString()
  }
  def getFunction(param: String): PythonFunction = {
    val function = DatatypeConverter.parseHexBinary(getFunctionString(param))
    val workerEnv = new java.util.HashMap[String, String]()
    workerEnv.put("PYTHONHASHSEED", "0")
    // val curDir = System.getProperty("user.dir")
    // logger.info(s"current working directory: ${curDir}")
    // val rootPath = SparkFiles.getRootDirectory() + "/pydike_venv"
    val rootPath = "/usr"
    val func = PythonFunction(
      command = function,
      envVars = workerEnv,
      pythonIncludes = List.empty[String].asJava,
      pythonExec = s"${rootPath}/bin/python",
      pythonVer = "3.8",
      broadcastVars = List.empty[Broadcast[PythonBroadcast]].asJava,
      accumulator = null)
    func
  }

  def getPythonFunc(param: String): PythonUDF =
    PythonUDF("newFuncPythonUDF",
      getFunction(param),
      StructType(Seq(StructField("a", LongType))),
      Seq.empty,
      PythonEvalType.SQL_MAP_PANDAS_ITER_UDF,
      true)
}
