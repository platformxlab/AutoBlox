import os
import time
from evaluate_target_conf import generate_config_workload, save_to_xdb, get_performance_from_xml, evaluate_config_workload, generate_queuetest_config_workload

# proccesses in progress

def batch_exec(confdir, tracedir, confs, tracenames):
    confnames = [(confdir + "/" + fname) for fname in confs]
    tracenames = [(tracedir + "/" + fname) for fname in tracenames if fname in os.listdir(tracedir)]

    ### generate jobs pairs for regular test
    unfinished_jobs = []
    for i in range(len(confnames)):
        for j in range(len(tracenames)):
            temp = generate_config_workload(confnames[i], tracenames[j])
            if temp:
                unfinished_jobs.append(temp)

    procs = {}

    import subprocess
    import psutil

    PARALLELISM = 40
    BASE_PATH = "./"

    ongoing_warmup_jobs = []
    finished_warmup_jobs = []
    warmup_waiters = {}

    start_time = time.time()
    # issue unfinished jobs, try to fully utilize the memory and cpus
    while len(unfinished_jobs) > 0 or len(procs) > 0 or len(warmup_waiters) > 0:
        exit_codes = {proc:proc.poll() for proc in procs}
        finished_procs = [proc for proc, ec in exit_codes.items() if ec is not None]
        if len(finished_procs) > 0:
            for finished in finished_procs:
                print(f"Finished job {finished.pid}")
                returnval = finished.wait()
                if len(procs[finished]) == 2:
                    warmup_jobid = " ".join(procs[finished][0][0].split(" ")[0:-1])
                    if warmup_jobid in ongoing_warmup_jobs:
                        if warmup_jobid in warmup_waiters:
                            unfinished_jobs += warmup_waiters[warmup_jobid]
                            print(f"finished Warmup Job {warmup_jobid}, releasing waiting queue= {len(warmup_waiters[warmup_jobid])}!")
                            del warmup_waiters[warmup_jobid]
                        ongoing_warmup_jobs.remove(warmup_jobid)
                        finished_warmup_jobs.append(warmup_jobid)
                    subprocess.call(procs[finished][0][1], shell=True)
                    unfinished_jobs.append(procs[finished][1:])
                    del procs[finished]
                elif len(procs[finished]) == 1:
                    subprocess.call(procs[finished][0][1], shell=True)
                    del procs[finished]
        else:
            time.sleep(1)
        # if OOM, kill a new process
        while psutil.virtual_memory().percent >= 90.0:
            print(f"Memory Usage: {psutil.virtual_memory().percent}%")
            # mem, proc = max([(psutil.Process(proc.pid).memory_info().rss, proc) for proc in procs], key=lambda x: x[0])
            create_time, proc = max([(psutil.Process(proc.pid).create_time(), proc) for proc in procs], key=lambda x: x[0])
            mem = psutil.Process(proc.pid).memory_info().rss
            unfinished_jobs.append(procs[proc])
            if len(procs[proc]) == 2:
                warmup_jobid = " ".join(procs[proc][0][0].split(" ")[0:-1])
                if warmup_jobid in ongoing_warmup_jobs:
                    ongoing_warmup_jobs.remove(warmup_jobid)
            print(f"Killing job {proc.pid} due to OOM and release {mem / 1024} MB memory")
            print(f"# of Unfinished jobs {len(unfinished_jobs)}")
            subprocess.call("kill -9 %d" % (proc.pid), shell=True)
            subprocess.call("kill -9 %d" % (proc.pid + 1), shell=True)
            subprocess.call("kill -9 %d" % (proc.pid + 2), shell=True)
            time.sleep(10)
            del procs[proc]
        while len(procs) < PARALLELISM and len(unfinished_jobs) > 0 and psutil.virtual_memory().percent <= 75.0:
            print(f"# Popping from Unfinished jobs of {len(unfinished_jobs)}")
            next_job = unfinished_jobs.pop(0)
            if len(next_job) == 2:
                warmup_jobid = " ".join(next_job[0][0].split(" ")[0:-1])
                if warmup_jobid in ongoing_warmup_jobs:
                    if not warmup_jobid in warmup_waiters:
                        warmup_waiters[warmup_jobid] = []
                    warmup_waiters[warmup_jobid].append(next_job[1:])
                    print("Waiting for existing Warmup Job!")
                    continue
                else:
                    ongoing_warmup_jobs.append(warmup_jobid)
                    proc = subprocess.Popen(["timeout 6000 " + next_job[0][0]], cwd=BASE_PATH, shell=True)
                    procs[proc] = next_job
                    print(f"Running job {proc.pid}: {next_job}")
                    print(next_job[0][0])
            elif len(next_job) == 1:
                proc = subprocess.Popen(["timeout 6000 " + next_job[0][0]], cwd=BASE_PATH, shell=True)
                procs[proc] = next_job
                print(f"Running job {proc.pid}: {next_job}")
                print(next_job[0][0])
            time.sleep(5)
        if len(unfinished_jobs) > 0 or len(warmup_waiters) > 0:
            print(f"unfinished jobs {len(unfinished_jobs)}, warmup waiters {len(warmup_waiters)}\n")
            time.sleep(30)
    end_time = time.time()
    print("BATCH EXECUTION FINISHED!")
    print("finish time:")
    print(end_time - start_time)

