'''
Authors: Sen Chen and Lingling Fan
'''
# coding=utf-8
import commands, collections, platform
import shutil
import traverse_tree
import get_act_method_code
import run_rpk_explore_apk
import create_json_withindent
import csv
import os

#emulator = sys.argv[1]
emulator = 'emulator-5554'

launchActivity = ''
defined_pkg_name = ''
defined_app_name = ''
used_pkg_name = ''

'''
Ubuntu and Macbook
'''

env_os = platform.system()

print 'Current environment: ' + env_os

if 'Linux' in env_os: # Ubuntu
    java_home_path = '/usr/lib/jvm/jdk1.8.0_45'
    sdk_platform_path = '/media/dell/49fff1d2-ef19-4e4d-855b-4eca95be873a/dell/Xiangyu/StoryDroid/main-folder/config/libs/android-platforms/'
    lib_home_path = '/media/dell/49fff1d2-ef19-4e4d-855b-4eca95be873a/dell/Xiangyu/StoryDroid/main-folder/config/libs/'
    callbacks_path = '/media/dell/49fff1d2-ef19-4e4d-855b-4eca95be873a/dell/Xiangyu/StoryDroid/main-folder/config/AndroidCallbacks.txt'
    jadx_path = '/media/dell/49fff1d2-ef19-4e4d-855b-4eca95be873a/dell/Xiangyu/StoryDroid/main-folder/jadx-master/'
    ic3_path = '/media/dell/49fff1d2-ef19-4e4d-855b-4eca95be873a/dell/Xiangyu/StoryDroid/main-folder/IC3/'

if 'Darwin' in env_os: # Macbook
    java_home_path = '/Library/Java/JavaVirtualMachines/jdk1.8.0_211.jdk/Contents/Home'
    sdk_platform_path = '/Users/chensen/Tools/storydistiller/config/libs/android-platforms/'
    lib_home_path = '/Users/chensen/Tools/storydistiller/config/libs/'
    callbacks_path = '/Users/chensen/Tools/storydistiller/config/AndroidCallbacks.txt'
    jadx_path = '/Users/chensen/Tools/storydroid_v1/jadx-master/'
    ic3_path = '/Users/chensen/Tools/storydroid_v1/IC3/'

'''
Rename the app name
'''
def rename(apk_path, apk_dir):
    global defined_pkg_name
    global used_pkg_name
    defined_pkg_name = commands.getoutput('aapt dump badging %s | grep package | awk \'{print $2}\' | sed s/name=//g | sed s/\\\'//g'%(apk_path))
    launcher = commands.getoutput(r"aapt dump badging " + apk_path + " | grep launchable-activity | awk '{print $2}'")
    # Sometimes launcher is empty or launcher starts with "."
    if launcher == '' or defined_pkg_name in launcher or launcher.startswith("."):
        used_pkg_name = defined_pkg_name
    else:
        used_pkg_name = launcher.replace('.' + launcher.split('.')[-1], '').split('\'')[1]
    print 'Rename pkg: ' + used_pkg_name

    version = commands.getoutput('aapt dump badging %s | grep versionName | awk \'{print $3}\' | sed s/versionCode=//g | sed s/\\\'//g'%(apk_path))
    os.system('mv %s %s'%(apk_path, apk_dir + used_pkg_name + '_' + version + '.apk')) # used_pkg_name_version.apk
    global defined_app_name
    defined_app_name = defined_pkg_name + '_' + version
    return apk_dir + used_pkg_name + '_' + version + '.apk'

'''
Get icon of the app
'''
def get_icon(results_visual_icon):
    #icon_path = output + 'java_codes/' + apk_name + '/resources/res/mipmap-hdpi-v4/ic_launcher.png'
    '''Need to check the path'''
    icon_path = output + 'java_code/' + apk_name + '/resources/res/drawable-xhdpi-v4/ic_launcher.png'
    if os.path.exists(icon_path):
        os.system('cp %s %s'%(icon_path, results_visual_icon))
    else:
        icon_path = output + 'java_code/' + apk_name + '/resources/res/drawable-xhdpi-v4/icon.png'
        os.system('cp %s %s' % (icon_path, results_visual_icon))

