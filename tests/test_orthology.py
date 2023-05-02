import numpy as np
import pandas as pd

from omnipath._core.utils._homologene import download_homologene
from omnipath._core.utils._homologene import show_homologene


class TestHomologene():
    def test_download_homologene(self):
        
        homologene = download_homologene()
        
        expected_shape = (17312, 2)
        actual_shape = homologene.shape
        
        assert expected_shape == actual_shape
        
        expected_columns = ['source', 'target']
        actual_columns = homologene.columns
        
        assert expected_columns == actual_columns
        


class TestOrthologyConversion():
    def test_complex_genes(self):
        
        df = pd.DataFrame({'symbol': [''] })
        df = ['CSF2RA_CSF2RB',
              'CSF2RB_IL5RA',
              'CSF2RB_IL3RA',
              'IL11RA_IL6ST',
              'IFNL3_IFNLR1_IL10RB',
              'IL22_IL22RA1'
              ]