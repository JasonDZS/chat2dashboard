class DatabaseNotFoundError(Exception):
    def __init__(self, db_name: str):
        self.db_name = db_name
        super().__init__(f"Database '{db_name}' not found")

class SchemaNotFoundError(Exception):
    def __init__(self, db_name: str):
        self.db_name = db_name
        super().__init__(f"Schema file for database '{db_name}' not found")

class UnsupportedFileTypeError(Exception):
    def __init__(self, filename: str):
        self.filename = filename
        super().__init__(f"File {filename} is not a supported file type. Only .xlsx and .csv files are allowed.")

class PandasNotAvailableError(Exception):
    def __init__(self, error_message: str):
        self.error_message = error_message
        super().__init__(f"Pandas support not available: {error_message}")

class InvalidIndexError(Exception):
    def __init__(self, index: int, max_index: int):
        self.index = index
        self.max_index = max_index
        super().__init__(f"Invalid index {index}. Valid range: 0-{max_index}")

class RequestNotFoundError(Exception):
    def __init__(self, request_id: int):
        self.request_id = request_id
        super().__init__(f"Request log with ID {request_id} not found")

class NoSQLTrainingDataError(Exception):
    def __init__(self):
        super().__init__("No SQL training data found")


# 文档处理相关异常

class DocumentNotFoundError(Exception):
    """文档未找到异常"""
    def __init__(self, file_id: str):
        self.file_id = file_id
        super().__init__(f"Document with ID '{file_id}' not found")


class ProcessingInProgressError(Exception):
    """文档正在处理中异常"""
    def __init__(self, file_id: str):
        self.file_id = file_id
        super().__init__(f"Document '{file_id}' is currently being processed. Please wait for completion.")


class DocumentProcessingError(Exception):
    """文档处理错误异常"""
    def __init__(self, file_id: str, error_message: str):
        self.file_id = file_id
        self.error_message = error_message
        super().__init__(f"Failed to process document '{file_id}': {error_message}")


class InvalidChunkSizeError(Exception):
    """无效分块大小异常"""
    def __init__(self, chunk_size: int):
        self.chunk_size = chunk_size
        super().__init__(f"Invalid chunk size '{chunk_size}'. Must be between 100 and 2048.")


class InvalidDocumentFormatError(Exception):
    """无效文档格式异常"""
    def __init__(self, filename: str, format_type: str):
        self.filename = filename
        self.format_type = format_type
        super().__init__(f"Invalid document format for '{filename}'. Expected format: {format_type}")


class DocumentCorruptedError(Exception):
    """文档损坏异常"""
    def __init__(self, filename: str):
        self.filename = filename
        super().__init__(f"Document '{filename}' appears to be corrupted and cannot be processed")


class FileSizeExceededError(Exception):
    """文件大小超出限制异常"""
    def __init__(self, filename: str, size: int, max_size: int):
        self.filename = filename
        self.size = size
        self.max_size = max_size
        super().__init__(f"File '{filename}' size ({size} bytes) exceeds maximum allowed size ({max_size} bytes)")


class KnowledgeBaseNotFoundError(Exception):
    """知识库未找到异常"""
    def __init__(self, kb_id: str):
        self.kb_id = kb_id
        super().__init__(f"Knowledge base with ID '{kb_id}' not found")


class BuildInProgressError(Exception):
    """构建正在进行中异常"""
    def __init__(self, kb_id: str):
        self.kb_id = kb_id
        super().__init__(f"Knowledge base '{kb_id}' is currently being built. Please wait for completion.")


class BatchProcessingError(Exception):
    """批量处理错误异常"""
    def __init__(self, batch_id: str, failed_files: int, total_files: int):
        self.batch_id = batch_id
        self.failed_files = failed_files
        self.total_files = total_files
        super().__init__(f"Batch processing '{batch_id}' completed with errors: {failed_files}/{total_files} files failed")


# 搜索相关异常

class InvalidSearchQueryError(Exception):
    """无效搜索查询异常"""
    def __init__(self, query: str, reason: str = ""):
        self.query = query
        self.reason = reason
        message = f"Invalid search query: '{query}'"
        if reason:
            message += f" - {reason}"
        super().__init__(message)


class SearchTimeoutError(Exception):
    """搜索超时异常"""
    def __init__(self, timeout_seconds: float, query: str = ""):
        self.timeout_seconds = timeout_seconds
        self.query = query
        message = f"Search operation timed out after {timeout_seconds} seconds"
        if query:
            message += f" for query: '{query}'"
        super().__init__(message)


class SearchIndexError(Exception):
    """搜索索引错误异常"""
    def __init__(self, index_name: str, error_message: str):
        self.index_name = index_name
        self.error_message = error_message
        super().__init__(f"Search index '{index_name}' error: {error_message}")


class VectorStoreError(Exception):
    """向量存储错误异常"""
    def __init__(self, operation: str, error_message: str):
        self.operation = operation
        self.error_message = error_message
        super().__init__(f"Vector store operation '{operation}' failed: {error_message}")


class KnowledgeGraphError(Exception):
    """知识图谱错误异常"""
    def __init__(self, operation: str, error_message: str):
        self.operation = operation
        self.error_message = error_message
        super().__init__(f"Knowledge graph operation '{operation}' failed: {error_message}")


class EmbeddingModelError(Exception):
    """嵌入模型错误异常"""
    def __init__(self, model_name: str, error_message: str):
        self.model_name = model_name
        self.error_message = error_message
        super().__init__(f"Embedding model '{model_name}' error: {error_message}")


class QueryExpansionError(Exception):
    """查询扩展错误异常"""
    def __init__(self, query: str, strategy: str, error_message: str):
        self.query = query
        self.strategy = strategy
        self.error_message = error_message
        super().__init__(f"Query expansion failed for '{query}' using strategy '{strategy}': {error_message}")


class RerankingError(Exception):
    """重排序错误异常"""
    def __init__(self, reranker_name: str, error_message: str):
        self.reranker_name = reranker_name
        self.error_message = error_message
        super().__init__(f"Reranking with '{reranker_name}' failed: {error_message}")


class FusionStrategyError(Exception):
    """融合策略错误异常"""
    def __init__(self, strategy: str, error_message: str):
        self.strategy = strategy
        self.error_message = error_message
        super().__init__(f"Fusion strategy '{strategy}' failed: {error_message}")