'''
Decomile the apk and get the Java appstory
'''
def decompile(apk_path, apk_name):
    global launchActivity
    #bin_path = output + 'jadx-master/build/jadx/bin/'
    bin_path = jadx_path + 'build/jadx/bin/'
    results_visual = output + 'outputs/' + apk_name + '/'
    results_visual_icon = results_visual + 'icon/'
    if not os.path.exists(results_visual):
        os.mkdir(results_visual)
    if not os.path.exists(results_visual_icon):
        os.mkdir(results_visual_icon)
    JavaCode_path = output + 'java_code/'
    if not os.path.exists(JavaCode_path):
        os.mkdir(JavaCode_path)
    results_JavaCode = JavaCode_path + apk_name + '/'
    if not os.path.exists(results_JavaCode):
        os.chdir(bin_path)
        os.system('./jadx -d %s %s' % (results_JavaCode, apk_path))

    # Get icon
    get_icon(results_visual_icon)

    launchActivity = commands.getoutput('aapt dump badging %s | grep launchable-activity | awk \'{print $2}\' | sed s/name=//g | sed s/\\\'//g'%apk_path)
    if launchActivity == '':
        launchActivity = commands.getoutput('aapt dump badging %s | grep Activity | awk \'{print $2}\' | sed s/name=//g | sed s/\\\'//g'%apk_path)
    result_launcher = output + 'outputs/' + apk_name + '/launcher.txt'
    launcher_file = open(result_launcher, 'wb')
    launcher_file.write(launchActivity)

'''
Run IC3
'''
def run_IC3(apk_path):
    IC3_fail_file = output + 'outputs/IC3_fail.txt'
    results_IC3_dir = output + 'ic3_atgs/'
    if not os.path.exists(results_IC3_dir):
        os.makedirs(results_IC3_dir)
    results_IC3 = results_IC3_dir + apk_name + '.txt'
    '''
    if os.path.exists(results_IC3):
        return results_IC3
    '''
    open(results_IC3,'wb').write('')
    IC3_home = ic3_path + 'ic3-0.2.0/'
    IC3_jar = IC3_home + 'ic3-0.2.0-full.jar'
    IC3_android_jar = IC3_home + 'android.jar'
    fail_writer = open(IC3_fail_file, 'ab')
    os.chdir(IC3_home)
    # print os.system('timeout 15m java -Xmx4g -jar %s -apkormanifest %s -in %s -cp %s -protobuf %s | grep "PATH: "' % (IC3_jar, apk_path, sootOutput_dir, IC3_android_jar, results_IC3_dir))
    if (os.system('timeout 15m java -Xmx4g -jar %s -apkormanifest %s -in %s -cp %s -protobuf %s | grep "PATH: "'
                      % (IC3_jar, apk_path, sootOutput_dir, IC3_android_jar, results_IC3_dir))) != 0:
        fail_writer.write(apk_path + '\n')

    #if os.path.exists(results_IC3):
        # rename the ic3 result file, because the pkg and real pkg are inconsistant.
        #os.system('mv %s %s' % (results_IC3, results_IC3_dir + apk_name + '.txt'))
    #print results_IC3_dir + used_pkg_name + '.txt'
    #os.system('mv %s %s' % (results_IC3_dir + used_pkg_name + '.txt', results_IC3))

    return results_IC3

'''
Parse the results of IC3
'''
def parse_IC3(file, pkg):
    dict = {}
    f = open(file, 'rb')
    line = f.readline()
    flag = -1
    s = 0 # indicate component
    brace = 0 # indicate the number of braces
    while line:
        if '{' in line:
            brace += 1
        if '}' in line:
            brace -= 1
        if 'components {' in line:
            s = 1
            flag = -1
            tmp =''
            brace = 1
        elif s == 1 and 'name:' in line:
            tmp = line.split(': "')[1].split('"')[0]
            s = 2
        elif s == 2 and 'kind: ACTIVITY' in line:
            flag = 0
            sourceActivity = tmp
            s = 3
        elif flag == 0 and "exit_points" in line:
            flag = 1
        elif flag == 1 and 'statement' in line:
            stm = line.split(': "')[1].split('"')[0]
            flag = 2
        elif flag == 2 and 'method: "' in line:
            mtd = line.split(': "<')[1].split('>"')[0]
            flag = 3
        elif flag == 3 and 'kind: ' in line:
            if 'kind: ACTIVITY' in line:
                flag = 4
            else:
                flag = 0
        elif flag == 4 and 'kind: CLASS' in line:
            flag = 5
        elif flag == 5 and 'value' in line:
            if ': "L' in line:
                targetActivity = line.strip().split(': "L')[1].split(';"')[0].replace('/', '.')
                if targetActivity.endswith('"'):
                    targetActivity = targetActivity.split('"')[0]
            else:
                targetActivity = line.strip().split(': "')[1].split(';"')[0].replace('/', '.')
                if targetActivity.endswith('"'):
                    targetActivity = targetActivity.split('"')[0]
            if not pkg in targetActivity:
                flag = 0
                continue
            if not sourceActivity in dict.keys():
                dict[sourceActivity] = set()
            dict[sourceActivity].add(targetActivity)
            flag = 4
        if brace == 1 and s == 3: # in component, find more exit_points
            flag = 0
        line = f.readline()
    return dict

