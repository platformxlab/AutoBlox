# AutoBlox_Artifact

Artifact of paper Learning to Drive Software-Deﬁned Solid-State Drives to appear in MICRO'23.

## Artifact Introduction

AutoBlox is a learning framework to assist the design of Software-Defined SSDs. Specifically, AutoBlox can efficiently identify optimized configurations for target workloads with constraints (Host Interface, Capacity, Power).

## Dependencies Installation 

AutoBlox requires psutil, scikit-learn, numpy and seaborn packages. 

Please run the following script to install dependencies (requires sudo permission).

```
sudo bash cloudlab_server_setup_instructions.sh
```

## Dependencies Compilation

Please run the following script to compile MQSim.

```
cd MQSim
make clean
make -j 16
cd ..
```

## Trace Downloading and Installation

Please download the traces from this link: https://drive.google.com/uc?export=download&id=1O4wzIwWgTmc9Xgt5dgrg6ctH68AoKcTJ, and download the baseline configuration and the warmup files from this link: https://drive.google.com/file/d/1ha25yZPiIT2U_9i3tI9w9uL5oM3fsKbE/view?usp=drive_link.

You can also use the download script:

```
cd src
python3 download.py
cd ..
```

unzip the traces in AutoBlox_Artifact directory:

```
unzip autoblox_traces.zip
```

Then, move all the folders into the root directory:

```
mv autoblox_traces/* .
rm -r autoblox_traces/
```

## Running the Experiments


Before running the experiments, you first need to set up the xdb Tables. First unzip the configuration files into the root directory, and setup xdb with it:

```
unzip xdb_base.zip
cd src/
bash setup_xdb.sh
```

The xdb directory is automatically set to the root directory of AutoBlox. If you wish to build your own xdb, please change the xdb directory in setup_xdb.sh file. For artifact reviewers, the setup on CloudLab is different; please take a look at the CloudLab account we provided.

Then, you can start reproducing the figures.

### Workload Clustering (Figure 2)

To reproduce Figure 2 in the paper, please run the following scripts in src/ folder: 

```
python3 clustering_motivation.py
cd ../reproduced_dat
python3 clustering.py
```

The workload clustering figure will appear in reproduced_dat folder. This experiment will demonstrate that AutoBlox can efficiently identify new workloads.


### Fine-grained and Coarsed-grained Pruning (Figure 3 and Figure 4)

To reproduce Figure 3 and Figure 4,  please run this in src/ folder:

```
export target="target_workload"
bash run_pruning.sh
```

Here target_workload has 7 options (YCSB, TPCC, AdspayLoad, MapReduce, LiveMapsBackEnd, WebSearch, and CloudStorage). It takes approximately 2-4 hour for each workload to finish its pruning. To speed up the experiments, we will provide you several CloudLab nodes to run the pruning experiments in parallel. If you are an artifact reviewer, please get in touch with us to gain access to the CloudLab nodes. Note that you must change the xdb directory in generate_* and get_* files.

After the pruning is finished, please run

```
cd reproduced_dat/
python3 fine_grained_pruning.py
python3 coarsed_pruning.py
```

After that,  Figure 3 and Figure 4 will appear in the reproduced_dat folder.

### Learning (reproduce Table 1, Figure 7, and Figure 8)

After reproducing Figure 3 and 4, please run the following script to get the tuning_order data for the training phase.

```
./get_tuning_order.sh
```


Give a type of workloads, we will train the models and learn the SSD parameters with and without tuning order respectively, please use the following scripts: 

```
cd src
find_best_conf.py target_workload use_tuning_order xdb_directory
```

Here target_workload has 7 options (YCSB, TPCC, AdspayLoad, MapReduce, LiveMapsBackEnd, WebSearch, and CloudStorage); use_tuning_order has two options (True and False); and xdb_directory is the xdb database used in AutoBlox(e.g. ../xdb). Since it will take approximately 18 hour to finish the learning of each workload, we will provide several CloudLab nodes to run the learning in parallel.

After the learning, the experimental results will be placed in the xdb/ folder. 

To reproduce Table 1, please run the following script:

```
python3 get_recommended_configurations.py xdb_directory target_workload
```

You can use target_workload = (YCSB, TPCC, AdspayLoad, MapReduce, LiveMapsBackEnd, WebSearch, CloudStorage, and ALL) to generate partial Table for each of the workloads. To generate Figure 8, you need to use TPCC or ALL.

Table 1 should show up in the reproduced_dat folder. Note that because part of the ML model requries random search, the performance improvement may have less than 10\% deviation.

To plot the learning procedure as shown in Figure 7 and Figure 8, please run: 

```
cd ../reproduced_dat
python3 learning_profile.py
python3 tuning_time.py
```

Figure 7 and 8 should appear in reproduce_dat/ folder. This figure shows that with enforced tuning order, AutoBlox can accelerate the training procedure. Note that because of the randomness in the ML model,  the Figure 7, 8 may not look exactly like that in the paper, but it should show that with enforced tuning order, AutoBlox can accelerate and simplify the tuning procedure.



