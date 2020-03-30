import os
import tempfile
import unittest


class PimarcWriterTest(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory to use as our storage location
        self.storage_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.storage_dir)


class CreateEmptyArchiveTest(PimarcWriterTest):
    """
    Create an empty archive and write to disk.

    """
    def test_create(self):
        from pimlico.utils.pimarc import PimarcWriter

        with PimarcWriter(os.path.join(self.storage_dir, "test.prc")):
            # Created the archive: don't do anything now
            # The index will be written when we exit the block
            pass


def _generate_random_text(length=300):
    """
    Generate a string made up of random characters.
    """
    import string
    import random
    return "".join(random.choice(string.ascii_lowercase) for i in range(length))


class WriteRandomDocumentsTest(PimarcWriterTest):
    """
    Create an empty archive and add some randomly-generated text documents.

    """
    def test_write(self):
        from pimlico.utils.pimarc import PimarcWriter

        with PimarcWriter(os.path.join(self.storage_dir, "test.prc")) as arc:
            # Add 5 files to the archive
            for i in range(5):
                text = _generate_random_text()
                arc.write_file(text.encode("utf-8"), "doc_{}".format(i))


if __name__ == "__main__":
    unittest.main()
