import pickle
import json
import struct
import cloudpickle
from pyspark.sql.types import LongType

# def ndp_reader(split_index, config_json):
#     config = json.loads(config_json)
#     print(config)
#     return pydike.client.tpch.TpchSQL(config)


class DeSerializer:
    def load_stream(self, infile):
        length = infile.read(4)
        length = struct.unpack("!i", length)[0]
        s = infile.read(length)
        return s


class Serializer:
    def dump_stream(self, out_iter, outfile):
        out_iter.to_spark(outfile)

def create_spark_worker_command():
    # func = ndp_reader
    # deser = DeSerializer()
    # ser = Serializer()

    #command = (func, None, deser, ser)  # Format should be (func, profiler, deserializer, serializer)
    pickle_protocol = pickle.HIGHEST_PROTOCOL
    return pickle.dumps(command, pickle_protocol)

def filter_func(iterator):
    for pdf in iterator:
        yield pdf #pdf[pdf.id == 1]

def create_command():
    return_type = [LongType, LongType, LongType, LongType]
    cmd = (filter_func, return_type)
    pickle_protocol = pickle.HIGHEST_PROTOCOL
        return cloudpickle.dumps(cmd, pickle_protocol)


if __name__ == '__main__':
    command = create_command()
    print(command.hex())
    # print(filter_func)
    # c1 = cloudpickle.dumps(filter_func)
    # del filter_func
    # for i in (c_loaded)(list(range(0, 5))):
    #     print(i)
    #
    # print("done")


