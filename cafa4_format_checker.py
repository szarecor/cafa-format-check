#!/usr/bin/env python


#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import zipfile
import csv
import sys
import re
import os

from cafa_hpo_format_checker import cafa_checker as hpo
from cafa_go_format_checker import cafa_checker as go
from cafa_do_format_checker import cafa_checker as do_checker
from cafa_binding_site_format_checker import cafa_checker as bind


CAFA_VERSION = 4

"""
function go_hpo_predictions((
            None,
            False,
            "Error in %s\nThere are not enough fields)
Files are sent here from the main function if there are three fields seperated by '_' in the input filename.
function purpose:
    1. check that the third field is an integer and is between 1 and 3.
    2. check the second field for a taxonId or "hpo" to decide whether to branch into the GO format checker or HPO format checker
    3. test to see whether the file is zipped
        a. if zipped, opens, unzips, and reads the zipped file into cafa_{go/hpo}_format_checker.cafa_checker
        b. if not zipped, opens file and reads into cafa_{go/hpo}_format_checker.cafa_checker
"""


def go_hpo_predictions(path, fileName):
    features = (fileName.split(".")[0]).split("_")
    if features[0].lower() == "tc":
        taxon = features[3].lower()
        modelNum = features[2][-1]
        if taxon == "hpo":
            return (
                False,
                "Error in {}\nTerm Centric predictions are for GO terms only and cannot be done for HPO terms.".format(fileName),
            )

    else:
        taxon = features[2].lower()
        modelNum = features[1][-1]

    try:
        modelNum = int(modelNum)
    except ValueError:
        return False, "Error in {}\nModel number in filename must be integer".format(fileName)

    if modelNum < 1 or modelNum > 3:
        return (
            False,
            "Error in %s\nModel number in file name incorrect, you may only submit one to three models\nFormat should be teamId_model#_taxonId/hpo.txt"
            % fileName,
        )

    if taxon == "hpo":
        return hpo(path, fileName)
    if taxon == "do":
        # TODO: do_checker doesn't work with zip files if the fileName is not passed.
        #  What's up with that?
        return do_checker(path, fileName)

    else:
        return go(path, fileName)


"""
function binding_sites()
Files are sent here from the main function if there are four fields seperated by '_' in the input filename.
function purpose:
    1. check that the fourth field is 'binding'.
    2. check that the third field is an integer and is between 1 and 3.
    3. check that the second field is not 'hpo'
    4. sends file to cafa_binding_site_format_checker.py, function cafa_checker
    5. returned boolean, message is return to file_name_checker
"""


def binding_sites(path, filename):
    features = (filename.split(".")[0]).split("_")
    try:
        model_count = int(features[1][-1:])
    except:
        return False, "{}\nModel number in filename must be integer".format(filename)
    taxon = features[2].lower()
    bind_field = features[3].lower()
    if bind_field != "binding":
        return (
            False,
            "Error in {}\nBinding specification in filename is incorrect.  Binding site prediction filename must be\
             formatted teamId_model#_taxonId_binding.[txt/zip]\nField four is incorrect, must be 'binding'.".format(
                filename
            ),
        )
    if model_count < 1 or model_count > 3:
        return (
            False,
            "Error in {}\nModel number in file name incorrect, you may only submit one to three models\nFormat should\
             be teamId_model#_taxonId/hpo_binding.[txt/zip]".format(
                filename
            ),
        )
    if taxon == "hpo":
        return (
            False,
            "Error in {}\nBinding site prediction filename cannot have 'hpo' as third field, must be taxon Id.".format(
                filename
            ),
        )
    else:
        return bind(path, filename)
        # return True, "Binding site prediction file has been validated!"


"""
HPO and GO predictions are supposed to be team_model#_taxonID/HPO
Term Centric GO predictions are supposed to be tc_team_model#_taxonID
Binding site predictions are supposed to be team_model#_taxonID_binding
Checks how many fields seperated by '_' counted, and sent to the proper checker function

Function purpose:
    1. checks the number of fields seperated by "_"
    2. if three, file is sent to go_hpo_predictions
    3. if four, file is checked for "tc" field in first section.
    4. if tc, file is sent to go_hpo_predictions, if not, file is sent to binding_sites.
    5. if fields are too large or too small, error messages are returned.
    6. returned boolean,message from the format checkers are return to the main cafa_checker function.
"""


