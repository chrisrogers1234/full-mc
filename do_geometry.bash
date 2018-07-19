#!/bin/bash
# Now get the run data
if [ "$#" -gt 0 ]; then
    # if there are command line arguments it should be a list of run numbers
    # eventually this becomes a load test (but online recon is failing right now)
    run_list=$@
fi
for run in ${run_list}
do
    export geometry_run=${run}
    export geometry_dir=geometry_${geometry_run}
    rm -r ${geometry_dir}
    mkdir ${geometry_dir}
    python ${MAUS_ROOT_DIR}/bin/utilities/download_geometry.py --geometry_download_by run_number --geometry_download_directory ${geometry_dir} --geometry_download_run ${geometry_run} --cdb_download_url "http://cdb.mice.rl.ac.uk/cdb/"
done

exit 0

#--geometry_download_by "id" --geometry_download_id 184 --cdb_download_url "http://preprodcdb.mice.rl.ac.uk/cdb/" --geometry_download_directory ${geometry_dir}