if __name__ == "__main__":
    import sys

    print ('Number of arguments:', len(sys.argv), 'arguments.')
    print ('Argument List:', str(sys.argv))

    if len(sys.argv) != 3:
        print("Usage: batch_evaluation.py exp_name target_name")
        exit()
    exp_name = sys.argv[1]
    target_name = sys.argv[2]

    if exp_name == "Coarsed_Layout":
        confdir = "../xdb/coarsed_pruning_layout/configurations"
        tracedir = "../test_traces"
        confs = [conf for conf in os.listdir(confdir)]
    elif exp_name == "Coarsed_Non_Layout":
        confdir = "../xdb/coarsed_pruning/configurations"
        tracedir = "../test_traces"
        confs = [conf for conf in os.listdir(confdir)]
    elif exp_name == "Fine_Grained":
        confdir = "../xdb/fine_grained_pruning/configurations"
        tracedir = "../test_traces"
        confs = [conf for conf in os.listdir(confdir)]
    else:
        print("No Matching exp_name.")
        exit()
    
    if target_name in ["LiveMapsBackEnd", "TPCC", "AdspayLoad", "WebSearch", "YCSB", "MapReduce", "CloudStorage"]:
        tracenames = []
        for trace in os.listdir(tracedir):
            if trace.startswith(target_name + "-") and not trace.endswith("-0-0-0"):
                tracenames.append(trace)
    else:
        print("No Matching target_name.")
        exit()
    batch_exec(confdir, tracedir, confs, tracenames)

# confdir = "/mnt/nvme1n1/daixuan2/xdb/coarsed_pruning/configurations"
# tracedir = "../val_traces"
# confs = [conf for conf in os.listdir(confdir)]
# traces = []
# traces += [f"LiveMapsBackEnd-1-0-{i}" for i in range(8, 10)]
# traces += [f"YCSB-0-0-{i}" for i in range(2, 3)]
# traces += [f"TPCC-{i}-0-0" for i in range(1, 2)]
# traces += [f"MapReduce-{i}-0-0" for i in range(1, 2)]
# traces += [f"AdspayLoad-0-0-{i}" for i in range(2, 3)]
# traces += [f"CloudStorage-{i}-0-0" for i in range(6, 7)]
# traces += [f"WebSearch-{i}-0-0" for i in range(1, 2)]

# batch_exec(confdir, tracedir, confs, traces)

# confdir = "/mnt/nvme1n1/daixuan2/xdb/coarsed_pruning_layout/configurations"
# tracedir = "../val_traces"
# confs = [conf for conf in os.listdir(confdir)]
# tracenames = [trace for trace in os.listdir(tracedir)]

# batch_exec(confdir, tracedir, confs, traces)

# for confname in confnames:
#     for tracename in tracenames:
#         evaluate_config_workload(confname, tracename)

# for confname, queue_size in confnames_queue_list:
#     for tracename in tracenames:
#         evaluate_config_workload(confname, tracename)

# traces = []
# this is for training
# traces += [f"LiveMapsBackEnd-1-0-{i}" for i in range(8, 10)]
# traces += [f"YCSB-0-0-{i}" for i in range(2, 3)]
# traces += [f"TPCC-{i}-0-0" for i in range(1, 2)]
# traces += [f"MapReduce-{i}-0-0" for i in range(1, 2)]
# traces += [f"AdspayLoad-0-0-{i}" for i in range(2, 3)]
# traces += [f"CloudStorage-{i}-0-0" for i in range(6, 7)]
# traces += [f"WebSearch-{i}-0-0" for i in range(1, 2)]

# traces += [f"VDI-2-0-0"]
# traces += [f"TPCCTest-1-0-0"]
# traces += [f"YCSBTest-0-0-1"]
# traces += [f"CloudStorageTest-1-0-0", f"CloudStorageTest-2-0-0"]
# traces += [f"FIUHome-0-0-1"]
# traces += [f"RadiusAuth-0-0-1"]

