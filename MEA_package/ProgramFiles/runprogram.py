import os
import sys
from LNA import LinearNoiseApproximation
from model import parse_model
from moment_expansion_approximation import MomentExpansionApproximation
from ode_problem import parse_problem, ODEProblemWriter, ODEProblemLatexWriter
from paramtime import paramtime
from simulate import simulate, graphbuilder
from sumsq_infer import write_inference_results, graph, parse_experimental_data_file, ParameterInference
from hypercube import hypercube
import gamma_infer

def printOptions():
    print "\nList of possible options:"

    print "\n House-keeping:"
    print "  --wd\t\tSpecify the working directory. This will contain all input and\n\t\toutput files. Default Inoutput folder provided."

    print "\n Moment expansion approximation:"
    print "  --MEA\t\tCreate a system of ODEs using moment expansion from the model\n\t\tspecified with --model."
    print "  --model\tSpecify the model input file. Use format in modeltemplate.txt.\n\t\tE.g. --model=yourmodel.txt."
    print "  --nMom\tNumber of moments used in expansion. Default --nMom=2."
    print "  --ODEout\tName of output file. Default --ODEout=ODEout."

    print "\n Linear noise approximation:"
    print "  --LNA\t\tCreate a system of ODEs using LNA. Use --model and --ODEout\n\t\toptions as above."

    print "\n Compiling the ODE solver:"
    print "  --compile\tCreate and compile the file needed for the ODE solver, use\n\t\t--ODEout and --timeparam to specify model and timepoints."
    print "  --library\tSpecify name for the C library with no file type extension.\n\t\tDefault --library=solver."
    print "  --timeparam\tName of file containing timepoints using format in\n\t\tparamtimetemp.txt. Required for --compile. Later used to input\n\t\tother parameters for inference or simulation."
    print "  --sd1\t\tPath to directory containing sundials header files.\n\t\tDefault --sd1=/cluster/soft/Linux_2.6_64/include/."
    print "  --sd2\t\tPath to directory containing sundials libraries.\n\t\tDefault --sd2=/cluster/soft/Linux_2.6_64/lib/."

    print "\n Simulation:"
    print "  --sim\t\tSimulate moment trajectories for a given set of parameters.\n\t\tUse --library, --timeparam and --ODEout to specify required\n\t\tinformation."
    print "  --simout\tSpecify filename for simulated trajectory data output."
    print "  --maxorder\tSpecify the maximum order of moments to simulate (only for\n\t\t--MEA).  Default = maxorder of MEA model used"



    print "\n Parameter inference:"
    print "  --infer\tInfer model parameters using experimental data.\n\t\tUse --timeparam and --data to provide required information."
    print "  --data\tSpecify experimental data file to be used for parameter\n\t\tinference. Timepoints must be the same in both --data and\n\t\t--timeparam files."
    print "  --inferfile\tName of parameter inference output file.\n\t\tDefault --inferfile=inference.txt."
    print "  --restart\tUse Latin Hypercube Sampling for random restarts. Use\n\t\t--timeparam to specify ranges for both kinetic parameters and\n\t\tinitial conditions. For fixed starting parameter values, enter\n\t\tsame value for upper and lower bound."
    print "  --nRestart\tSpecify the number of random restarts. Default --nRestart=4."
    print "  --limit\tConstrain parameter values during optimisation. Use --timeparam\n\t\tto set constraints."
    print "  --pdf\t\tChoose the probability density function used to approximate\n\t\tlikelihood for each species/timepoint.\n\t\tOptions: gamma, normal, lognormal."
    print "  --maxent\tUse maximum entropy to approximate probability density."

    print "\n Graph options:"
    print "  --plot\tPlot simulated or inferred moment trajectories."
    print "  --plottitle\tSpecify plot title."

    print "\n  --help\tPrints out this list of options.\n"

