"""
Simple benchmarking/profiling tool to investigate what is taking most time in
running document map modules with multiple processes.

"""
from datetime import datetime
from multiprocessing import Value, Queue, Event

from pimlico.cfg import BENCHMARK_DOC_MAP_MODULES


class BenchmarkingError(Exception):
    pass


class Timer(object):
    def __init__(self, name, cache_size=1000):
        self.cache_size = cache_size
        self.name = name
        self.start_time = None
        self._recent_times = []
        self._total_time = 0.
        self._num_times = 0

    def start(self):
        self.start_time = datetime.now()

    def end(self):
        if self.start_time is None:
            raise BenchmarkingError("timer '{}' ended before it was started".format(self.name))
        time = (datetime.now() - self.start_time).total_seconds()
        self.start_time = None
        self.add_time(time)

    def add_time(self, time):
        self._recent_times.append(time)
        if len(self._recent_times) > self.cache_size:
            self.condense()

    def condense(self):
        # Recompute sum
        # This is done every now and again so we don't accumulate too many values and use up memory
        self._total_time += sum(self._recent_times)
        self._num_times += len(self._recent_times)
        self._recent_times.clear()

    @property
    def mean_time(self):
        self.condense()
        if self._num_times > 0:
            return self._total_time / self._num_times
        else:
            return 0.

    @property
    def num_times(self):
        return self._num_times

    def __add__(self, other):
        self.condense()
        other.condense()
        self._total_time += other._total_time
        self._num_times += other._num_times
        return self

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end()


class NoOpTimer(object):
    def __init__(self, name, cache_size=1000):
        self.name = name
        self.start_time = None
        self._recent_times = []
        self._total_time = 0.
        self._num_times = 0
        self.mean_time = 0.
        self.num_times = 0

    def start(self):
        pass

    def end(self):
        pass

    def condense(self):
        pass

    def __add__(self, other):
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return


class DocMapThreadBenchmarker(object):
    """
    Thread/process-specific benchmarking. Stats are collected at the end.

    """
    def __init__(self):
        self.wait_for_input_timer = Timer("worker waiting for input")
        self.process_doc_timer = Timer("process doc")
        self.queue_output_timer = Timer("queue output")

    def start_worker_wait_for_input(self):
        self.wait_for_input_timer.start()

    def end_worker_wait_for_input(self):
        self.wait_for_input_timer.end()

    def start_process_doc(self):
        self.process_doc_timer.start()

    def end_process_doc(self):
        self.process_doc_timer.end()

    def start_queue_output(self):
        self.queue_output_timer.start()

    def end_queue_output(self):
        self.queue_output_timer.end()

    @staticmethod
    def combine(*benchmarkers):
        new_benchmarker = DocMapThreadBenchmarker()
        # Accumulate timings from all threads' benchmarkers
        for benchmarker in benchmarkers:
            new_benchmarker.wait_for_input_timer += benchmarker.wait_for_input_timer
            new_benchmarker.process_doc_timer += benchmarker.process_doc_timer
            new_benchmarker.queue_output_timer += benchmarker.queue_output_timer
        return new_benchmarker


class DocMapBenchmarker(object):
    """
    Keeps track of timings for benchmarking doc map modules.

    """
    def __init__(self):
        self.write_output_timer = Timer("output writting")
        self._start_time = None
        self.thread_bm_queue = Queue()
        self.num_threads = Value("i")
        self.got_all_results = Event()
        self.result_fetch_timer = Timer("result fetch")
        self.results_waiting = {}
        self.get_next_doc_timer = Timer("get next doc")
        self.yield_result_timer = Timer("yield result")

    def start_write_output(self):
        self.write_output_timer.start()

    def end_write_output(self):
        self.write_output_timer.end()

    def start(self):
        self._start_time = datetime.now()

    def init_thread(self):
        self.num_threads.value += 1
        bm = DocMapThreadBenchmarker()

        def _get_callback():
            def _callback():
                self.thread_bm_queue.put(bm)
                self.got_all_results.wait()
            return _callback

        return bm, _get_callback()

    def accumulate_threads(self):
        """
        Called at the end to accumulate timings from all threads.

        """
        thread_bms = []
        while len(thread_bms) < self.num_threads.value:
            thread_bms.append(self.thread_bm_queue.get(block=True))
        self.got_all_results.set()
        return DocMapThreadBenchmarker.combine(*thread_bms), len(thread_bms)

    def finish(self):
        """
        Write out benchmarking stats to stdout

        """
        total_time = (datetime.now() - self._start_time).total_seconds()
        thread_bm, num_threads = self.accumulate_threads()

        print("\nBenchmarking stats")
        print("==================\n")
        print("Total execution:          {:.2e}".format(total_time))
        print("Output writing mean time: {:.2e} ({:,}), total {:.2e}"
              .format(self.write_output_timer.mean_time, self.write_output_timer.num_times,
                      self.write_output_timer._total_time))
        print("Time waiting for process output: {:.2e} ({:,}), total {:.2e}"
              .format(self.result_fetch_timer.mean_time, self.result_fetch_timer.num_times,
                      self.result_fetch_timer._total_time))
        print("Time getting next doc name: {:.2e} ({:,}), total {:.2e}"
              .format(self.get_next_doc_timer.mean_time, self.get_next_doc_timer.num_times,
                      self.get_next_doc_timer._total_time))
        print("Time yielding result:     {:.2e} ({:,}), total {:.2e}"
              .format(self.yield_result_timer.mean_time, self.yield_result_timer.num_times,
                      self.yield_result_timer._total_time))
        print("Stats from {} threads".format(num_threads))
        print("Worker wait for input:    {:.2e} ({:,}), total {:.2e}"
              .format(thread_bm.wait_for_input_timer.mean_time, thread_bm.wait_for_input_timer.num_times,
                      thread_bm.wait_for_input_timer._total_time))
        print("Worker process doc:       {:.2e} ({:,}), total {:.2e}"
              .format(thread_bm.process_doc_timer.mean_time, thread_bm.process_doc_timer.num_times,
                      thread_bm.process_doc_timer._total_time))
        print("Worker queue output:      {:.2e} ({:,}), total {:.2e}"
              .format(thread_bm.queue_output_timer.mean_time, thread_bm.queue_output_timer.num_times,
                      thread_bm.queue_output_timer._total_time))
        print()


class NoOpThreadBenchmarker(object):
    def __init__(self):
        self.wait_for_input_timer = NoOpTimer("worker waiting for input")
        self.process_doc_timer = NoOpTimer("process doc")
        self.queue_output_timer = NoOpTimer("queue output")

    def start_worker_wait_for_input(self):
        pass

    def end_worker_wait_for_input(self):
        pass

    def start_process_doc(self):
        pass

    def end_process_doc(self):
        pass


class NoOpBenchmarker(object):
    def __init__(self):
        self.write_output_timer = NoOpTimer("output writting")
        self.result_fetch_timer = NoOpTimer("result fetch")
        self.yield_result_timer = NoOpTimer("yield result")
        self.get_next_doc_timer = NoOpTimer("get next doc")

    def start(self):
        pass

    def init_thread(self):
        return NoOpThreadBenchmarker(), lambda: None

    def accumulate_threads(self):
        return NoOpThreadBenchmarker()

    def finish(self):
        pass



if BENCHMARK_DOC_MAP_MODULES:
    # Perform benchmarking when a doc map module is run
    print("WARNING: Benchmarking doc map modules: this should not be used at production time")
    benchmarker = DocMapBenchmarker()
else:
    # No benchmarking
    benchmarker = NoOpBenchmarker()
