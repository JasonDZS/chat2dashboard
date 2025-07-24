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