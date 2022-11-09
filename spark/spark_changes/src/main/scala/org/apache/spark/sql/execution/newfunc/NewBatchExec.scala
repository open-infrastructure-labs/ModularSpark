package org.apache.spark.sql.execution.newfunc

import org.apache.spark.api.python.ChainedPythonFunctions
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.catalyst.InternalRow
import org.apache.spark.sql.catalyst.expressions.{AttributeSet, Expression, PythonUDF, UnsafeProjection}
import org.apache.spark.sql.catalyst.plans.physical.Partitioning
import org.apache.spark.sql.execution.UnaryExecNode
import org.apache.spark.sql.execution.python.BatchIterator
import org.apache.spark.{ContextAwareIterator, TaskContext}

trait NewBatchExec extends UnaryExecNode {

  // private val pythonFunction = func.asInstanceOf[PythonUDF].func

//  override def producedAttributes: AttributeSet = AttributeSet(output)

  private val batchSize = conf.arrowMaxRecordsPerBatch

  override def outputPartitioning: Partitioning = child.outputPartitioning

//  override protected def doExecute(): RDD[InternalRow] = {
//    child.execute().mapPartitionsInternal { inputIter =>
//      // Single function with one struct.
//      val argOffsets = Array(Array(0))
//      val chainedFunc = Seq(ChainedPythonFunctions(Seq(pythonFunction)))
//      val sessionLocalTimeZone = conf.sessionLocalTimeZone
//      //      val pythonRunnerConf = ArrowUtils.getPythonRunnerConfMap(conf)
//      val outputTypes = child.schema
//
//      val context = TaskContext.get()
//      val contextAwareIterator = new ContextAwareIterator(context, inputIter)
//
//      // Here we wrap it via another row so that Python sides understand it
//      // as a DataFrame.
//      val wrappedIter = contextAwareIterator.map(InternalRow(_))
//
//      // DO NOT use iter.grouped(). See BatchIterator.
//      val batchIter =
//        if (batchSize > 0) new BatchIterator(wrappedIter, batchSize) else Iterator(wrappedIter)
//
//      //      val columnarBatchIter = new ArrowPythonRunner(
//      //        chainedFunc,
//      //        pythonEvalType,
//      //        argOffsets,
//      //        StructType(StructField("struct", outputTypes) :: Nil),
//      //        sessionLocalTimeZone,
//      //        pythonRunnerConf).compute(batchIter, context.partitionId(), context)
//
//      val unsafeProj = UnsafeProjection.create(output, output)
//
//      //      batchIter.flatMap { batch =>
//      // Scalar Iterator UDF returns a StructType column in ColumnarBatch, select
//      // the children here
//      //        val structVector = batch.column(0).asInstanceOf[ArrowColumnVector]
//      //        val outputVectors = output.indices.map(structVector.getChild)
//      //        val flattenedBatch = new ColumnarBatch(outputVectors.toArray)
//      //        flattenedBatch.setNumRows(batch.numRows())
//      //        flattenedBatch.rowIterator.asScala
//      //      }.map(unsafeProj)
//      inputIter.map(unsafeProj)
//    }
//  }
}