'''
Save the parsed results of IC3
'''
def save_parsed_IC3(dict):
    results_parseIC3_dir = output + 'parsed_ic3/'
    if not os.path.exists(results_parseIC3_dir):
        os.makedirs(results_parseIC3_dir)
    # if not os.path.exists(output + 'parsed_ic3/' + apk_name + '.txt'):
    #     open(results_parseIC3_dir + apk_name + '.txt', 'wb').write('')
    #     return
    open(results_parseIC3_dir + apk_name + '.txt', 'wb').write('')
    for k, v in dict.items():
        for v1 in v:
            open(results_parseIC3_dir + apk_name + '.txt', 'ab').write(k + '-->' + v1 + '\n')

'''
Get call graphs of the app
'''
def get_callgraphs(apk_path):
    results_CG_dir = output + 'soot_cgs/'
    CG_jar = output + 'config/CGGenerator.jar'
    os.chdir(output)
    os.system('java -Xmx4g -jar %s %s %s %s %s' % (CG_jar, apk_path, results_CG_dir, sdk_platform_path, callbacks_path))

'''
Parse the results of call graphs
'''
def parse_CG(cg_file, pkg_name):
    if not os.path.exists(output + 'soot_cgs/' + apk_name + '.txt'):
        return
    dict = collections.defaultdict(set)
    f = open(cg_file, 'rb')
    line = f.readline()
    while line:
        print line
        key = line.split(' in <')[1].split('> ==> <')[0]
        value = line.split('> ==> <')[1][0:-1]
        if pkg_name in key and pkg_name in value and not 'EmmaInstrument' in key and not 'EmmaInstrument' in value:
            dict[key].add(value[:-1])
        line = f.readline()
    #print '[6] Parse CG: DONE'
    return dict

'''
Save the parsed results of call graphs
'''
def save_parsed_CG(dict):
    results_parsedCG_dir = output + 'parsed_cgs/'
    if not os.path.exists(results_parsedCG_dir):
        os.makedirs(results_parsedCG_dir)
    if not os.path.exists(output + 'soot_cgs/' + apk_name + '.txt'):
        #open(results_parseCG_dir + apk_name + '.txt', 'wb')
        return
    saved_parseCG = open(results_parsedCG_dir + apk_name + '.txt', 'wb')
    processed_cg_file = output + 'outputs/' + apk_name + '/' + apk_name + '_cgs.txt'
    saved_parseCG_visulization = open(processed_cg_file, 'wb')
    for k, v in dict.items():
        for v1 in v:
            saved_parseCG.write(k + '-->' + v1 + '\n')
    for k, v in dict.items():
        for v1 in v:
            saved_parseCG_visulization.write(k + '-->' + v1 + '\n')

'''
Run soot
'''
def run_soot(output, apk_path, pkg_name, apk_name):
    results_enhancedIC3 = output + 'storydroid_atgs/' + apk_name + '.txt'
    results_enhancedIC3_label = output + 'outputs/' + apk_name + '/activity_paras.txt'
    if os.path.exists(results_enhancedIC3_label):
        return

    '''
    Using jar
    
    enhancedIC3_jar = output + 'config/run_soot.jar'
    os.chdir(output)
    os.system('java -jar %s %s %s %s %s %s %s' % (enhancedIC3_jar, output, apk_path, pkg_name, java_home_path, sdk_platform_path, lib_home_path))
    '''

    '''
    Using binary
    '''
    config_path = os.path.join(output, 'config/')
    soot_binary = 'run_soot.run'
    os.chdir(config_path)
    os.system('./%s %s %s %s %s %s %s' % (soot_binary, output, apk_path, pkg_name, java_home_path, sdk_platform_path, lib_home_path))

