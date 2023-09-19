cd MQSim
make clean
make -j 16
cd ..

cd src
python3 download.py
cd ..

unzip autoblox_traces.zip
mv autoblox_traces/* .
rm -r autoblox_traces/

unzip xdb_base.zip
cd src/
bash setup_xdb.sh