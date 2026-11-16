# Fabric Notebook Code: Utilities/init_session

"""
NBA Live Data Platform - Session Initialization Utility
Notebook: Utilities/init_session

Purpose:
- Initialize Spark session with optimal configuration
- Set up logging
- Configure lakehouse and schemas
- Provide common utilities for all notebooks

This notebook should be called via %run at the beginning of every other notebook
Usage: 
"""

# Cell 1: Configure Spark Session for Optimal Performance
# =======================================================

# Spark session configuration
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.sql.shuffle.partitions", "200")

# Delta Lake optimization
spark.conf.set("spark.microsoft.delta.optimizeWrite.enabled", "true")

# Performance tuning
spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "true")
spark.conf.set("spark.sql.broadcastTimeout", "36000")

# Cell 2: Verify Lakehouse Connection
# ====================================

try:
    # Test connection to default lakehouse
    spark.sql("SELECT 1 as test_connection").collect()
    print("✅ Lakehouse connected successfully")
    
    # Get lakehouse info
    context = notebookutils.runtime.context
    workspace_id = context.get("currentWorkspaceId", "UNKNOWN")
    workspace_name = context.get("workspaceName", "UNKNOWN")
    
    print(f"   Workspace: {workspace_name} (ID: {workspace_id})")
    
except Exception as e:
    print(f"❌ Lakehouse connection failed: {str(e)}")
    raise


# Cell 3: Lakehouse Schema Support
# ================================

import uuid


def lakehouse_is_schema_enabled() -> bool:
    probe_schema = f"_schema_probe_{uuid.uuid4().hex}"
    try:
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {probe_schema}")
        spark.sql(f"DROP SCHEMA IF EXISTS {probe_schema}")
        return True
    except Exception as exc:
        if "Feature not supported on Apache Spark in Microsoft Fabric" in str(exc):
            return False
        raise


LAKEHOUSE_SCHEMA_ENABLED = lakehouse_is_schema_enabled()
if LAKEHOUSE_SCHEMA_ENABLED:
    for schema_name in ("bronze", "silver", "gold"):
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")


def lakehouse_table_name(layer: str, table: str) -> str:
    if layer not in {"bronze", "silver", "gold"} or not table.isidentifier():
        raise ValueError(f"Invalid lakehouse table name: {layer}.{table}")
    return f"{layer}.{table}" if LAKEHOUSE_SCHEMA_ENABLED else f"{layer}_{table}"


print(f"Lakehouse schema-enabled: {LAKEHOUSE_SCHEMA_ENABLED}")


# Cell 4: Common Utility Functions
# ================================

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class ExecutionLogger:
    """
    Production-grade execution logger.
    
    Features:
    - Timestamps for all operations
    - Structured logging with context
    - Performance metrics
    """
    
    def __init__(self, notebook_name: str):
        self.notebook_name = notebook_name
        self.logger = logging.getLogger(notebook_name)
        self.start_time = datetime.now()
        self.metrics = {}
    
    def info(self, message: str, **kwargs):
        """Log info with context."""
        context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        full_msg = f"{message}" + (f" [{context}]" if context else "")
        self.logger.info(full_msg)
    
    def warning(self, message: str, **kwargs):
        """Log warning with context."""
        context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        full_msg = f"{message}" + (f" [{context}]" if context else "")
        self.logger.warning(full_msg)
    
    def error(self, message: str, **kwargs):
        """Log error with context."""
        context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
        full_msg = f"{message}" + (f" [{context}]" if context else "")
        self.logger.error(full_msg)
    
    def metric(self, metric_name: str, value: Any):
        """Record a metric for reporting."""
        self.metrics[metric_name] = value
    
    def elapsed_seconds(self) -> float:
        """Get elapsed time since logger creation."""
        return (datetime.now() - self.start_time).total_seconds()
    
    def summary(self) -> Dict[str, Any]:
        """Get execution summary."""
        return {
            "notebook": self.notebook_name,
            "elapsed_seconds": self.elapsed_seconds(),
            "metrics": self.metrics,
            "timestamp": datetime.now().isoformat()
        }


