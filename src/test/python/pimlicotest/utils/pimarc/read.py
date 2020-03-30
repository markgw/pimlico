import os
import tempfile
import unittest


class PimarcReadTest(unittest.TestCase):
    def setUp(self):
        from pimlico import TEST_DATA_DIR
        import os

        self.input_path = os.path.join(TEST_DATA_DIR, "pimarc", "smallex.prc")


class OpenArchiveTest(PimarcReadTest):
    """
    Just open an archive and do nothing with it.

    """
    def test_create(self):
        from pimlico.utils.pimarc import PimarcReader

        with PimarcReader(self.input_path):
            # Just opened the archive: don't do anything more
            pass


class ReadIndexTest(PimarcReadTest):
    """
    Read in an archive's index and check its format.

    We use a pre-prepared index where we know what the filenames should be and check they're write.

    """
    def test_create(self):
        from pimlico.utils.pimarc import PimarcReader

        # We know that the filenames in the archive should look like this
        filename_base = "doc_{}"
        with PimarcReader(self.input_path) as arc:
            for i, filename in enumerate(arc.index):
                expected_fn = filename_base.format(i)
                self.assertEqual(expected_fn, filename, msg="filename read in archive did not match that expected")


class ReadFilesTest(PimarcReadTest):
    """
    Read in an archive's index and each of its files.

    We use a pre-prepared index where we know what the file content should be.
    Each file contains random data, but starts with a fixed string containing the filename,
    so we check that this has been correctly read.

    """
    def test_create(self):
        from pimlico.utils.pimarc import PimarcReader

        # We know that the files in the archive should start like this
        file_start_base = "Start of doc_{}"
        with PimarcReader(self.input_path) as arc:
            for i, (metadata, file_data) in enumerate(arc):
                expected_start = file_start_base.format(i)
                # Decode the UTF-8 encoded data
                file_text = file_data.decode("utf-8")
                file_text_start = file_text[:len(expected_start)]
                self.assertEqual(expected_start, file_text_start,
                                 msg="text read in file in archive did not start with the expected string")


if __name__ == "__main__":
    unittest.main()
