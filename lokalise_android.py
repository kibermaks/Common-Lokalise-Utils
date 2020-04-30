#!/usr/bin/env python

import os
from os import listdir
import shutil
import time
import argparse
import json
import lokalise_common

LOCALIZATIOS_UNUSED_TAG = 'unused'

LOCALIZATION_DEFAULT_LANGUAGE = "en"
LOCALIZATION_DEFAULT_FOLDER = "values"
LOCALIZATION_FILE_NAME = u"strings.xml"
LOCALIZATION_FOLDER_NAMES = ["values", "values-ko", "values-th", "values-fr", "values-tr", "values-hi", 
							"values-nl", "values-zh-rTW", "values-af", "values-it", "values-pt", "values-de", 
							"values-ja", "values-ru", "values-vi", "values-zh-rCN", "values-es"]


LOCALIZATION_IMPORT_MAP = {"zh-rTW" : "zh-Hant", "zh-rCN" : "zh-Hans"}
LOCALIZATION_RENAME_MAP = {"values-zh-rHant" : "values-zh-rTW", "values-zh-rHans" : "values-zh-rCN"}  					

def localization_import(localization_folder, lokalise_token, lokalise_project_id, full_import, tags = None, cleanFilePath = None):
	if full_import:
		if cleanFilePath:
			lokalise_common.lokaliseImport(lokalise_token, lokalise_project_id, cleanFilePath, LOCALIZATION_DEFAULT_LANGUAGE, None)

			destPath = os.path.join(localization_folder, LOCALIZATION_DEFAULT_FOLDER)
			filePath = "{}/{}".format(destPath, LOCALIZATION_FILE_NAME)
			lokalise_common.lokaliseImport(lokalise_token, lokalise_project_id, filePath, LOCALIZATION_DEFAULT_LANGUAGE, [LOCALIZATIOS_UNUSED_TAG])

		for folder in LOCALIZATION_FOLDER_NAMES:
			destPath = os.path.join(localization_folder, folder)

			localization_code = ""
			split_code = folder.split("-")
			if len(split_code) == 1:
				localization_code = LOCALIZATION_DEFAULT_LANGUAGE
			elif len(split_code) == 2:
				localization_code = split_code[1]
			elif len(split_code) == 3:
				localization_code = split_code[1] + "-" + split_code[2]

			if localization_code in LOCALIZATION_IMPORT_MAP:
				localization_code = LOCALIZATION_IMPORT_MAP[localization_code]

			filePath = "{}/{}".format(destPath, LOCALIZATION_FILE_NAME)
			lokalise_common.lokaliseImport(lokalise_token, lokalise_project_id, filePath, localization_code, tags)
	else:
		destPath = os.path.join(localization_folder, LOCALIZATION_DEFAULT_FOLDER)
		filePath = "{}/{}".format(destPath, LOCALIZATION_FILE_NAME)
		lokalise_common.lokaliseImport(lokalise_token, lokalise_project_id, filePath, LOCALIZATION_DEFAULT_LANGUAGE, tags)

def localization_export(localization_folder, lokalise_token, lokalise_project_id):
	print('Removing local localizations...')
	for folder in LOCALIZATION_FOLDER_NAMES:
		destFile = os.path.join(localization_folder, folder, LOCALIZATION_FILE_NAME)
		os.remove(destFile)

	lokalise_common.lokaliseExport(lokalise_token, lokalise_project_id, "xml", localization_folder)

	for key, value in LOCALIZATION_RENAME_MAP.items():
		fromPath = os.path.join(localization_folder, key)
		toPath = os.path.join(localization_folder, value)
		os.rename(fromPath, toPath)