class DataFrameUtils:
    """
    Utility functions for DataFrame operations.
    """
    
    @staticmethod
    def get_row_count(df, table_name: str = "") -> int:
        """
        Get row count with logging.
        
        Args:
            df: Spark DataFrame
            table_name: Optional name for logging
            
        Returns:
            Row count
        """
        count = df.count()
        if table_name:
            logging.info(f"{table_name}: {count:,} rows")
        return count
    
    @staticmethod
    def show_sample(df, n_rows: int = 5, truncate: bool = True):
        """
        Display sample rows.
        
        Args:
            df: Spark DataFrame
            n_rows: Number of rows to show
            truncate: Truncate long columns
        """
        df.limit(n_rows).show(truncate=truncate)
    
    @staticmethod
    def get_schema_info(df) -> List[Tuple[str, str, bool]]:
        """
        Get schema information.
        
        Returns:
            List of (column_name, data_type, nullable)
        """
        return [(field.name, field.dataType.simpleString(), field.nullable)
                for field in df.schema.fields]
    
    @staticmethod
    def check_nulls(df) -> Dict[str, int]:
        """
        Check null counts per column.
        
        Returns:
            Dictionary with column -> null_count
        """
        from pyspark.sql import functions as F
        
        null_counts = {}
        for column in df.columns:
            null_count = df.filter(F.col(column).isNull()).count()
            if null_count > 0:
                null_counts[column] = null_count
        
        return null_counts


class FileSystemUtils:
    """
    Utilities for OneLake file operations.
    """
    
    @staticmethod
    def list_files(path: str) -> List[str]:
        """
        List files in OneLake directory.
        
        Args:
            path: OneLake path (e.g., "/Files/data")
            
        Returns:
            List of file names
        """
        files = notebookutils.fs.ls(path)
        return [f.name for f in files]
    
    @staticmethod
    def read_json_file(path: str) -> Optional[Dict[str, Any]]:
        """
        Read JSON file from OneLake.
        
        Args:
            path: Full path to JSON file
            
        Returns:
            Parsed JSON object. Raises on file or parse errors.
        """
        data = json.loads(notebookutils.fs.head(path, 10 * 1024 * 1024))
        if not isinstance(data, dict):
            raise TypeError(f"Expected a JSON object in {path}")
        return data
    
    @staticmethod
    def write_json_file(path: str, data: Dict[str, Any]):
        """
        Write JSON file to OneLake.
        
        Args:
            path: Full path to JSON file
            data: Dictionary to serialize
        """
        notebookutils.fs.put(path, json.dumps(data, indent=2), True)
        logging.info(f"Wrote JSON to {path}")


class TableUtils:
    """
    Utilities for table operations.
    """
    
    @staticmethod
    def table_exists(schema: str, table: str) -> bool:
        """
        Check if table exists.
        
        Args:
            schema: Schema name
            table: Table name
            
        Returns:
            True if table exists
        """
        return spark.catalog.tableExists(lakehouse_table_name(schema, table))
    
    @staticmethod
    def get_table_stats(schema: str, table: str) -> Dict[str, Any]:
        """
        Get table statistics.
        
        Args:
            schema: Schema name
            table: Table name
            
        Returns:
            Dictionary with row count, size, columns
        """
        full_name = lakehouse_table_name(schema, table)
        df = spark.table(full_name)
        row_count = df.count()
        column_count = len(df.columns)
        
        return {
            "table": full_name,
            "row_count": row_count,
            "column_count": column_count,
            "columns": df.columns,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def drop_table_safe(schema: str, table: str):
        """
        Safely drop table (dev only).
        
        Args:
            schema: Schema name
            table: Table name
        """
        full_name = lakehouse_table_name(schema, table)
        spark.sql(f"DROP TABLE IF EXISTS {full_name}")
        logging.info(f"Dropped table {full_name}")


# Cell 5: Performance Monitoring Functions
# ========================================

class PerformanceMonitor:
    """
    Monitor Spark job performance.
    """
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """Start timing."""
        self.start_time = datetime.now()
        logging.info(f"⏱️  Timing started: {self.start_time}")
    
    def end(self):
        """End timing and log duration."""
        if self.start_time is None:
            raise RuntimeError("Timing has not been started")
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        logging.info(f"✅ Completed in {duration:.2f} seconds")
        return duration
    
    def checkpoint(self, label: str):
        """Log checkpoint time."""
        if self.start_time is None:
            raise RuntimeError("Timing has not been started")
        elapsed = (datetime.now() - self.start_time).total_seconds()
        logging.info(f"⏱️  [{label}] {elapsed:.2f}s elapsed")


# Cell 6: Export Utilities
# =======================

# Make utilities available to calling notebooks
execution_logger = ExecutionLogger
dataframe_utils = DataFrameUtils
filesystem_utils = FileSystemUtils
table_utils = TableUtils
performance_monitor = PerformanceMonitor

print("\n" + "="*60)
print("✅ SESSION INITIALIZATION COMPLETE")
print("="*60)
print("\nAvailable utilities:")
print("  • ExecutionLogger - Structured logging")
print("  • DataFrameUtils - DataFrame operations")
print("  • FileSystemUtils - OneLake file I/O")
print("  • TableUtils - Table management")
print("  • PerformanceMonitor - Execution timing")
print("\nUsage: ExecutionLogger('notebook_name')")
print("="*60 + "\n")



