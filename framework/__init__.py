"""
Framework CRISP per la generazione di libri.
"""

from .crisp_framework import CRISPFramework
from .crisp_extractors import extract_data_from_response
from .crisp_utils import load_docx_content, extract_section, replace_variables