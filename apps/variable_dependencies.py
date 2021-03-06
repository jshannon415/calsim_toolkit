"""
Summary
-------
For a given variable, list variables that are dependent on it and variables
that feed directly into it.

Examples
--------
An engineer can utilize the variable dependency tool either through the command
line or via Python import. From the command line, pass in additional system
arguments to the Python executable.

>>> python calsim_toolkit/apps/variable_dependencies.py CalSim3 S_SHSTA
Variable Dependency Results for S_SHSTA in study diretory CalSim3...

To import and used the tool, call the `main` function.

>>> from calsim_toolkit.apps import variable_dependencies as vard
>>> _ = vard.main('CalSim3', 'S_SHSTA')
>>> run_CalSim.run_CalSim(lf)
Variable Dependency Results for S_SHSTA in study diretory CalSim3...

"""
# %% Import libraries.
# Import standard libraries.
import os
import sys
import glob
import re
import argparse


# %% Define functions.
def find_statement(code, statement=r'define', var=r'.*?'):
    # Initialize variables.
    re_statement = statement + r'\s+' + var + '\s*?{.*?}'
    # Find matches.
    matches = list(re.finditer(re_statement, code, re.IGNORECASE | re.DOTALL))
    # Return matches.
    return matches


def line_numbers(match, code):
    # Initialize variables.
    start = None
    end = None
    re_lines = r".*\n"
    # Parse lines.
    lines = list(re.finditer(re_lines, code, re.IGNORECASE))
    # Find start and end lines of match in code.
    for i, line in enumerate(lines, 1):
        if line.start() <= match.start() <= line.end():
            start = i
        if line.start() <= match.end() <= line.end():
            end = i
    # Return line numbers.
    return (start, end)


def remove_comments(code):
    # Initialize variables.
    re_cb = r'/\*.*?\*/'
    re_ic = r'!.*(?=\n)'
    # Identify comments in code.
    comments = list(re.finditer(re_cb, code, re.DOTALL))
    comments += list(re.finditer(re_ic, code))
    # Replace comment-occupied space with whitespace.
    temp_code = code
    for comment in comments:
        block1 = temp_code[:comment.start()]
        block2 = ' ' * len(range(*comment.span()))
        block3 = temp_code[comment.end():]
        temp_code = block1 + block2 + block3
    # Return code without comments.
    return temp_code


def remove_cases(code):
    # Initialize variables.
    re_case = r'case.*?{.*?}'
    # Identify comments in code.
    cases = list(re.finditer(re_case, code, re.DOTALL))
    # Replace comment-occupied space with whitespace.
    temp_code = code
    for case in cases:
        block1 = temp_code[:case.start()]
        block2 = ' ' * len(range(*case.span()))
        block3 = temp_code[case.end():]
        temp_code = block1 + block2 + block3
    # Return code without comments.
    return temp_code


def remove_non_variables(code):
    # Initialize variables.
    wresl_keys = ['initial', 'define', 'svar', 'goal', 'group', 'dvar',
                  'integer', 'alias', 'value', 'std', 'kind', 'units',
                  'weight', 'upper', 'lower', 'convert', 'name', 'type',
                  'desc', 'bounds', 'penalty', 'month', 'wateryear', 'always',
                  'never', 'constrain', 'include', 'case', 'condition', 'lhs',
                  'rhs', 'import', 'sequence', 'model', 'order', 'timeseries',
                  'lookup', 'select', 'from', 'where', 'given', 'use', 'sum',
                  'max', 'min', 'abs', 'binary', 'and', 'or', 'cfs', 'taf',
                  'storage', 'diversion', 'flow']
    re_num = r'\b\d\.?\d*\b'
    re_key = r'\b{}\b'
    re_case = r'\bcase.*?{'
    re_cycle = r'\[.+?\]'
    # Identify digits and keys in code.
    matches = list(re.finditer(re_num, code))
    matches += list(re.finditer(re_cycle, code))
    for wresl_key in wresl_keys:
        if wresl_key == 'case':
            matches += list(re.finditer(re_case, code, re.IGNORECASE))
        else:
            re_k = re_key.format(wresl_key)
            matches += list(re.finditer(re_k, code, re.IGNORECASE))
    # Replace match spaces with whitespace.
    temp_code = code
    for match in matches:
        block1 = temp_code[:match.start()]
        block2 = ' ' * len(range(*match.span()))
        block3 = temp_code[match.end():]
        temp_code = block1 + block2 + block3
    # Return code without comments.
    return temp_code