'''
Get the results of transitions
'''
def get_atgs(apk_name):
    results_parseIC3 = output + 'parsed_ic3/' + apk_name + '.txt'
    results_enhancedIC3 = output + 'storydroid_atgs/' + apk_name + '.txt'
    if not os.path.exists(results_enhancedIC3):
        open(results_enhancedIC3, 'wb').write('')
    ICC_path = output + 'atgs/'
    if not os.path.exists(ICC_path):
        os.makedirs(ICC_path)
    results_ICCs = output + 'atgs/' + apk_name + '.txt'
    results_visulization_ICCs = output + 'outputs/' + apk_name + '/' + apk_name + '_atgs.txt'
    file_parseIC3 = open(results_parseIC3, 'rb')
    ICCs = set()
    for line in file_parseIC3.readlines():
        ICCs.add(line)
    file_enhancedIC3 = open(results_enhancedIC3, 'rb')
    for line in file_enhancedIC3.readlines():
        ICCs.add(line)
    file_ICCs = open(results_ICCs, 'wb')
    for ICC in ICCs:
        file_ICCs.write(ICC)
    file_ICCs_visulization = open(results_visulization_ICCs, 'wb')
    for ICC in ICCs:
        file_ICCs_visulization.write(ICC)

'''
Copy file
'''
def copy_search_file(srcDir, desDir):
    if not os.path.exists(desDir):
        os.mkdir(desDir)
    for line in os.listdir(srcDir):
        filePath = os.path.join(srcDir, line)
        if os.path.isdir(filePath):
            os.system('cp -r %s %s'%(filePath, desDir))
        else:
            os.system('cp %s %s' % (filePath, desDir))

'''
For the input of IC3
'''
def getSootOutput(apk_path, apk_name):
    if 'Linux' in env_os:
        sootOutput_jar = output + '/config/getSootOutput-Ubuntu.jar'
    if 'Darwin' in env_os:
        sootOutput_jar = output + '/config/getSootOutput-Macbook.jar'

    print 'java -jar %s %s %s %s %s' % (sootOutput_jar, sootOutput_dir, apk_name, output, apk_path)
    os.chdir(output + '/config/')
    os.system('java -jar %s %s %s %s %s' % (sootOutput_jar, sootOutput_dir, apk_name, output, apk_path))

def get_failed_startup_acts(all_acts):
    screenshots_dir = os.path.join(result_apkfolder,'screenshots/')
    startup_acts = set()
    if len(os.listdir(screenshots_dir)) == 0:
        return 0
    else:
        for png in os.listdir(screenshots_dir):
            act_name = png.split('.png')[0]
            startup_acts.add(act_name)
        retD = list(set(all_acts).difference(startup_acts))
        return retD

def getNumber(icc_file):
    atgs = set()
    if os.path.exists(icc_file):
        for line in open(icc_file, 'r').readlines():
            atgs.add(line)
    atgs_num = len(atgs)
    return atgs_num


def getScenariosNum(appearedActs_in_atgs):
    screenshots_dir = os.path.join(result_apkfolder, 'screenshots/')
    startup_acts = set()
    if len(os.listdir(screenshots_dir)) == 0:
        return len(appearedActs_in_atgs)
    else:
        for png in os.listdir(screenshots_dir):
            act_name = png.split('.png')[0]
            startup_acts.add(act_name)
        num = len(appearedActs_in_atgs.union(startup_acts))
        return num


