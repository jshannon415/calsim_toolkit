"""
Summary
-------
This application allows a user to run a CalSim study in Python.

Example
-------
Execute the following code to run a CalSim3 study.

>>> from calsim_toolkit.apps import run_CalSim
>>> lf = 'CalSim3/Existing.launch'
>>> run_CalSim.run_CalSim(lf)

"""
# %% Import libraries.
# Import standard libraries.
import os
import glob
import json
import subprocess as sb
import datetime as dt
import argparse
# Import custom modules.
try:
    import custom_modules
    from clean_CalSim import clean_CalSim
    from tools.variables import external_apps_config
except(ModuleNotFoundError):
    from .clean_CalSim import clean_CalSim
    from ..tools.variables import external_apps_config


# %% Define functions.
def WRIMS_config():
    """
    Summary
    -------
    Function to configure Python's connection to WRIMS.

    Returns
    -------
    WRIMS : path
        Configured directory path of WRIMS application.
    launch_group_file : path
        File path of grouped launch files as input into WRIMS *.bat
        applications.
    settings_file : path
        File path to settings for WRIMS application.

    """
    # Obtain WRIMS application directory.
    WRIMS = external_apps_config(app='wrims')
    # Obtain launch group file.
    launch_group_file = os.path.join(WRIMS, r'batchrun/LaunchFileGroup.lfg')
    launch_group_file = os.path.realpath(launch_group_file)
    # Obtain settings file.
    settings_file = os.path.join(WRIMS, r'data/setting.prf')
    settings_file = os.path.realpath(settings_file)
    # Return paths.
    return WRIMS, launch_group_file, settings_file


def WRIMS_settings(settings_file, solver='CBC', memory=4096, cycles=False,
                   cycle_list=[]):
    """
    Summary
    -------
    A function to write settings for WRIMS.

    Parameters
    ----------
    settings_file : path
        File path to settings for WRIMS application; an return of
        `WRIMS_config`.
    solver : string, default 'CBC', optional
        CalSim Solver; choose either 'xa' or 'cbc'. This variable is not case
        sensitive.
    memory : integer, default 4096, optional
        Memory allocated for WRIMS to utilize, in Megabytes (MB); provide a
        multiple of 64 for efficient use of 64-bit computer resources.
    cycles : boolean, default False, optional
        Option to write CalSim cycle solutions to output *.dss file.
    cycle_list : list of integers, default [], optional,
        List of specific CalSim cycle solutions to write to output *.dss file.
        If list is empty and `cycles` = True, then all cycle solutions are
        written to output *.dss file.

    Returns
    -------
    _ : int
        The value of 0 is returned to indicate success.

    """
    # Initialize variables.
    solver_options = ['XA', 'CBC']
    options_list = list()
    # Add solver to options.
    if solver.upper() not in solver_options:
        msg = 'Invalid solver specified.'
        raise RuntimeError(msg)
    options_list.append(solver.upper())
    # Add memory allocation to options.
    if not isinstance(memory, int):
        msg = 'Allocated memory must be an integer value in MB.'
        raise RuntimeError(msg)
    if memory > 8192:
        msg = 'Allocated memory exceeds built-in cap of 8 GB.'
        raise RuntimeError(msg)
    options_list.append(str(memory))
    # Set cycle solution options.
    if cycles:
        options_list.append('true')
        if cycle_list:
            options_list.append('false')
            if not all(isinstance(n, int) for n in cycle_list):
                msg = '`cycle_list` provided must be list of integers.'
                raise RuntimeError(msg)
            cycle_num = ', '.join([str(x) for x in cycle_list])
            options_list.append("'{}'".format(cycle_num))
        else:
            options_list.append('true')
            options_list.append("''")
    else:
        options_list.append('false')
        options_list.append('true')
        options_list.append("''")
    # Write settings to file.
    options = '\n'.join(options_list)
    with open(settings_file, 'w') as f:
        f.write(options)
    # Return success indicator.
    return 0