def generate_report(var, study, var_defines, var_inputs, var_depends):
    """
    Summary
    -------
    Internal function to generate report.

    """
    # Initialize variables.
    found_in_line = 'Line {} of {}'
    found_in_lines = 'Lines {} - {} of {}'
    # Initialize report header.
    results = 'Variable Dependency Results for {} in study diretory {}\n'
    results = results.format(var, os.path.abspath(study))
    results += '\n{} is defined in the following locations:\n'.format(var)
    # Identify definition locations of variable.
    for i, var_define in enumerate(var_defines, 1):
        _, file, lines, _ = var_define
        start_line, end_line = lines
        if start_line == end_line:
            var_msg = found_in_line.format(start_line, file)
        else:
            var_msg = found_in_lines.format(start_line, end_line, file)
        results += '{}. {}\n'.format(i, var_msg)
    # Identify variable input locations.
    if var_inputs:
        results += ('\n'
                    'The inputs of {} are defined in the following '
                    'locations:'
                    '\n').format(var)
        for i, var_input in enumerate(var_inputs, 1):
            v, file, lines, _ = var_input
            start_line, end_line = lines
            if start_line == end_line:
                var_msg = found_in_line.format(start_line, file)
            else:
                var_msg = found_in_lines.format(start_line, end_line, file)
            results += '{}. {}: {}\n'.format(i, v, var_msg)
    else:
        results += ('\nThere are no variable inputs for {}.\n').format(var)
    # Identify variable dependency locations.
    if var_depends:
        results += ('\n'
                    'The following variable rely on {} as input:'
                    '\n').format(var)
        for i, var_depend in enumerate(var_depends, 1):
            v, file, lines, _ = var_depend
            start_line, end_line = lines
            if start_line == end_line:
                var_msg = found_in_line.format(start_line, file)
            else:
                var_msg = found_in_lines.format(start_line, end_line, file)
            results += '{}. {}: {}\n'.format(i, v, var_msg)
    else:
        results += ('\nNo variables depend on {} as input.\n').format(var)
    # Return results report.
    return results