def getLogData(all_acts, results_visulization_ICCs, results_visulization_ICCs_static,
               results_visulization_ICCs_dynamic):
    all_acts_num = len(all_acts)
    appearedActs_in_atgs = set()
    lines = open(results_visulization_ICCs, 'r').readlines()
    for line in lines:
        left = line.split('-->')[0]
        right = line.split('-->')[1]
        appearedActs_in_atgs.add(left)
        appearedActs_in_atgs.add(right.strip())

    # May contain other types of components, therefore, it needs to check by all activities
    appearedActs_in_atgs_num = len(set(all_acts).intersection(appearedActs_in_atgs))
    if all_acts_num != 0:
        act_coverage = round(float(appearedActs_in_atgs_num)/float(all_acts_num), 2)
    else:
        act_coverage = 1
    independentActs_not_in_acts_num = int(all_acts_num - appearedActs_in_atgs_num)

    all_atgs_num = getNumber(results_visulization_ICCs)

    scenarios_num = getScenariosNum(appearedActs_in_atgs) # May contain other types such as Fragment

    static_atgs_num = getNumber(results_visulization_ICCs_static)
    dynamic_atgs_num = getNumber(results_visulization_ICCs_dynamic)

    startup_acts_num = int(commands.getoutput('ls %s | wc -l' % (result_apkfolder + 'screenshots')).split('\n')[0])
    failed_startup_acts_num = int(all_acts_num - startup_acts_num)

    if failed_startup_acts_num == 0:
        failed_startup_acts = []
    else:
        failed_startup_acts = get_failed_startup_acts(all_acts)

    return appearedActs_in_atgs_num, act_coverage, independentActs_not_in_acts_num, \
           all_atgs_num, scenarios_num, static_atgs_num, dynamic_atgs_num, \
           startup_acts_num , failed_startup_acts_num, failed_startup_acts


