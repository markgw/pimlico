from pimlico.utils.varint import decode_stream, encode


def _read_var_length_data(reader):
    """
    Read some data from a file-like object by first reading a varint that says how many
    bytes are in the data and then reading the data immediately following.

    """
    # Get a single varint from the reader stream
    data_length = decode_stream(reader)
    # Read the data as a bytes array
    return reader.read(data_length)


def _skip_var_length_data(reader):
    """
    Like read_var_length_data, but doesn't actually read the data. Just reads the length
    indicator and seeks to the end of the data.

    """
    data_length = decode_stream(reader)
    reader.seek(data_length, 1)


def _write_var_length_data(writer, data):
    """
    Write some data to a file-like object by first writing a varint that says how many
    bytes are in the data and then writing the data immediately following.

    """
    # Store the length of the data in bytes
    data_length = len(data)
    writer.write(encode(data_length))
    # Write the data as a bytes array
    return writer.write(data)