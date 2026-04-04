#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comprehensive test suite for LocalFileSerilizer in cup/services/serializer.py
"""
import sys
import os
import tempfile
import shutil
import unittest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cup.services import serializer


class TestLocalFileSerilizerBase(unittest.TestCase):
    """Base test class with common setup/teardown"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp(prefix='cup_serializer_test_')
        self.storage_subdir = os.path.join(self.temp_dir, '0')
        os.makedirs(self.storage_subdir, exist_ok=True)
        
    def tearDown(self):
        """Clean up temporary directory"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


class TestLogfileFinding(TestLocalFileSerilizerBase):
    """Test _find_logfile_by_logid method"""
    
    def test_find_logfile_basic(self):
        """Test basic log file finding functionality"""
        serilizer = serializer.LocalFileSerilizer(storage_dir=self.temp_dir)
        
        # Create test log files
        for start_id in [0, 10, 20, 30]:
            fname = os.path.join(self.storage_subdir, 'done.{0}'.format(start_id))
            with open(fname, 'wb') as f:
                pass
        
        serilizer._do_open4read(start_logid=-1)
        
        # Test various logid lookups
        self.assertEqual(serilizer._find_logfile_by_logid(5), 'done.0')
        self.assertEqual(serilizer._find_logfile_by_logid(10), 'done.10')
        self.assertEqual(serilizer._find_logfile_by_logid(15), 'done.10')
        self.assertEqual(serilizer._find_logfile_by_logid(25), 'done.20')
        
        serilizer.close_read()
    
    def test_find_logfile_with_writing_file(self):
        """Test log file finding with writing file"""
        serilizer = serializer.LocalFileSerilizer(storage_dir=self.temp_dir)
        
        # Create test files including writing file
        for start_id in [0, 10, 20]:
            fname = os.path.join(self.storage_subdir, 'done.{0}'.format(start_id))
            with open(fname, 'wb') as f:
                pass
        
        writing_fname = os.path.join(self.storage_subdir, 'writing.30')
        with open(writing_fname, 'wb') as f:
            pass
        
        serilizer._do_open4read(start_logid=-1)
        
        # Should find writing file for logids beyond last done file
        self.assertEqual(serilizer._find_logfile_by_logid(35), 'writing.30')
        
        serilizer.close_read()
    
    def test_find_logfile_invalid(self):
        """Test log file finding with invalid logid"""
        serilizer = serializer.LocalFileSerilizer(storage_dir=self.temp_dir)
        
        # Create test files starting from logid 10
        for start_id in [10, 20, 30]:
            fname = os.path.join(self.storage_subdir, 'done.{0}'.format(start_id))
            with open(fname, 'wb') as f:
                pass
        
        serilizer._do_open4read(start_logid=-1)
        
        # Logid smaller than all files should return None
        result = serilizer._find_logfile_by_logid(5)
        self.assertIsNone(result)
        
        serilizer.close_read()
    
    def test_find_logfile_empty(self):
        """Test log file finding with no files"""
        serilizer = serializer.LocalFileSerilizer(storage_dir=self.temp_dir)
        serilizer._buffer_files = []
        
        result = serilizer._find_logfile_by_logid(10)
        self.assertIsNone(result)
    
    def test_find_logfile_single_file(self):
        """Test log file finding with single file"""
        serilizer = serializer.LocalFileSerilizer(storage_dir=self.temp_dir)
        
        fname = os.path.join(self.storage_subdir, 'done.100')
        with open(fname, 'wb') as f:
            pass
        
        serilizer._do_open4read(start_logid=-1)
        
        # Any logid >= 100 should map to this file
        self.assertEqual(serilizer._find_logfile_by_logid(100), 'done.100')
        self.assertEqual(serilizer._find_logfile_by_logid(150), 'done.100')
        
        serilizer.close_read()


class TestOpen4ReadWithLogid(TestLocalFileSerilizerBase):
    """Test _do_open4read with start_logid parameter"""
    
    def test_open4read_default_behavior(self):
        """Test that default behavior (start_logid=-1) still works"""
        serilizer = serializer.LocalFileSerilizer(storage_dir=self.temp_dir)
        
        # Create test files
        for start_id in [0, 10, 20]:
            fname = os.path.join(self.storage_subdir, 'done.{0}'.format(start_id))
            with open(fname, 'wb') as f:
                pass
        
        # Should open first file
        result = serilizer._do_open4read(start_logid=-1)
        self.assertTrue(result)
        self.assertIsNotNone(serilizer._load_stream)
        
        serilizer.close_read()
    
    def test_open4read_specific_logid(self):
        """Test opening read stream from specific logid"""
        serilizer = serializer.LocalFileSerilizer(storage_dir=self.temp_dir)
        
        # Create test files
        for start_id in [0, 10, 20]:
            fname = os.path.join(self.storage_subdir, 'done.{0}'.format(start_id))
            with open(fname, 'wb') as f:
                pass
        
        # Should open file containing logid 15 (which is done.10)
        # But since files are empty, seek will fail (expected behavior)
        result = serilizer._do_open4read(start_logid=15)
        # Will return False because file is empty and EOF is reached
        self.assertFalse(result)
        
        # Test with logid that exists in first file (logid 5 in done.0)
        result = serilizer._do_open4read(start_logid=5)
        # Will also return False because file is empty
        self.assertFalse(result)
    
    def test_open4read_nonexistent_logid(self):
        """Test opening read stream with non-existent logid"""
        serilizer = serializer.LocalFileSerilizer(storage_dir=self.temp_dir)
        
        # Create test files
        for start_id in [0, 10, 20]:
            fname = os.path.join(self.storage_subdir, 'done.{0}'.format(start_id))
            with open(fname, 'wb') as f:
                pass
        
        # Logid too large should fail gracefully
        result = serilizer._do_open4read(start_logid=1000)
        self.assertFalse(result)
    
    def test_open4read_invalid_logid(self):
        """Test opening read stream with invalid logid"""
        serilizer = serializer.LocalFileSerilizer(storage_dir=self.temp_dir)
        
        # Create test files starting from 10
        for start_id in [10, 20, 30]:
            fname = os.path.join(self.storage_subdir, 'done.{0}'.format(start_id))
            with open(fname, 'wb') as f:
                pass
        
        # Logid smaller than all files should fail
        result = serilizer._do_open4read(start_logid=5)
        self.assertFalse(result)
    
    def test_open4read_no_files(self):
        """Test opening read stream with no log files"""
        serilizer = serializer.LocalFileSerilizer(storage_dir=self.temp_dir)
        
        result = serilizer._do_open4read(start_logid=-1)
        self.assertFalse(result)


class TestCloseRead(TestLocalFileSerilizerBase):
    """Test close_read method"""
    
    def test_close_read_when_open(self):
        """Test closing read stream when open"""
        serilizer = serializer.LocalFileSerilizer(storage_dir=self.temp_dir)
        
        fname = os.path.join(self.storage_subdir, 'done.0')
        with open(fname, 'wb') as f:
            pass
        
        serilizer._do_open4read(start_logid=-1)
        self.assertIsNotNone(serilizer._load_stream)
        
        serilizer.close_read()
        self.assertIsNone(serilizer._load_stream)
    
    def test_close_read_when_closed(self):
        """Test closing read stream when already closed"""
        serilizer = serializer.LocalFileSerilizer(storage_dir=self.temp_dir)
        
        # Should not raise exception
        serilizer.close_read()
        self.assertIsNone(serilizer._load_stream)


class TestAsignUint2byteBybits(TestLocalFileSerilizerBase):
    """Test asign_uint2byte_bybits method for Python 3 compatibility"""
    
    def test_asign_basic(self):
        """Test basic uint to byte conversion"""
        result = serializer.BaseSerilizer.asign_uint2byte_bybits(256, 16)
        self.assertEqual(len(result), 2)
    
    def test_asign_128bit(self):
        """Test 128-bit conversion"""
        result = serializer.BaseSerilizer.asign_uint2byte_bybits(1000, 128)
        self.assertEqual(len(result), 16)  # 128 bits / 8 = 16 bytes
    
    def test_asign_32bit(self):
        """Test 32-bit conversion"""
        result = serializer.BaseSerilizer.asign_uint2byte_bybits(65536, 32)
        self.assertEqual(len(result), 4)  # 32 bits / 8 = 4 bytes
    
    def test_asign_zero(self):
        """Test conversion of zero"""
        result = serializer.BaseSerilizer.asign_uint2byte_bybits(0, 16)
        self.assertEqual(len(result), 2)
        for char in result:
            self.assertEqual(ord(char), 0)


class TestConvertBytes2uint(TestLocalFileSerilizerBase):
    """Test convert_bytes2uint method"""
    
    def test_convert_basic(self):
        """Test basic byte to uint conversion"""
        test_str = chr(1) + chr(0)
        result = serializer.BaseSerilizer.convert_bytes2uint(test_str)
        self.assertEqual(result, 1)
    
    def test_convert_roundtrip(self):
        """Test roundtrip conversion"""
        original = 1000
        bytes_data = serializer.BaseSerilizer.asign_uint2byte_bybits(original, 16)
        result = serializer.BaseSerilizer.convert_bytes2uint(bytes_data)
        self.assertEqual(result, original)


class TestSeekToLogid(TestLocalFileSerilizerBase):
    """Test _seek_to_logid method"""
    
    def test_seek_basic(self):
        """Test basic seek functionality"""
        serilizer = serializer.LocalFileSerilizer(
            storage_dir=self.temp_dir,
            skip_badlog=True
        )
        
        # Create a file and open for reading
        fname = os.path.join(self.storage_subdir, 'done.0')
        with open(fname, 'wb') as f:
            pass
        
        serilizer._do_open4read(start_logid=-1)
        serilizer._seek_to_logid(10)
        # Should not raise exception
        
        serilizer.close_read()
    
    def test_seek_no_stream(self):
        """Test seek with no open stream"""
        serilizer = serializer.LocalFileSerilizer(storage_dir=self.temp_dir)
        
        # Should not raise exception, just log error
        serilizer._seek_to_logid(10)


class TestBackwardCompatibility(TestLocalFileSerilizerBase):
    """Test backward compatibility"""
    
    def test_open4read_without_parameter(self):
        """Test that open4read() still works without parameters"""
        serilizer = serializer.LocalFileSerilizer(storage_dir=self.temp_dir)
        
        fname = os.path.join(self.storage_subdir, 'done.0')
        with open(fname, 'wb') as f:
            pass
        
        result = serilizer.open4read()
        self.assertTrue(result)
        
        serilizer.close_read()
    
    def test_existing_api_unchanged(self):
        """Test that existing API methods are unchanged"""
        serilizer = serializer.LocalFileSerilizer(storage_dir=self.temp_dir)
        
        # Test that all public methods still exist
        self.assertTrue(hasattr(serilizer, 'add_log'))
        self.assertTrue(hasattr(serilizer, 'read'))
        self.assertTrue(hasattr(serilizer, 'open4read'))
        self.assertTrue(hasattr(serilizer, 'close_read'))
        self.assertTrue(hasattr(serilizer, 'open4write'))
        self.assertTrue(hasattr(serilizer, 'close_write'))


class TestEdgeCases(TestLocalFileSerilizerBase):
    """Test edge cases and error handling"""
    
    def test_invalid_filename_format(self):
        """Test handling of invalid filename format"""
        serilizer = serializer.LocalFileSerilizer(storage_dir=self.temp_dir)
        
        # Create file with invalid name format
        fname = os.path.join(self.storage_subdir, 'invalid_file.txt')
        with open(fname, 'wb') as f:
            pass
        
        serilizer._do_open4read(start_logid=-1)
        
        # Should skip invalid file
        result = serilizer._find_logfile_by_logid(10)
        self.assertIsNone(result)
        
        serilizer.close_read()
    
    def test_mixed_valid_invalid_files(self):
        """Test handling of mixed valid and invalid files"""
        serilizer = serializer.LocalFileSerilizer(storage_dir=self.temp_dir)
        
        # Create mix of valid and invalid files
        valid_files = ['done.0', 'done.10', 'done.20']
        invalid_files = ['invalid.txt', 'test.log', 'readme.md']
        
        for fname in valid_files:
            with open(os.path.join(self.storage_subdir, fname), 'wb') as f:
                pass
        
        for fname in invalid_files:
            with open(os.path.join(self.storage_subdir, fname), 'wb') as f:
                pass
        
        serilizer._do_open4read(start_logid=-1)
        
        # Should only consider valid files
        self.assertEqual(serilizer._find_logfile_by_logid(5), 'done.0')
        self.assertEqual(serilizer._find_logfile_by_logid(15), 'done.10')
        
        serilizer.close_read()


def run_all_tests():
    """Run all tests and return results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestLogfileFinding,
        TestOpen4ReadWithLogid,
        TestCloseRead,
        TestAsignUint2byteBybits,
        TestConvertBytes2uint,
        TestSeekToLogid,
        TestBackwardCompatibility,
        TestEdgeCases,
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    print("=" * 80)
    print("Running Comprehensive Tests for LocalFileSerilizer")
    print("=" * 80)
    
    result = run_all_tests()
    
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print("Tests run: {0}".format(result.testsRun))
    print("Failures: {0}".format(len(result.failures)))
    print("Errors: {0}".format(len(result.errors)))
    print("Skipped: {0}".format(len(result.skipped)))
    
    if result.wasSuccessful():
        print("\n✓ ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n✗ SOME TESTS FAILED!")
        sys.exit(1)