def main(lf, run_parallel=False, run_bat=True, **kwargs):
    # TODO: Add options to modify launch file.
    """
    Summary
    -------
    A function to run CalSim studies through WRIMS *.bat files.

    Parameters
    ----------
    lf : path or list of paths
        Absolute or relative file path(s) to CalSim *.launch file(s). If a
        study directory is provided, this function will search for all *.launch
        files in the directory, but not in any subdirectories.
    run_parallel : bool, default False, optional
        Option to run multiple CalSim studies in parallel. Default option is to
        run CalSim studies in sequential order.
    run_bat : bool, default True, optional
        Option to not run CalSim studies. This option is intended for debugging
        the function.
    **kwargs : optional
        Keyword arguments to pass to the `WRIMS_settings` function.

    Returns
    -------
    _ : int
        The value of 0 is returned to indicate success. Intermediate messages
        are printed to console to indicate when processes are complete.

    """
    # TODO: Start here to re-write code!
    # <JAS 2019-10-09>
    # Initialize variables.
    solver_opts = ['XA', 'CBC']
    # Get WRIMSv2 configuration paths.
    WRIMS, launch_group_file, settings_file = WRIMS_config()
    # Modify settings.
    WRIMS_settings(settings_file, **kwargs)
    # Prepare list of launch files.
    if isinstance(lf, list):
        launch_files = lf
    elif os.path.isdir(lf):
        launch_files = glob.glob(os.path.join(lf, '*.launch'))
    else:
        launch_files = [lf]
    launch_files = [x for x in launch_files if 'wsi' not in x.lower()]
    for i, f in enumerate(launch_files):
        launch_files[i] = os.path.realpath(f)
        if not os.path.exists(f):
            msg = 'Path {} does not exist'.format(f)
            raise RuntimeError(msg)
    # Run CalSim studies in parallel or sequence.
    if run_parallel:
        # Connect to parallel engine.
        CalSim = os.path.join(WRIMS, r'batchrun/ParallelBatchRun.bat')
        CalSim = os.path.realpath(CalSim)
        if os.path.exists(CalSim):
            work_dir = os.path.dirname(CalSim)
        else:
            err_msg = 'File not found: ' + CalSim
            raise ValueError(err_msg)
        # Break list of *.launch files into packets.
        chunk = 5
        data_packet = [launch_files[i:i + chunk]
                       for i in range (0, len(launch_files), chunk)]
        for packet in data_packet:
            # Write *.launch files to *.lfg file.
            with open(launch_group_file, 'w') as file:
                file.write('\n'.join(packet))
            # Run subprocess.
            if run_bat:
                t0 = dt.datetime.now()
                process = sb.run(CalSim, cwd=work_dir)
                t1 = dt.datetime.now()
                if process.returncode != 0:
                    print('CalSim Subprocess Failed.')
                else:
                    print('CalSim Subprocess Complete!')
                t_process = t1 - t0
                print('Parallel Process Time', t_process, sep=': ')
    else:
        # Connect to sequential engine.
        CalSim = os.path.join(WRIMS, r'batchrun/SequentialBatchRun.bat')
        CalSim = os.path.realpath(CalSim)
        if os.path.exists(CalSim):
            work_dir = os.path.dirname(CalSim)
        else:
            err_msg = 'File not found: ' + CalSim
            raise ValueError(err_msg)
        # Write *.launch files to *.lfg file.
        with open(launch_group_file, 'w') as file:
            file.write('\n'.join(launch_files))
        # Run subprocess.
        if run_bat:
            t0 = dt.datetime.now()
            p_args = r'jre\bin\java -Djava.library.path="lib" -cp "dropins\wrimsv2_plugin_1.0.0.0.jar;lib\xml.jar;lib\xmlbeans-2.3.0.jar;lib\hec.jar;lib\hecData.jar;lib\heclib.jar;lib\rma.jar;batchrun\org.eclipse.core.runtime-3.1.0.jar;plugins\org.apache.commons.io_2.0.1.v201105210651.jar;plugins\org.eclipse.debug.core_3.9.1.v20140805-1629.jar;plugins\org.eclipse.osgi_3.10.2.v20150203-1939.jar;plugins\org.eclipse.equinox.common_3.6.200.v20130402-1505.jar;plugins\org.eclipse.core.resources_3.9.1.v20140825-1431.jar;plugins\org.eclipse.ui.workbench_3.106.2.v20150204-1030.jar;plugins\org.eclipse.swt.win32.win32.x86_64_3.103.2.v20150203-1351.jar;plugins\org.eclipse.jface_3.10.2.v20141021-1035.jar" wrimsv2_plugin.batchrun.BatchRunCmd batchrun\LaunchFileGroup.lfg'.split()
            p_args[0] = os.path.join(WRIMS, p_args[0])
            p_args[3] = p_args[3].strip('"')
            # NOTES:
            #   1. If subprocess has additional arguments to pass, then
            #      `p_args` must be a list (safe) or sb.run must have 
            #       shell=True (not safe).
            #   2. How do I have the subprocess output in the same Python
            #      window? I recall doing this with HEC5Q; something related to
            #      creationflags=sb.CREATE_NEW_CONSOLE. It is just nice to
            #      know. In reality, it would be better to open a separate
            #      window to control workflow. Perhaps it can be an option for
            #      the end user to specify.
            #   3. Even when this code is updated, Hao still needs to return
            #      error codes when WRIMS is interrupted.
            #   4. If I do not strip p_args[3] of the quotations, the
            #      subprocess does return a code of "1".
            process = sb.run(p_args, cwd=WRIMS, capture_output=True)
            print('Return Code', process.returncode, sep=': ')
            t1 = dt.datetime.now()
            if process.returncode != 0:
                print('CalSim Subprocess Failed.')
            else:
                print('CalSim Subprocess Complete!')
            t_process = t1 - t0
            print('Series Process Time', t_process, sep=': ')
    # Clean the study of temporary processing files.
    study_dir = list()
    for f in launch_files:
        s_dir = os.path.dirname(f)
        study_dir.append(s_dir)
    study_dir = list(set(study_dir))
    for s in study_dir:
        _ = clean_CalSim(s)
    # Return completion indicator.
    return 0


