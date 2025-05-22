"""
Compressed storage implementation.
"""
import os
import json
import gzip
import lzma
import bz2
import zlib
import pickle
import logging
from enum import Enum
from typing import Dict, List, Optional, Any, Union, BinaryIO, TextIO, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class CompressionFormat(str, Enum):
    """Compression format."""
    GZIP = "gzip"
    LZMA = "lzma"
    BZ2 = "bz2"
    ZLIB = "zlib"
    NONE = "none"

class CompressionConfig(BaseModel):
    """Configuration for compression."""
    format: CompressionFormat = CompressionFormat.GZIP
    level: int = 9  # Compression level (1-9, higher = more compression)
    use_for_text: bool = True
    use_for_binary: bool = True
    min_size_for_compression: int = 1024  # Don't compress files smaller than this
    metadata_compression: bool = True  # Compress metadata files
    
    # Format-specific options
    gzip_wbits: int = 31  # 31 = gzip format with maximum window size
    zlib_wbits: int = 15  # 15 = maximum window size
    lzma_preset: int = 9  # 0-9, higher = more compression
    
    class Config:
        use_enum_values = True

class CompressedStorage:
    """
    Compressed storage for lib2docScrape.
    Provides compression for stored data.
    """
    
    def __init__(self, config: Optional[CompressionConfig] = None):
        """
        Initialize the compressed storage.
        
        Args:
            config: Optional compression configuration
        """
        self.config = config or CompressionConfig()
        logger.info(f"Initialized compressed storage with format={self.config.format}, level={self.config.level}")
        
    def compress_data(self, data: bytes) -> bytes:
        """
        Compress binary data.
        
        Args:
            data: Data to compress
            
        Returns:
            Compressed data
        """
        # Skip compression for small data
        if len(data) < self.config.min_size_for_compression:
            return data
            
        # Compress based on format
        if self.config.format == CompressionFormat.GZIP:
            return gzip.compress(data, compresslevel=self.config.level)
        elif self.config.format == CompressionFormat.LZMA:
            return lzma.compress(data, preset=self.config.lzma_preset)
        elif self.config.format == CompressionFormat.BZ2:
            return bz2.compress(data, compresslevel=self.config.level)
        elif self.config.format == CompressionFormat.ZLIB:
            return zlib.compress(data, level=self.config.level)
        else:
            return data
            
    def decompress_data(self, data: bytes, format: Optional[CompressionFormat] = None) -> bytes:
        """
        Decompress binary data.
        
        Args:
            data: Compressed data
            format: Optional format override
            
        Returns:
            Decompressed data
        """
        format = format or self.config.format
        
        # Decompress based on format
        if format == CompressionFormat.GZIP:
            return gzip.decompress(data)
        elif format == CompressionFormat.LZMA:
            return lzma.decompress(data)
        elif format == CompressionFormat.BZ2:
            return bz2.decompress(data)
        elif format == CompressionFormat.ZLIB:
            return zlib.decompress(data)
        else:
            return data
            
    def compress_text(self, text: str, encoding: str = 'utf-8') -> bytes:
        """
        Compress text data.
        
        Args:
            text: Text to compress
            encoding: Text encoding
            
        Returns:
            Compressed data
        """
        if not self.config.use_for_text:
            return text.encode(encoding)
            
        return self.compress_data(text.encode(encoding))
        
    def decompress_text(self, data: bytes, encoding: str = 'utf-8', format: Optional[CompressionFormat] = None) -> str:
        """
        Decompress text data.
        
        Args:
            data: Compressed data
            encoding: Text encoding
            format: Optional format override
            
        Returns:
            Decompressed text
        """
        if not self.config.use_for_text and format is None:
            return data.decode(encoding)
            
        return self.decompress_data(data, format).decode(encoding)
        
    def save_json(self, data: Any, file_path: str) -> None:
        """
        Save JSON data to a file with compression.
        
        Args:
            data: Data to save
            file_path: Path to save to
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        # Convert to JSON
        json_str = json.dumps(data, indent=2)
        
        # Compress if needed
        if self.config.metadata_compression and self.config.use_for_text:
            # Add compression extension
            if not file_path.endswith(f".{self.config.format}"):
                file_path = f"{file_path}.{self.config.format}"
                
            # Compress and save
            compressed_data = self.compress_text(json_str)
            with open(file_path, 'wb') as f:
                f.write(compressed_data)
        else:
            # Save without compression
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
                
        logger.debug(f"Saved JSON data to {file_path}")
        
    def load_json(self, file_path: str) -> Any:
        """
        Load JSON data from a file with decompression.
        
        Args:
            file_path: Path to load from
            
        Returns:
            Loaded data
        """
        # Check if file exists
        if not os.path.exists(file_path):
            # Try with compression extension
            for format in CompressionFormat:
                if format != CompressionFormat.NONE:
                    compressed_path = f"{file_path}.{format}"
                    if os.path.exists(compressed_path):
                        file_path = compressed_path
                        break
                        
        # Determine if file is compressed
        format = None
        for fmt in CompressionFormat:
            if fmt != CompressionFormat.NONE and file_path.endswith(f".{fmt}"):
                format = fmt
                break
                
        # Load and decompress if needed
        if format is not None:
            with open(file_path, 'rb') as f:
                compressed_data = f.read()
                
            json_str = self.decompress_text(compressed_data, format=format)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_str = f.read()
                
        # Parse JSON
        data = json.loads(json_str)
        
        logger.debug(f"Loaded JSON data from {file_path}")
        
        return data
        
    def save_pickle(self, data: Any, file_path: str) -> None:
        """
        Save pickled data to a file with compression.
        
        Args:
            data: Data to save
            file_path: Path to save to
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        # Pickle data
        pickled_data = pickle.dumps(data)
        
        # Compress if needed
        if self.config.use_for_binary:
            # Add compression extension
            if not file_path.endswith(f".{self.config.format}"):
                file_path = f"{file_path}.{self.config.format}"
                
            # Compress and save
            compressed_data = self.compress_data(pickled_data)
            with open(file_path, 'wb') as f:
                f.write(compressed_data)
        else:
            # Save without compression
            with open(file_path, 'wb') as f:
                f.write(pickled_data)
                
        logger.debug(f"Saved pickled data to {file_path}")
        
    def load_pickle(self, file_path: str) -> Any:
        """
        Load pickled data from a file with decompression.
        
        Args:
            file_path: Path to load from
            
        Returns:
            Loaded data
        """
        # Check if file exists
        if not os.path.exists(file_path):
            # Try with compression extension
            for format in CompressionFormat:
                if format != CompressionFormat.NONE:
                    compressed_path = f"{file_path}.{format}"
                    if os.path.exists(compressed_path):
                        file_path = compressed_path
                        break
                        
        # Determine if file is compressed
        format = None
        for fmt in CompressionFormat:
            if fmt != CompressionFormat.NONE and file_path.endswith(f".{fmt}"):
                format = fmt
                break
                
        # Load and decompress if needed
        with open(file_path, 'rb') as f:
            data = f.read()
            
        if format is not None:
            data = self.decompress_data(data, format=format)
            
        # Unpickle data
        unpickled_data = pickle.loads(data)
        
        logger.debug(f"Loaded pickled data from {file_path}")
        
        return unpickled_data
