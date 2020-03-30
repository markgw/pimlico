"""
Test writing out data and reading it back in.

"""
import os
import tempfile
import unittest


class PimarcWriteReadTest(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory to use as our storage location
        self.storage_dir = tempfile.mkdtemp()
        self.archive_path = os.path.join(self.storage_dir, "test.prc")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.storage_dir)


class WriteEmptyArchiveTest(PimarcWriteReadTest):
    """
    Create an empty archive and write to disk, then read it back in and check it's empty.

    """
    def test_create(self):
        from pimlico.utils.pimarc import PimarcWriter, PimarcReader

        with PimarcWriter(self.archive_path):
            # Created the archive: don't do anything now
            pass

        with PimarcReader(self.archive_path) as arc:
            self.assertEqual(len(arc), 0)
            self.assertEqual(len(arc.index), 0)


def _generate_random_text(length=300):
    """
    Generate a string made up of random characters.
    """
    import string
    import random
    return "".join(random.choice(string.ascii_lowercase) for i in range(length))


class WriteRandomDocumentsTest(PimarcWriteReadTest):
    """
    Create an empty archive and add some randomly-generated text documents.
    Read them back in and check they're the same.

    """
    def test_write(self):
        from pimlico.utils.pimarc import PimarcWriter, PimarcReader
        # Generate some random text
        files_data = [_generate_random_text() for i in range(5)]

        with PimarcWriter(self.archive_path) as arc:
            # Add 5 files to the archive
            for i, text in enumerate(files_data):
                arc.write_file(text.encode("utf-8"), "doc_{}".format(i))

        with PimarcReader(self.archive_path) as arc:
            self.assertEqual(len(arc), len(files_data))
            
            # Read each file back in and check it has the same content
            for (metadata, file_data), expected_data in zip(arc, files_data):
                self.assertEqual(file_data.decode("utf-8"), expected_data,
                                 msg="data read in from archive doesn't match what we wrote out "
                                     "for the corresponding file")


if __name__ == "__main__":
    unittest.main()