def file_name_check(infile, fileName):

    features = fileName.split(".")[0].split("_")
    if len(features) == 3:
        if features[2].lower() != "moon":
            return tuple(["GO/HPO Prediction"]) + go_hpo_predictions(infile, fileName)
        elif features[2].lower() == "moon":
            return tuple(["Moonlighting Protein Prediction"]) + go_hpo_predictions(
                infile, fileName
            )
    elif len(features) == 4:
        if features[0].lower() == "tc":
            # print "File %s is being treated as a Term Centric GO and moonlighting proteins prediction\n" % fileName
            # print go_hpo_predictions(infile, fileName)
            return tuple(["Term Centric GO Prediction"]) + go_hpo_predictions(
                infile, fileName
            )
        else:
            return tuple(["Binding Site Prediction"]) + binding_sites(infile, fileName)

    elif len(features) < 3:
        return (
            None,
            False,
            "Error in %s\nThere are not enough fields separated by '_' to the left of .{txt/zip} in the filename\nFor the default HPO and GO predictions, the filename should be three fields, team_model#_{taxonID/hpo}\nFor Term Centric GO predictions, the filename should be four fields, TC_team_model#_taxonID\nFor binding site predictions, filename should be four fields, team_model#_taxonID_binding, For moonlighting protein predictions filename should be three fields, team_model#_moon"
            % fileName,
        )

    else:
        return (
            None,
            False,
            "Error in %s\nThere are too many fields seperated by '_' to the left of .{txt/zip} in the filename\nFor the default HPO and GO predictions, the filename should be three fields, team_model#_{taxonID/hpo}\nFor Term Centric GO and moonlighting protein predictions, the filename should be four fields, TC_team_model#_taxonID\nFor binding site predictions, filename should be four fields, team_model#_taxonID_binding, For moonlighting protein predictions filename should be three fields, team_model#_moon"
            % fileName,
        )


def cafa_checker(input_file):
    """
    function purpose:
        1. Checks to see if the submission is a zipped archive or not.
        2. Checks to see if the submission is a unzipped directory.  If it is, returns False
        3. opens files and sends them to the file_name_check function
        4. Builds an error report and prints it out when validation is finished
        5. Checks to see if all the files are the same type of prediction.  Return False
    """
    # holds all returned boolean variables and the error messages.
    REPORT = []

    # holds the booleans returned from file_name_checker to see if any of the files return False for correct format
    FLAGS = []

    # holds all the file types that have been tested so that full zipped files can be checked if they are the same type of file.
    TYPES = []

    print("____________________________________________")
    if zipfile.is_zipfile(input_file):
        files = zipfile.ZipFile(input_file, "r")
        names = files.namelist()
        names = [
            name
            for name in names
            if "__MACOSX" not in name
            and not name.endswith("/")
            and not name.endswith(".DS_Store")
        ]
        for name in names:
            filename = name.split("/")[-1]
            infile = files.read(name)
            infile = infile.strip().split(b"\n")
            print("Validating {}".format(filename))
            file_type, correct, errmsg = file_name_check(infile, filename)
            FLAGS.append(correct)
            REPORT.append((correct, errmsg))
            TYPES.append(file_type)
    elif os.path.isdir(input_file):
        print("\nFolders must be compressed into a zipped archive before submission and validation\n")
        return
    else:
        infile = open(input_file, "r")
        filename = input_file.split("/")[-1]
        print("Validating {}".format(filename))
        # print file_name_check(infile, filename)
        file_type, correct, errmsg = file_name_check(infile, filename)

        FLAGS.append(correct)
        REPORT.append((correct, errmsg))
        TYPES.append(file_type)
    print("\n")

    if False in FLAGS:
        print("Files incorrecly formatted:\n")
        for correct, errmsg in REPORT:
            if not correct:
                print(errmsg)
                print("\n")
        return False

    if True in FLAGS:
        print("Files correctly formatted:\n")
        for correct, errmsg in REPORT:
            if correct:
                print(errmsg)

        return True
    if False not in FLAGS:
        if len(set(TYPES)) != 1:
            print("\nZipped archives should only contain one type of prediction")
            print("The following types of predictions are present:")
            TYPES = set(TYPES)
            for file_type in TYPES:
                print(">", file_type)

            return False

        else:
            print("\nAll files are correctly formatted")
            return True
    print("____________________________________________")


def usage():
    print("Usage: cafa4_format_check.py <path to input file or zipped archive>")


if __name__ == "__main__":
    try:
        cafa_checker(sys.argv[1])
    except IndexError:
        usage()
