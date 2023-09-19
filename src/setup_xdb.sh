export xdb_dir=../xdb
mkdir $xdb_dir
mv ../xdb_base $xdb_dir
cd $xdb_dir
# pruning exps
mkdir coarsed_pruning
cd coarsed_pruning
mkdir configurations
mkdir dram_trace
mkdir warmup
mkdir workloads
cp ../../utils/baseline_nvmemlc/* configurations
cp ../xdb_base/warmup/* warmup
cp ../xdb_base/status_file/* .
cd ..
mkdir coarsed_pruning_layout
cd coarsed_pruning_layout
mkdir configurations
mkdir dram_trace
mkdir warmup
mkdir workloads
cp ../../utils/baseline_nvmemlc/* configurations
cp ../xdb_base/warmup/* warmup
cp ../xdb_base/status_file/* .
cd ..
mkdir fine_grained_pruning
cd fine_grained_pruning
mkdir configurations
mkdir dram_trace
mkdir warmup
mkdir workloads
cp ../../utils/baseline_nvmemlc/* configurations
cp ../xdb_base/warmup/* warmup
cp ../xdb_base/status_file/* .
cd ..
mkdir nvme_mlc_TPCC_0
cd nvme_mlc_TPCC_0
mkdir configurations
mkdir dram_trace
mkdir warmup
mkdir workloads
cp ../../utils/baseline_nvmemlc/* configurations
cp ../xdb_base/warmup/* warmup
cp ../xdb_base/status_file/* .
cd ..
mkdir nvme_mlc_YCSB_0
cd nvme_mlc_YCSB_0
mkdir configurations
mkdir dram_trace
mkdir warmup
mkdir workloads
cp ../../utils/baseline_nvmemlc/* configurations
cp ../xdb_base/warmup/* warmup
cp ../xdb_base/status_file/* .
cd ..
mkdir nvme_mlc_WebSearch_0
cd nvme_mlc_WebSearch_0
mkdir configurations
mkdir dram_trace
mkdir warmup
mkdir workloads
cp ../../utils/baseline_nvmemlc/* configurations
cp ../xdb_base/warmup/* warmup
cp ../xdb_base/status_file/* .
cd ..
mkdir nvme_mlc_LiveMapsBackEnd_0
cd nvme_mlc_LiveMapsBackEnd_0
mkdir configurations
mkdir dram_trace
mkdir warmup
mkdir workloads
cp ../../utils/baseline_nvmemlc/* configurations
cp ../xdb_base/warmup/* warmup
cp ../xdb_base/status_file/* .
cd ..
mkdir nvme_mlc_AdspayLoad_0
cd nvme_mlc_AdspayLoad_0
mkdir configurations
mkdir dram_trace
mkdir warmup
mkdir workloads
cp ../../utils/baseline_nvmemlc/* configurations
cp ../xdb_base/warmup/* warmup
cp ../xdb_base/status_file/* .
cd ..
mkdir nvme_mlc_CloudStorage_0
cd nvme_mlc_CloudStorage_0
mkdir configurations
mkdir dram_trace
mkdir warmup
mkdir workloads
cp ../../utils/baseline_nvmemlc/* configurations
cp ../xdb_base/warmup/* warmup
cp ../xdb_base/status_file/* .
cd ..
mkdir nvme_mlc_MapReduce_0
cd nvme_mlc_MapReduce_0
mkdir configurations
mkdir dram_trace
mkdir warmup
mkdir workloads
cp ../../utils/baseline_nvmemlc/* configurations
cp ../xdb_base/warmup/* warmup
cp ../xdb_base/status_file/* .
cd ..
mkdir nvme_mlc_TPCC_1
cd nvme_mlc_TPCC_1
mkdir configurations
mkdir dram_trace
mkdir warmup
mkdir workloads
cp ../../utils/baseline_nvmemlc/* configurations
cp ../xdb_base/warmup/* warmup
cp ../xdb_base/status_file/* .
cd ..
mkdir nvme_mlc_YCSB_1
cd nvme_mlc_YCSB_1
mkdir configurations
mkdir dram_trace
mkdir warmup
mkdir workloads
cp ../../utils/baseline_nvmemlc/* configurations
cp ../xdb_base/warmup/* warmup
cp ../xdb_base/status_file/* .
cd ..
mkdir nvme_mlc_WebSearch_1
cd nvme_mlc_WebSearch_1
mkdir configurations
mkdir dram_trace
mkdir warmup
mkdir workloads
cp ../../utils/baseline_nvmemlc/* configurations
cp ../xdb_base/warmup/* warmup
cp ../xdb_base/status_file/* .
cd ..
mkdir nvme_mlc_LiveMapsBackEnd_1
cd nvme_mlc_LiveMapsBackEnd_1
mkdir configurations
mkdir dram_trace
mkdir warmup
mkdir workloads
cp ../../utils/baseline_nvmemlc/* configurations
cp ../xdb_base/warmup/* warmup
cp ../xdb_base/status_file/* .
cd ..
mkdir nvme_mlc_AdspayLoad_1
cd nvme_mlc_AdspayLoad_1
mkdir configurations
mkdir dram_trace
mkdir warmup
mkdir workloads
cp ../../utils/baseline_nvmemlc/* configurations
cp ../xdb_base/warmup/* warmup
cp ../xdb_base/status_file/* .
cd ..
mkdir nvme_mlc_CloudStorage_1
cd nvme_mlc_CloudStorage_1
mkdir configurations
mkdir dram_trace
mkdir warmup
mkdir workloads
cp ../../utils/baseline_nvmemlc/* configurations
cp ../xdb_base/warmup/* warmup
cp ../xdb_base/status_file/* .
cd ..
mkdir nvme_mlc_MapReduce_1
cd nvme_mlc_MapReduce_1
mkdir configurations
mkdir dram_trace
mkdir warmup
mkdir workloads
cp ../../utils/baseline_nvmemlc/* configurations
cp ../xdb_base/warmup/* warmup
cp ../xdb_base/status_file/* .
cd ..