if __name__ == '__main__':

    # output = sys.argv[1] # Main folder path
    output = '/media/dell/49fff1d2-ef19-4e4d-855b-4eca95be873a/dell/Xiangyu/StoryDroid/main-folder/'
    #output = '/Users/chensen/Tools/storydistiller/'
    # adb = sys.argv[2] # adb emulator
    adb = 'adb '

    apk_dir = os.path.join(output, 'apks/') # APK folder
    out_csv = os.path.join(output, 'log.csv') # Log file

    # apk name, apk_name
    # package name, pkg_name
    # number of all activities in manifest, all_acts_num
    # number of appeared activities in atgs, appearedActs_in_atgs_num
    # Activity coverage, act_coverage
    # number of independent activities (not in atgs), independentActs_not_in_acts_num
    # number of all atgs including static and dynamic, all_atgs_num
    # number of scenarios, scenarios_num
    # number of atgs by static, static_atgs_num
    # number of atgs by dynamic, dynamic_atgs_num
    # number of startup activity, startup_acts_num
    # number of the failed startup activity, failed_startup_acts_num
    # failed startup activities, failed_startup_acts

    csv.writer(open(out_csv, 'a')).writerow(('apk_name', 'pkg_name', 'all_acts_num', 'appearedActs_in_atgs_num', 'act_coverage', 'independentActs_not_in_acts_num', 'all_atgs_num',
                                             'scenarios_num', 'static_atgs_num',
                                             'dynamic_atgs_num', 'startup_acts_num', 'failed_startup_acts_num', 'failed_startup_acts'))

    for apk in os.listdir(apk_dir):
        if apk.endswith('.apk'):

            root = 'adb -s %s root'%(emulator)  # root the emulator before running
            print commands.getoutput(root)

            apk_path = apk_dir + apk
            org_apk_name = apk.split('.apk')[0]

            print 'apk path: ' + apk_path
            print 'Start to rename the app and get package name.'
            apk_path = rename(apk_path, apk_dir)
            apk_name = os.path.split(apk_path)[1].split('.apk')[0]

            '''
            Create output folder
            '''
            dir = output + '/outputs/' + apk_name + '/'
            if not os.path.exists(dir):
                os.makedirs(dir)

            '''
            Save pkg name
            '''
            open(dir + 'used_pkg_name.txt', 'wb').write(used_pkg_name + '\n')
            open(dir + 'defined_pkg_name.txt', 'wb').write(defined_pkg_name + '\n')

            '''
            Create sootOutput folder
            '''
            sootOutput_dir = output + 'sootOutput/' + apk_name + '/'
            if not os.path.exists(sootOutput_dir):
                os.makedirs(sootOutput_dir)

            ''' # Comment on 2022.10.24
            print 'Start to decompile apk'
            decompile(apk_path, apk_name)
            '''

            '''
            The results are used for running IC3, which are the inputs of IC3
            '''
            print 'Start to get SootOutput (class) and check layout type'
            getSootOutput(apk_path, apk_name)

            print 'Start to run IC3 ' + apk_name
            results_IC3 = run_IC3(apk_path)

            print 'Start to parse IC3'
            dict = parse_IC3(results_IC3, used_pkg_name) # Will check whether is defined_pkg_name
            save_parsed_IC3(dict)

            ''' # Comment on 2022.10.24
            print 'Start to get call graphs ' + apk_name
            CG_path = output + 'soot_cgs/'
            if not os.path.exists(CG_path):
                os.makedirs(CG_path)
            results_CG = CG_path + apk_name + '.txt'
            if not os.path.exists(results_CG):
                get_callgraphs(apk_path)

            print 'Start to parse call graphs ' + apk_name
            dict = parse_CG(results_CG, used_pkg_name)
            save_parsed_CG(dict)
            '''

            print 'Start to delete sootOutput ' + apk_name
            shutil.rmtree(sootOutput_dir)  # Delete sootOutput
            #os.chdir(output + 'apktojimple')
            #os.system('./decompile.sh %s %s'%(apk_path, sootOutput_dir))

            print 'Start to get static ATG by Soot' + apk_name
            print 'Soot pkg: ' + used_pkg_name
            run_soot(output, apk_path, used_pkg_name, apk_name)
            get_atgs(apk_name)

            result_apkfolder = output + 'outputs/' + apk_name + '/'
            results_visulization_ICCs = result_apkfolder + apk_name + '_atgs.txt'

            # copy apk_name + '_atgs' to apk_name + '_atgs_static'
            results_visulization_ICCs_static = result_apkfolder + apk_name + '_atgs_static.txt'
            if os.path.exists(results_visulization_ICCs):
                os.system('cp %s %s' % (results_visulization_ICCs, results_visulization_ICCs_static))

            print 'Start to get the corresponding storyboards ' + apk_name
            # Dynamic analysis
            if not os.path.exists(result_apkfolder + 'screenshots'):
                os.mkdir(result_apkfolder + 'screenshots')
            all_acts = run_rpk_explore_apk.execute(apk_path, apk_name, result_apkfolder, output)

            # if _atg_dynamic exist, copy it to _atgs
            results_visulization_ICCs_dynamic = result_apkfolder + apk_name + '_atgs_dynamic.txt'
            if os.path.exists(results_visulization_ICCs_dynamic):
                dynamic_pair = set()
                lines = open(results_visulization_ICCs_dynamic, 'r').readlines()
                # Handle duplication
                for line in lines:
                    pair = line.split('->')[0] + '-->' + line.split('->')[-1]
                    if pair in dynamic_pair:
                        continue
                    dynamic_pair.add(pair)

                for pair in dynamic_pair:
                    open(results_visulization_ICCs, 'ab').write(pair)

            if all_acts != None:
                appearedActs_in_atgs_num, act_coverage, independentActs_not_in_acts_num, all_atgs_num, \
                scenarios_num, static_atgs_num, dynamic_atgs_num, \
                startup_acts_num , failed_startup_acts_num, failed_startup_acts \
                = getLogData(all_acts, results_visulization_ICCs,
                             results_visulization_ICCs_static, results_visulization_ICCs_dynamic)

                csv.writer(open(out_csv, 'a')).writerow((apk_name, used_pkg_name, len(all_acts), appearedActs_in_atgs_num, act_coverage,
                                                         independentActs_not_in_acts_num, all_atgs_num, scenarios_num, static_atgs_num, dynamic_atgs_num,
                                                         startup_acts_num , failed_startup_acts_num, failed_startup_acts))

            ''' # Comment on 2022.10.24
            print 'Start to get Activity and method code' + apk_name
            results_JavaCode = output + 'java_code/' + apk_name + '/'
            processed_cg_file = result_apkfolder + apk_name + '_cgs.txt'
            if os.path.exists(results_JavaCode):
                get_act_method_code.main(results_JavaCode, result_apkfolder, results_visulization_ICCs,
                                         processed_cg_file, launchActivity)

            print 'Start to get method call sequence'
            if os.path.exists(processed_cg_file):
                traverse_tree.main(processed_cg_file, results_visulization_ICCs, result_apkfolder)

            print 'Start to get JSON and webpages'
            config_path = os.path.join(output, 'config/')
            copy_search_file(os.path.join(config_path, 'template/'), os.path.join(result_apkfolder, 'output/'))
            create_json_withindent.execute(result_apkfolder)
            '''

            if os.path.exists(os.path.join(result_apkfolder, apk_name + '.apk')):
                os.remove(os.path.join(result_apkfolder, apk_name + '.apk'))

            os.remove(apk_path)