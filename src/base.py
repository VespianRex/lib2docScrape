"""Base components and utilities for the documentation crawler."""

import logging
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse, urlunparse


# URLInfo dataclass, normalize_url, and is_valid_url functions removed as they are deprecated
# and replaced by src.utils.url_info.py