def run():
    
    MFK = False
    model_file = False
    nMoments = 2
    ODEout = 'ODEout'
    createcfile = False
    library = 'solver'
    tpfile = None
    solve = False
    maxorder = None
    plot = False
    plottitle = ''
    trajout = 'traj.txt'
    infer = False
    inferfile = 'inference.txt'
    exptdata = None
    restart = False
    nRestart=4
    limit = False
    wd = '../Inoutput/'
    distribution = False
    LNA = False
    sundials_1 = '/cluster/soft/Linux_2.6_64/include/'
    sundials_2 = '/cluster/soft/Linux_2.6_64/lib/'


    for i in range(1,len(sys.argv)):
        if sys.argv[i].startswith('--'):
            option = sys.argv[i][2:]

            if option == 'help':
                printOptions()
                sys.exit()
            elif option == 'MEA': MFK = True
            elif option[0:6] == 'model=':model_file = option[6:]
            elif option[0:5] == 'nMom=':nMoments = option[5:]
            elif option[0:7] == 'ODEout=':ODEout = option[7:]
            elif option == 'compile' : createcfile = True # TODO: this is not used any more, the only reason we keep this
                                                          # is because I do nt want to change all regression tests just now
            elif option[0:8] == 'library=':library = option[8:]
            elif option[0:10]=='timeparam=':tpfile=option[10:]
            elif option[0:4]=='sd1=':sundials_1=option[4:]
            elif option[0:4]=='sd2=':sundials_2=option[4:]
            elif option == 'sim' : solve = True
            elif option == 'plot' : plot = True
            elif option[0:10] == 'plottitle=' : plottitle = option[10:]
            elif option[0:7] == 'simout=' : trajout = option[7:]
            elif option[0:9] == 'maxorder=' : maxorder = int(option[9:])
            elif option == 'infer' : infer = True
            elif option[0:10] == 'inferfile=': inferfile = option[10:]
            elif option[0:5] == 'data=' : exptdata=option[5:]
            elif option == 'restart':restart=True
            elif option[0:9] == 'nRestart=':nRestart=option[9:]
            elif option[0:5] == 'limit':limit=True
            elif option[0:3] == 'wd=': wd = option[3:]
            elif option[0:4] == 'pdf=': distribution = option[4:]
            elif option[0:6] == 'maxent': distribution = 'maxent'
            elif option[0:3] == 'LNA' : LNA = True
            elif option.startswith('random-seed='):
                import random
                random_seed = int(option[12:])
                print 'Setting random seed to {0}'.format(random_seed)
                random.seed(random_seed)
                import numpy.random
                numpy.random.seed(random_seed)
            elif not(sys.argv[i-1][2:] == 'LNA'):
                print "\nunknown option "+sys.argv[i]
                printOptions()
                sys.exit()
        elif not(sys.argv[i-1][2:]=='LNA'):
            print "\nunknown option "+sys.argv[i]
            printOptions()
            sys.exit()

    if MFK and LNA:
        print "\n  Error:\n  Please choose EITHER --MEA or --LNA.\n"
        sys.exit(1)

    if MFK or LNA:
        if not model_file:
            print "\n No input model file given.\n Try:\n\t--model=modelname.txt\n"
            sys.exit(1)

        model = None
        try:
            model = parse_model(os.path.join(wd, model_file))
        except IOError as e:
            print "\n  Error:\n  Cannot open {0!r}. Got {1!r}\n" \
                  "Please try again with correct model filename.\n".format(model_file, e)
            sys.exit(1)

        approximation = None
        if MFK:
            approximation = MomentExpansionApproximation(model, nMoments)
        else:
            approximation = LinearNoiseApproximation(model)

        problem = approximation.run()

        ode_writer = ODEProblemWriter(problem, approximation.time_last_run)
        ode_writer.write_to(os.path.join(wd, ODEout))
        tex_writer = ODEProblemLatexWriter(problem)
        tex_writer.write_to(os.path.join(wd, '.'.join([ODEout, "tex"])))

    if solve and infer:
        print "\n  Error:\n  Please choose EITHER --solve or --infer but not both.\n"
        sys.exit()

    if solve:
        if not os.path.exists(wd+tpfile):
            print "\n  Error:\n  "+tpfile+"  does not exist in working directory.\n  Please try again with correct timepoint/parameter filename.\n"
            sys.exit(1)

        [t,param,initcond,vary, varyic, limits] = paramtime(wd+tpfile,restart, limit)
        problem = parse_problem(wd+ODEout)  # TODO: os.path.join

        simulated_timepoints, solution, momlist = simulate(problem,
                                         wd+trajout,t,param,initcond, maxorder)

        if plot:
            graphbuilder(solution,wd+ODEout,plottitle,simulated_timepoints,momlist)

    if infer:
        if not tpfile:
            print "\n No timepoints/parameters/initial conditions given for inference.\n " \
                  "Please provide a file in the format of paramtimetemp.txt."
            sys.exit(1)
        if not os.path.exists(wd+tpfile):
            print "\n  Error:\n  "+tpfile+"  does not exist in working directory.\n  " \
                                          "Please try again with correct " \
                                          "timepoint/parameter/initial conditions filename.\n"
            sys.exit(1)
        if exptdata is None:
            print "\n No experimental data provided for inference.\n " \
                  "Please try again specifying your data file with the --data option."
            sys.exit(1)
        if not os.path.exists(wd+exptdata):
            print "\n  Error:\n  "+exptdata+"  does not exist in working directory.\n  " \
                                            "Please try again with correct experimental data filename.\n"
            sys.exit(1)

        problem = parse_problem(wd+ODEout)
        # read sample data from file and get indices for mean/variances in CVODE output
        (observed_timepoints, observed_trajectories) = parse_experimental_data_file(wd+exptdata)

        try:
            [t, param, initcond, vary, varyic, limits] = paramtime(wd + tpfile, restart, limit)
        except ValueError:
            print '{0} is not in correct format. Ensure you have entered upper and lower bounds ' \
                  'for all parameter values.'.format(tpfile)
            sys.exit(1)
        if restart:
            all_params = hypercube(int(nRestart), param[:] + initcond[:])
            # TODO: hypercube is a bit funny in how it returns stuff
            all_params = [(x[:len(param)], x[len(param):]) for x in all_params]
        else:
            all_params = [(param, initcond)]

        restart_results = []
        for param_n, initcond_n in all_params:
             # FIXME: this should not be here
            if len(initcond_n) != problem.number_of_equations:
                # This just applies padding of [0, False] to unspecified initconditions
                # consider moving it to appropriate parse function instead
                diff = problem.number_of_equations - len(initcond_n)
                initcond_n += [0] * diff
                initcond_full = initcond_n
                varyic += [False] * diff

            params_with_variability = zip(param_n, vary)
            initcond_with_variability = zip(initcond_n, varyic)

            optimiser_method = distribution if distribution else 'sum_of_squares'
            optimiser = ParameterInference(problem, params_with_variability,
                                           initcond_with_variability, limits,
                                           observed_timepoints,
                                           observed_trajectories,
                                           method=optimiser_method)
            result = optimiser.infer()

            restart_results.append([result, observed_trajectories, param_n, initcond_n])

        restart_results.sort(key=lambda x: x[0][1], reverse=False)

        # write results to file (default name 'inference.txt') and plot graph if selected
        write_inference_results(restart_results, t, vary, initcond_full, varyic, wd + inferfile)
        if plot:
            graph(problem, restart_results[0], observed_trajectories, t, initcond_full, vary, varyic, plottitle)


run()
