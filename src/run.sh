bash run_pruning.sh

python3 find_best_conf.py $target True ../xdb
python3 find_best_conf.py $target False ../xdb
python3 get_recommended_configurations.py ../xdb $target