# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
import os
import shutil
import tarfile
from operator import itemgetter

import sys
from pimlico.cli.subcommands import PimlicoCLISubcommand
from pimlico.datatypes.base import DataNotReadyError
from pimlico.utils.progress import get_open_progress_bar


class RecoverCmd(PimlicoCLISubcommand):
    """
    When a document map module gets killed forcibly, sometimes it doesn't have time to
    save its execution state, meaning that it can't pick up from where it left off.

    This command tries to fix the state so that execution can be resumed. It counts
    the documents in the output corpora and checks what the last written document was.
    It then updates the state to mark the module as partially executed, so that it
    continues from this document when you next try to run it.

    The last written document is always thrown away, since we don't know whether it
    was fully written. To avoid partial, broken output, we assume the last document
    was not completed and resume execution on that one.

    Note that this will only work for modules that output something (which may be an
    invalid doc) to every output for every input doc. Modules that only output to
    some outputs for each input cannot be recovered so easily.

    """
    command_name = "recover"
    command_help = "Examine and fix a partially executed map module's output state after forcible termination"

    def add_arguments(self, parser):
        parser.add_argument("module", help="The name (or number) of the module to recover")
        parser.add_argument("--dry", action="store_true", help="Dry run: just say what we'd do")
        parser.add_argument("--last-docs", type=int, help="Number of last docs to look at in each corpus "
                                                          "when synchronizing", default=10)

    def run_command(self, pipeline, opts):
        dry = opts.dry
        last_docs_buffer_size = opts.last_docs
        module_name = opts.module
        module = pipeline[module_name]

        def _dry_print(mess):
            if dry:
                print "DRY: Not doing: {}".format(mess)
            else:
                print mess

        print "Trying to recover partial execution state of module {}".format(module_name)
        if module.status == "COMPLETE":
            print "Module appears to have been fully executed: not recovering"
            return

        if module.is_locked():
            _dry_print("Unlocking module")
            module.unlock()

        # Get the outputs that are being written
        outputs = module.get_grouped_corpus_output_names()
        print "Checking outputs: {}".format(", ".join(outputs))
        last_docs = []
        for output_name in outputs:
            print "\n### Checking output '{}'".format(output_name)
            try:
                output = module.get_output(output_name)
            except DataNotReadyError, e:
                print "Could not read output '{}': cannot check written documents".format(output_name)
                raise ValueError("could not read output '{}': {}".format(output_name, e))
            print "Reported length: {:,d}".format(len(output))
            print "Counting actual length. This could take some time..."
            output_last_docs, num_docs = count_docs(output, last_buffer_size=last_docs_buffer_size)
            print "\n{:,} docs. Last docs: {}".format(num_docs, "".join(
                "\n   {}, {}".format(archive, doc_name) for (archive, doc_name) in output_last_docs
            ))
            last_docs.append((num_docs, output_last_docs))

        # Look for the output that has the least written to it
        # All other outputs should end after the second last doc in this corpus
        min_count_last_docs = min(last_docs, key=itemgetter(0))
        new_last_doc = min_count_last_docs[1][-2]
        new_doc_count = min_count_last_docs[0] - 1
        print "Shortest output has {:,} docs: {:,} will be the new size of all outputs"\
            .format(new_doc_count+1, new_doc_count)

        for output_name, (count, output_last_docs) in zip(outputs, last_docs):
            # Check that all output modules have max 1 more doc than this one
            if count > new_doc_count + last_docs_buffer_size:
                print "{} has more than {} documents more than the shortest output ({:,}): outputs " \
                      "are heavily unsynchronized".format(output_name, last_docs_buffer_size, count)
            # Check that the new last doc matches with one of the last two for each other output
            if new_last_doc not in output_last_docs:
                print "{}'s last written documents do not contain the new last document in the corpus {}. " \
                      "Outputs are very out of sync, or something odd has gone on. Trying again with a larger " \
                      "--last-docs might help".format(output_name, new_last_doc)
                sys.exit(1)

        print "New last document in output corpora will be {}".format(new_last_doc)

        for output_name, (count, output_last_docs) in zip(outputs, last_docs):
            output = module.get_output(output_name)
            gzipped = output.metadata.get("gzip", False)
            removed_archives = []
            # Remove any whole archives that appear after the last doc
            for last in reversed(output_last_docs):
                # Check that the last archive is the one that will be the new last
                if last[0] != new_last_doc[0] and last[0] not in removed_archives:
                    # We can remove the whole of this archive
                    path = os.path.join(output.data_dir, "{}.tar".format(last[0]))
                    _dry_print("Removing archive {}".format(path))
                    if not dry:
                        os.remove(path)
                    removed_archives.append(last[0])
            # Truncate the new last archive so it ends after the new last file
            last_archive_path = os.path.join(output.data_dir, "{}.tar".format(new_last_doc[0]))
            _dry_print("Truncating {} after file {}".format(last_archive_path, new_last_doc[1]))
            if not dry:
                truncate_tar_after(last_archive_path, new_last_doc[1], gzipped)

        # Open a writer for each output to correct the metadata
        # This isn't strictly necessary to be able to continue, but it's useful
        for output_name in outputs:
            _dry_print("Correcting length metadata for output {}".format(output_name))
            if not dry:
                with module.get_output_writer(output_name) as writer:
                    writer.metadata["length"] = new_doc_count

        metadata = module.get_metadata()
        print "Old module metadata: {}".format(metadata)
        metadata["status"] = "PARTIALLY_PROCESSED"
        metadata["docs_completed"] = new_doc_count
        metadata["last_doc_completed"] = u"%s/%s" % new_last_doc
        print "New metadata: {}".format(metadata)
        _dry_print("Correcting status and progress of module")
        if not dry:
            module.set_metadata_values(metadata)


def count_docs(corpus, last_buffer_size=10):
    last_docs = []
    # Show counting progress so we know something's happening
    pbar = get_open_progress_bar("Counting")

    i = 0
    try:
        for i, (archive, doc_name) in pbar(enumerate(corpus.list_archive_iter())):
            # Keep a buffer of the last N docs
            last_docs.append((archive, doc_name))
            last_docs = last_docs[-last_buffer_size:]
    except tarfile.ReadError:
        # If the tar writing was broken off in the middle, tarfile might complain about
        # an unexpected end of the file
        # That's fine: we ignore the last, partially-written
        pass
    return last_docs, i


def truncate_tar_after(path, last_filename, gzipped=False):
    """
    Read through the given tar file to find the specified filename. Truncate
    the archive after the end of that file's contents.

    Creates a backup of the tar archive first, since this is a risky operation.

    Returns False if the filename wasn't found

    """
    backup_path = "{}.backup".format(path)
    print "Creating backup: {}".format(backup_path)
    shutil.copy2(path, backup_path)

    with open(path, mode="r+") as f:
        with tarfile.open(path, fileobj=f) as tar:
            for tarinfo in tar:
                filename = tarinfo.name
                # Do the same name preprocessing that archive_iter does
                doc_name = filename.decode("utf8")
                if gzipped and doc_name.endswith(".gz"):
                    # If we used the .gz extension while writing the file, remove it to get the doc name
                    doc_name = doc_name[:-3]
                if doc_name == last_filename:
                    # This is the tarinfo for what will now be the last file
                    # Check what position we're at after reading the tarinfo
                    pre_file_pos = f.tell()
                    # Advance to the end of the file
                    f.seek(pre_file_pos + tarinfo.size)
                    # Now truncate the file here
                    f.truncate()
                    return True
    return False