def main(study, var, output_file='', verbose=True):
    """
    Summary
    -------
    Function to note CalSim mixed integer linear program dependencies related
    to a given variable.

    Parameters
    ----------
    study : path
        Absolute or relative path to study directory.
    var : string
        Variable of interest to determine dependencies (e.g. "S_SHSTA").
    output_file : path, default '', optional
        Absolute or relative file path for writing dependency report to disk.
        If no path is provided, the report is not written to disk.
    verbose : boolean, default True, optional
        Option to display contents of dependency report to console.

    Returns
    -------
    results_dict : dictionary
        A dictionary with the following entries:
            - 'defined' : Location in which the variable of interest `var` is
                          defined in the `study`.
            - 'inputs' : Locations of variables that feed into `var`.
            - 'dependencies' : Locations of variables that depend are `var` as
                               an input.

    """
    # Initialize variables.
    re_var = r'\b{}\b'.format(var)
    re_words = r'\b\w+\b'
    # Identify *.wresl in the given study.
    if not os.path.exists(study):
        msg = '{} not found.'.format(study)
        raise OSError(msg)
    wresl_files = glob.glob(os.path.join(study, '**/*.wresl'), recursive=True)
    # Read all file content into a dictionary.
    wresl_code = dict()
    for wresl_file in wresl_files:
        with open(wresl_file) as f:
            code = f.read()
        wresl_code[wresl_file] = code
    # Find definition location of given variable.
    var_defines = list()
    for k, v in wresl_code.items():
        temp_code = remove_cases(remove_comments(v))
        matches = find_statement(temp_code, var=var)
        for match in matches:
            lines = line_numbers(match, v)
            file = os.path.relpath(k, study)
            var_defines += [(var, file, lines, match.span())]
    if not var_defines:
        print('Variable {} not found in {}.'.format(var, study))
        return None
    # Parse variables that feed into given variable.
    statement_inputs = list()
    for var_define in var_defines:
        _, file, _, span = var_define
        k = os.path.join(study, file)
        temp_code = wresl_code[k]
        temp_code = temp_code[slice(*span)].split('{', 1)[1]
        temp_code = remove_non_variables(temp_code)
        inputs = list(re.finditer(re_words, temp_code))
        for input in inputs:
            statement_inputs += [(input.group())]
    statement_inputs = list(set(statement_inputs))
    var_inputs = list()
    for s in statement_inputs:
        for k, v in wresl_code.items():
            temp_code = remove_cases(remove_comments(v))
            matches = find_statement(temp_code, var=s)
            for match in matches:
                lines = line_numbers(match, v)
                file = os.path.relpath(k, study)
                var_inputs += [(s, file, lines, match.span())]
    # Find all locations given variable is used.
    ###########################################################################
    ###########################################################################
    # TODO: Speed up this section of code to the hash break because it is
    #       responsible for roughly 95% of runtime.
    var_depends = list()
    for k, v in wresl_code.items():
        temp_code = remove_cases(remove_comments(v))
        matches = find_statement(temp_code)
        matches += find_statement(temp_code, statement=r'goal')
        for match in matches:
            inputs = v[slice(*match.span())].split('{', 1)
            inputs_ = remove_non_variables(inputs[1])
            found_it = list(re.finditer(re_var, inputs_, re.IGNORECASE))
            if found_it:
                vr = inputs[0].split()[-1]
                lines = line_numbers(match, v)
                file = os.path.relpath(k, study)
                var_depends += [(vr, file, lines, match.span())]
    ###########################################################################
    ###########################################################################
    # Write results to console and/or disk.
    if verbose or output_file:
        results = generate_report(var, study, var_defines, var_inputs,
                                  var_depends)
    if verbose:
        print(results)
    if output_file:
        with open(output_file, 'w') as f:
            f.write(results)
    # Return dictionary of results.
    results_dict = {'defined': var_defines,
                    'inputs': var_inputs,
                    'dependencies': var_depends}
    return results_dict


# %% Execute script.
# Parse command line arguments.
if __name__ == '__main__':
    # Initialize argument parser.
    intro = '''
            For a given variable, list variables that are dependent on it and
            variables that feed directly into it.
            '''
    parser = argparse.ArgumentParser(description=intro)
    # Add positional arguments to parser.
    parser.add_argument('study', metavar='study', type=str, nargs='?',
                        help='Absolute or relative path to study directory.')
    parser.add_argument('var', metavar='variable', type=str, nargs='?',
                        help='''
                             Variable of interest to determine dependencies
                             (e.g. "S_SHSTA").
                             ''')
    # Add optional arguments.
    parser.add_argument('-o', '--outfile', metavar='output file', type=str,
                        nargs='?', default='',
                        help='''
                             Absolute or relative file path for writing
                             dependency report to disk. If no path is provided,
                             the report is not written to disk.
                             ''')
    parser.add_argument('-s', '--silent', dest='verbose', action='store_false',
                        default=True,
                        help='''
                             Suppress displaying dependency report to console.
                             ''')
    # Parse arguments.
    args = parser.parse_args()
    study = args.study.strip('"')
    var = args.var.strip('"')
    output_file = args.outfile.strip('"')
    verbose = args.verbose
    # Pass arguments to function.
    _ = main(study, var, output_file=output_file, verbose=verbose)