# traces += [f"TPCC-{i}-0-0" for i in range(11, 12)]
# traces += [f"YCSB-0-0-{i}" for i in range(3, 4)]

## Set speed and width of DMA in channel in MT/s
# Width should be 8 or 16
# Typical values from ONFi:
#         ONFi   1.x     2.x   3.x~4.x    4.x
#  Timing Mode   SDR   NV-DDR  NV-DDR2  NV-DDR3
#      0         10      40      67       67
#      1         20      67      80       80
#      2         29     100     133      133
#      3         33     133     167      167
#      4         40     167     200      200
#      5         50     200     267      267
#      6          -       -     333      333
#      7          -       -     400      400
#      8          -       -     533      533
#      9          -       -       -      667
#     10          -       -       -      800
# 1066 MT/s, 1200 MT/s


# traces.remove("VDI-0-0-0")

# Currently use TPCC 11

# this is for testing
# traces += [f"YCSB-0-0-{i}" for i in range(1, 4)]
# traces += [f"TPCC-{i}-0-0" for i in range(1, 4)]
# traces += [f"MapReduce-{i}-0-0" for i in range(1, 3)]
# traces += [f"AdspayLoad-0-0-{i}" for i in range(1, 4)]
# traces += [f"CloudStorage-{i}-0-0" for i in range(1, 10)]
# traces += [f"WebSearch-{i}-0-0" for i in range(1, 3)]
# traces += [f"LiveMapsBackEnd-1-0-{i}" for i in range(1, 10)]

# confs = os.listdir(confdir)

# confs = ["baseline.xml","CS1.xml","CS2.xml","CS3.xml","CS4.xml","CS6.xml","CS7.xml","CS8.xml","CS9.xml","CS10.xml","DB.xml","KV.xml","CS.xml"]
# confs = ["baseline_dram.xml", "RC3_dram.xml", "KV_dram.xml", "DB_dram.xml", "WS11_dram.xml", "CS10_dram.xml", "CS2_dram.xml", "MR_dram.xml"]
# confs = ["baseline.xml"]
# confs = ["DB_DRAM1.xml","DB_DRAM2.xml" ,"DB_DRAM3.xml", "DB_DRAM4.xml", "DB_DRAM5.xml"]
# confs += ["DB_layout1.xml","DB_layout2.xml" ,"DB_layout3.xml", "DB_layout4.xml", "DB_layout5.xml"]
# confs += ["DB_rlatency1.xml", "DB_rlatency2.xml", "DB_rlatency3.xml", "DB_rlatency4.xml", "DB_rlatency5.xml",
        # "DB_wlatency1.xml", "DB_wlatency2.xml", "DB_wlatency3.xml", "DB_wlatency4.xml", "DB_wlatency5.xml"]
# confs = ["DB_wlatency_pcie1.xml","DB_wlatency_pcie2.xml","DB_wlatency_pcie3.xml","DB_wlatency_pcie4.xml","DB_wlatency_pcie5.xml",
        # "DB_qfs1.xml","DB_qfs2.xml","DB_qfs3.xml","DB_qfs4.xml","DB_qfs5.xml"]
# confs = ["DB_wlatency1-1.xml","DB_wlatency1-2.xml","DB_wlatency1-3.xml","DB_wlatency1-4.xml","DB_wlatency1-5.xml"]
# confs = ["DB_wlatency0-1.xml","DB_wlatency0-2.xml","DB_wlatency0-3.xml","DB_wlatency0-4.xml","DB_wlatency0-5.xml"]
# confs = ["DB_final1.xml", "DB_final2.xml", "DB_final3.xml", "DB_final4.xml", "DB_final5.xml"]
# confs = ["KV_final2.xml", "KV_final3.xml","KV_final4.xml"]
# confs = ["LM_final2.xml"]
# confs += [conf for conf in os.listdir(confdir) if conf.startswith("KV")]

# generate jobs pairs for best queue size test
# first, generate configuration-QueueSize pair lists
# conf_queue_list = [["baseline.xml", 4]]
# for qsize in [8, 16, 32, 64, 128, 256]:
#     for conf in confs:
#         newconf = conf.split(".")[0] + "-Q" + str(qsize) + "." + conf.split(".")[1]
#         conf_queue_list.append([newconf, qsize])


# confnames_queue_list = [[confdir + "/" + fname, queuesize] for fname, queuesize in conf_queue_list]

# unfinished_jobs = []
# for i in range(len(confnames_queue_list)):
#     for j in range(len(tracenames)):
#         temp = generate_queuetest_config_workload(confnames_queue_list[i][0], tracenames[j], confnames_queue_list[i][1])
#         if temp:
#             unfinished_jobs.append(temp)
