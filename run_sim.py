#!/usr/env python

import Configuration
import json
import sys
import os
import shutil
import subprocess
import time
import xboa.common

SCRIPT_NAME = 'simulate_beam.py'
DESTINATION = '/work/ast/cr67/mc'
DELTA_T = 60 # 60
N_SPILLS = 200 # 200
N_JOBS = 100 # 100

def move_geometry(data_dir):
    config = open(data_dir+'/0/config.py')
    config_json = Configuration.Configuration().\
                                          getConfigJSON(config_file=config)
    config_json = json.loads(config_json)
    geometry = os.path.split(config_json['simulation_geometry_filename'])[0]
    print '    ... Copying geometry', geometry, 'to', data_dir
    target = geometry.split('/')[-1]
    shutil.copytree(geometry, data_dir+'/'+geometry)
    print '    ... done'

def dir_name(seed):
    target_dir = 'data/'+str(seed)+'/'
    #time.sleep(1)
    return target_dir

def is_scarf():
    uname = subprocess.check_output(['uname', '-a'])
    return 'scarf.rl.ac.uk' in uname

def run_sim(run_number, unique_id, job):
    global SCRIPT_NAME, N_SPILLS
    run_number = str(run_number)
    out_dir = dir_name(unique_id)
    geo_path_in = os.path.join('config_'+run_number+'.in')
    geo_path_out = os.path.join(out_dir, 'config.py')
    here = os.getcwd()
    run_str = str(run_number).rjust(5, '0')
    for target in ['geometry_'+run_str, SCRIPT_NAME]:
        os.symlink(os.path.join(here, target), os.path.join(out_dir, target))
    xboa.common.substitute(geo_path_in, geo_path_out, job)
    log_name = 'simulation.log'
    run = ['python', SCRIPT_NAME,
           '--configuration_file', 'config.py',
           '--spill_generator_number_of_spills', str(N_SPILLS),
           '--maximum_number_of_steps', str(200000),
           '--SciFiNPECut', '4.0', # photoelectrons
    ]
    os.chdir(out_dir)
    if is_scarf():
        bsub = ['bsub',
                '-n', '1',
                '-W', '24:00',
                '-q', 'scarf-ibis',
                '-o', log_name,
                '-e', log_name,
                #'-K',
             ]
        run = bsub+run
        log_file = open('simulation_bsub.log', 'w')
    else:
        log_file = open(log_name, 'w')
    subproc = subprocess.Popen(run, stdout=log_file, stderr=subprocess.STDOUT)
    print "Running", unique_id, "with", job, "in process", subproc.pid
    os.chdir(here)
    return subproc

def poll_local(processes):
    _processes_update = []
    for proc in processes:
        if proc.returncode != None:
            sys.stdout.write('x')
        else:
            proc.poll()
            _processes_update.append(proc)
            sys.stdout.write('.')
    return _processes_update

def poll_bjobs():
    global SCRIPT_NAME
    output = subprocess.check_output(['bjobs', '-prw'])
    count = 0
    for line in output.split('\n'):
        if SCRIPT_NAME in line:
            count += 1
    return count

def make_dirs(my_jobs):
    try:
        if os.path.exists('data'):
            shutil.rmtree('data')
            time.sleep(1)
    except OSError:
        pass
    for i, job in enumerate(my_jobs):
        os.makedirs(dir_name(i))
        print i
    for i in range(5):
        print '.'
        time.sleep(1)

def job_list(n_procs):
    job_list = []
    for i in range(0, n_procs):
        job_list.append(
            {'__seed__':i},
        )
    return job_list

def move_data(run_number):
    global DESTINATION
    data_index = 4
    src = 'data'
    remote = None
    while remote == None or os.path.exists(remote) or os.path.exists(remote+'.tar.gz'):
       data_index += 1
       directory = str(run_number)+"_v"+str(data_index)
       remote = DESTINATION+'/'+directory
    shutil.copytree(src, remote)
    print '    ... saved in', remote
    shutil.rmtree(src)
    print '    ... cleaned'

def main(run_number, number_of_jobs, number_of_concurrent_processes):
    run_number = int(run_number)
    jobs = job_list(number_of_jobs)
    print 'Running', run_number, 'with', len(jobs), 'jobs; on scarf?', is_scarf()
    make_dirs(jobs)
    print 'Built directories'
    timer = 0
    processes = []
    bjobs = 0
    unique_id = 0
    while len(processes) > 0 or len(jobs) > 0 or bjobs > 0:
        while len(processes) < number_of_concurrent_processes and len(jobs) > 0:
            job = jobs.pop(0)
            processes.append(run_sim(run_number, unique_id, job))
            unique_id += 1
        print timer, '    ',
        processes = poll_local(processes)
        if is_scarf():
            bjobs = poll_bjobs()
        print bjobs
        timer += DELTA_T
        time.sleep(DELTA_T)
    unique_id = 0
    try:
        print subprocess.check_output(['bjobs'])
    except OSError:
        pass # not on scarf
    print "\nFinished simulation... moving to clean data"
    move_data(run_number)
    print "Done"

if __name__ == "__main__":
    if is_scarf():
        n_procs = min(N_JOBS, 100)
    else:
        n_procs = 3
    if len(sys.argv) <= 1:
        print "Usage:\n    python run_sim.py <run1> <run2> <run3>"
    for item in sys.argv[1:]:
        print item,
    print
    for run_number in sys.argv[1:]:
        main(run_number, N_JOBS, n_procs)