# %% Execute script.
if __name__ == '__main__':
    # Initialize argument parser.
    intro = '''
            This module runs CalSim studies in Python using the WRIMS *.bat
            files.
            '''
    parser = argparse.ArgumentParser(description=intro)
    # Add positional arguments to parser.
    parser.add_argument('lf', metavar='launch files', type=str, nargs='+',
                        help='''
                             Absolute or relative file path(s) to CalSim
                             *.launch file(s). If a study directory is
                             provided, this function will search for all
                             *.launch files in the directory, but not in any
                             subdirectories.
                             ''')
    # Add optional arguments.
    parser.add_argument('-p', '--parallel', action='store_true', default=False,
                        help='''
                             Option to run multiple CalSim studies in parallel.
                             Default option is to run CalSim studies in
                             sequential order.
                             ''')
    parser.add_argument('-n', '--no-run_bat', dest='run_bat',
                        action='store_false', default=True,
                        help='''
                             Option to not run CalSim studies. This option is
                             intended for debugging the function.
                             ''')
    parser.add_argument('-s', '--solver', metavar='solver', type=str, nargs='?',
                        default='cbc',
                        help='''
                             CalSim Solver; choose either 'xa' or 'cbc'. This
                             variable is not case sensitive.
                             ''')
    parser.add_argument('-m', '--memory', metavar='memory', type=int,
                        nargs='?', default=4096,
                        help='''
                             Memory allocated for WRIMS to utilize, in
                             Megabytes (MB); provide a multiple of 64 for
                             efficient use of 64-bit computer resources.
                             ''')
    parser.add_argument('-c', '--cycles', action='store_true', default=False,
                        help='''
                             Option to write CalSim cycle solutions to output
                             *.dss file.
                             ''')
    parser.add_argument('-l', '--cycle_list', metavar='cycle list', type=int,
                        nargs='*', default=[],
                        help='''
                             List of specific CalSim cycle solutions to write
                             to output *.dss file. If list is empty and
                             `cycles` = True, then all cycle solutions are
                             written to output *.dss file.
                             ''')
    # Parse arguments.
    args = parser.parse_args()
    lf = args.lf
    for i, f in enumerate(lf):
        fp = f.strip('"')
        lf[i] = fp
    lf = lf[0] if len(lf) == 1 else lf
    run_parallel = args.parallel
    run_bat = args.run_bat
    solver = args.solver.strip('"')
    memory = args.memory
    cycles = args.cycles
    cycle_list = args.cycle_list
    # Pass arguments to function.
    _ = main(lf, run_parallel=run_parallel, run_bat=run_bat, solver=solver,
             memory=memory, cycles=cycles, cycle_list=cycle_list)
